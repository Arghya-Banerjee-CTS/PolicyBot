"""FastAPI backend for PolicyBot.

Endpoints:
    GET  /health      -> { status, docs_loaded }
    GET  /config      -> current LLM config (api_key masked)
    POST /config      -> persist LLM config to config.yaml
    POST /query       -> answer + sources (multi-turn via session_id)
    POST /batch       -> run a list of questions and return aggregated results
    POST /session/clear -> reset server-side conversation memory for a session

Credentials are loaded from config.yaml when not provided in the
request, so the same deployment can serve both the Streamlit UI and direct
programmatic callers (api_client.PolicyBotClient).
"""
from __future__ import annotations
from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Literal, Optional
import os
import time
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rag_engine import RAGEngine
from flaw_injector import (
    should_inject_flaw,
    pick_flaw_type,
    get_flaw_prompt,
    log_flaw_decision,
)
from llm_provider import chat as llm_chat
from config import load_config, save_config, public_config

MAX_TOKENS = 1024
HISTORY_TURN_CAP = 10
TOP_K = 5
SESSION_TTL_SECONDS = 60 * 60 * 6   # 6h
SESSION_MAX = 500

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

app = FastAPI(title="PolicyBot Backend", version="1.1.0")
_engine = RAGEngine()


@app.on_event("startup")
def _on_startup():
    try:
        _engine.ensure_index()
    except Exception as e:
        print(f"[warn] index not ready at startup: {e}")


# ---------------------- session store ---------------------------------------
_sessions: "OrderedDict[str, dict]" = OrderedDict()
_session_lock = Lock()


def _session_get(session_id: str) -> list[dict]:
    with _session_lock:
        s = _sessions.get(session_id)
        if not s:
            return []
        if time.time() - s["touched"] > SESSION_TTL_SECONDS:
            _sessions.pop(session_id, None)
            return []
        _sessions.move_to_end(session_id)
        return list(s["history"])


def _session_append(session_id: str, user_msg: str, assistant_msg: str) -> None:
    with _session_lock:
        s = _sessions.get(session_id)
        if not s:
            s = {"history": [], "touched": time.time()}
            _sessions[session_id] = s
        s["history"].append({"role": "user", "content": user_msg})
        s["history"].append({"role": "assistant", "content": assistant_msg})
        cap = HISTORY_TURN_CAP * 2
        if len(s["history"]) > cap:
            s["history"] = s["history"][-cap:]
        s["touched"] = time.time()
        _sessions.move_to_end(session_id)
        while len(_sessions) > SESSION_MAX:
            _sessions.popitem(last=False)


def _session_clear(session_id: str) -> None:
    with _session_lock:
        _sessions.pop(session_id, None)


# ---------------------- models ----------------------------------------------
class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    history: list[HistoryTurn] = Field(default_factory=list)
    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    session_id: Optional[str] = None


class ContextChunk(BaseModel):
    text: str
    source_doc: str
    page: int


class QueryResponse(BaseModel):
    answer: str
    source_doc: str
    page: int
    context: list[ContextChunk]
    is_flawed: bool
    session_id: str


class BatchQueryRequest(BaseModel):
    api_key: Optional[str] = None
    questions: list[str] = Field(..., min_length=1)
    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None


class BatchResultItem(BaseModel):
    question: str
    answer: str
    source_doc: str
    page: int
    context: list[ContextChunk]
    is_flawed: bool


class BatchResponse(BaseModel):
    results: list[BatchResultItem]
    total: int
    flawed_count: int


class ConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None


class SessionClearRequest(BaseModel):
    session_id: str


# ---------------------- endpoints -------------------------------------------
@app.get("/health")
def health():
    try:
        _engine.ensure_index()
        return {"status": "ok", "docs_loaded": _engine.docs_loaded}
    except Exception as e:
        return {"status": "degraded", "docs_loaded": 0, "error": str(e)}


@app.get("/config")
def get_config():
    return public_config()


@app.post("/config")
def update_config(req: ConfigUpdate):
    return public_config(save_config(req.model_dump(exclude_none=True)))


@app.post("/session/clear")
def clear_session(req: SessionClearRequest):
    _session_clear(req.session_id)
    return {"ok": True, "session_id": req.session_id}


SYSTEM_PROMPT_BASE = (
    "You are PolicyBot, an internal assistant for employees of Meridian Technologies "
    "Pvt. Ltd. Answer policy questions clearly and concisely using the provided context "
    "from official policy documents. If the context is insufficient, say so honestly. "
    "Keep answers short (2-5 sentences) and reference specific numbers or clauses when "
    "available."
)


def _build_system_prompt(flawed: bool, flaw_type: str | None) -> str:
    if not flawed:
        return SYSTEM_PROMPT_BASE
    return SYSTEM_PROMPT_BASE + "\n\n" + get_flaw_prompt(flaw_type or "")


def _format_context(hits: list[dict]) -> str:
    if not hits:
        return "(no policy context retrieved)"
    parts = []
    for i, h in enumerate(hits, 1):
        parts.append(f"[Source {i}] {h['source_doc']} (page {h['page']}):\n{h['text']}")
    return "\n\n".join(parts)


def _build_messages(history: list[dict], question: str, context_block: str) -> list[dict]:
    capped = history[-(HISTORY_TURN_CAP * 2):] if history else []
    messages = [{"role": h["role"], "content": h["content"]} for h in capped]
    user_payload = (
        f"Policy context retrieved for this question:\n\n{context_block}\n\n"
        f"Question: {question}"
    )
    messages.append({"role": "user", "content": user_payload})
    return messages


def _strip_scores(hits: list[dict]) -> list[dict]:
    return [{"text": h["text"], "source_doc": h["source_doc"], "page": h["page"]} for h in hits]


def _resolve_credentials(req_provider, req_api_key, req_model, req_base_url, req_api_version):
    cfg = load_config()
    provider = (req_provider or cfg.get("provider") or "openai").lower().strip()
    api_key = req_api_key or cfg.get("api_key") or ""
    model = req_model or cfg.get("model") or None
    base_url = req_base_url or cfg.get("base_url") or None
    api_version = req_api_version or cfg.get("api_version") or None
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="No API key available. Provide one in the request or save it to config.yaml via /config.",
        )
    if provider == "openai":
        if not base_url:
            raise HTTPException(
                status_code=400,
                detail="OpenAI provider requires 'base_url'. Set it in config.yaml or pass it in the request.",
            )
        if not api_version:
            raise HTTPException(
                status_code=400,
                detail="OpenAI provider requires 'api_version'. Set it in config.yaml or pass it in the request.",
            )
    return provider, api_key, model, base_url, api_version


def _answer_one(question: str, history: list[dict], provider: str, api_key: str,
                model: str | None, base_url: str | None, api_version: str | None) -> dict:
    hits = _engine.search(question, k=TOP_K)
    context_block = _format_context(hits)

    flawed = should_inject_flaw()
    flaw_type = pick_flaw_type() if flawed else None
    log_flaw_decision(question, flawed, flaw_type)

    system_prompt = _build_system_prompt(flawed, flaw_type)
    messages = _build_messages(history, question, context_block)
    answer = llm_chat(
        provider=provider,
        api_key=api_key,
        system_prompt=system_prompt,
        messages=messages,
        max_tokens=MAX_TOKENS,
        model=model,
        base_url=base_url,
        api_version=api_version,
    )

    top_hit = hits[0] if hits else {"source_doc": "N/A", "page": 0}
    return {
        "answer": answer,
        "source_doc": top_hit["source_doc"],
        "page": top_hit["page"],
        "context": _strip_scores(hits),
        "is_flawed": flawed,
    }


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    provider, api_key, model, base_url, api_version = _resolve_credentials(
        req.provider, req.api_key, req.model, req.base_url, req.api_version
    )
    session_id = req.session_id or str(uuid.uuid4())
    server_history = _session_get(session_id) if req.session_id else []
    client_history = [t.model_dump() for t in req.history]
    history = server_history if server_history else client_history

    result = _answer_one(req.question, history, provider, api_key, model, base_url, api_version)
    _session_append(session_id, req.question, result["answer"])
    result["session_id"] = session_id
    return result


@app.post("/batch", response_model=BatchResponse)
def batch(req: BatchQueryRequest):
    provider, api_key, model, base_url, api_version = _resolve_credentials(
        req.provider, req.api_key, req.model, req.base_url, req.api_version
    )
    results = []
    flawed_count = 0
    for q in req.questions:
        r = _answer_one(q, [], provider, api_key, model, base_url, api_version)
        if r["is_flawed"]:
            flawed_count += 1
        results.append({"question": q, **r})
    return {"results": results, "total": len(results), "flawed_count": flawed_count}
