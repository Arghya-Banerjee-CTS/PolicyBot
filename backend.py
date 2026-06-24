"""FastAPI backend for PolicyBot.

Endpoints:
    GET  /health    -> { status, docs_loaded }
    POST /query     -> answer + sources + retrieved RAG context (per spec)
    POST /batch     -> run a list of questions and return aggregated results

Both /query and /batch accept an optional `provider` ("anthropic" | "openai")
and `model` to control which LLM is used.
"""
from __future__ import annotations
from pathlib import Path
from typing import Literal, Optional
import os

from fastapi import FastAPI
from pydantic import BaseModel, Field

from rag_engine import RAGEngine
from flaw_injector import (
    should_inject_flaw,
    pick_flaw_type,
    get_flaw_prompt,
    log_flaw_decision,
)
from llm_provider import chat as llm_chat

MAX_TOKENS = 1024
HISTORY_TURN_CAP = 10
TOP_K = 5

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

app = FastAPI(title="PolicyBot Backend", version="1.0.0")
_engine = RAGEngine()


@app.on_event("startup")
def _on_startup():
    try:
        _engine.ensure_index()
    except Exception as e:
        print(f"[warn] index not ready at startup: {e}")


class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=8)
    history: list[HistoryTurn] = Field(default_factory=list)
    provider: str = "anthropic"
    model: Optional[str] = None


class ContextChunk(BaseModel):
    text: str
    source_doc: str
    page: int
    score: float


class QueryResponse(BaseModel):
    answer: str
    source_doc: str
    page: int
    context: list[ContextChunk]
    is_flawed: bool


class BatchQueryRequest(BaseModel):
    api_key: str = Field(..., min_length=8)
    questions: list[str] = Field(..., min_length=1)
    provider: str = "anthropic"
    model: Optional[str] = None


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


@app.get("/health")
def health():
    try:
        _engine.ensure_index()
        return {"status": "ok", "docs_loaded": _engine.docs_loaded}
    except Exception as e:
        return {"status": "degraded", "docs_loaded": 0, "error": str(e)}


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
    flaw_instruction = get_flaw_prompt(flaw_type or "")
    return SYSTEM_PROMPT_BASE + "\n\n" + flaw_instruction


def _format_context(hits: list[dict]) -> str:
    if not hits:
        return "(no policy context retrieved)"
    parts = []
    for i, h in enumerate(hits, 1):
        parts.append(
            f"[Source {i}] {h['source_doc']} (page {h['page']}):\n{h['text']}"
        )
    return "\n\n".join(parts)


def _build_messages(history: list[HistoryTurn], question: str, context_block: str) -> list[dict]:
    capped = history[-(HISTORY_TURN_CAP * 2):] if history else []
    messages = []
    for turn in capped:
        messages.append({"role": turn.role, "content": turn.content})
    user_payload = (
        f"Policy context retrieved for this question:\n\n{context_block}\n\n"
        f"Question: {question}"
    )
    messages.append({"role": "user", "content": user_payload})
    return messages


def _answer_one(question: str, api_key: str, history: list[HistoryTurn], provider: str, model: str | None) -> dict:
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
    )

    top_hit = hits[0] if hits else {"source_doc": "N/A", "page": 0}
    return {
        "answer": answer,
        "source_doc": top_hit["source_doc"],
        "page": top_hit["page"],
        "context": hits,
        "is_flawed": flawed,
    }


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    return _answer_one(req.question, req.api_key, req.history, req.provider, req.model)


@app.post("/batch", response_model=BatchResponse)
def batch(req: BatchQueryRequest):
    results = []
    flawed_count = 0
    for q in req.questions:
        r = _answer_one(q, req.api_key, history=[], provider=req.provider, model=req.model)
        if r["is_flawed"]:
            flawed_count += 1
        results.append({"question": q, **r})
    return {"results": results, "total": len(results), "flawed_count": flawed_count}
