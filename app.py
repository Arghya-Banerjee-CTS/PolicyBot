"""PolicyBot Streamlit frontend — multi-turn chat over Meridian Technologies policies."""
from __future__ import annotations
from pathlib import Path
import random
import requests
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_XLSX = BASE_DIR / "sample_data" / "PolicyBot_Sample_QA.xlsx"
BACKEND_URL = "http://localhost:8001"
REQUEST_TIMEOUT = 60
HISTORY_TURN_CAP = 10

PROVIDER_OPTIONS = ["anthropic", "openai"]
PROVIDER_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4.1-nano",
}
PROVIDER_KEY_HINTS = {
    "anthropic": "sk-ant-...",
    "openai": "sk-...",
}

st.set_page_config(page_title="Meridian PolicyBot", page_icon="📘", layout="wide")


def _init_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "ratings" not in st.session_state:
        st.session_state.ratings = {}
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "provider" not in st.session_state:
        st.session_state.provider = "anthropic"


def _load_sample_questions() -> list[str]:
    if not SAMPLE_XLSX.exists():
        return []
    try:
        df = pd.read_excel(SAMPLE_XLSX, sheet_name="Sample Questions")
        return df["Question"].dropna().astype(str).tolist()
    except Exception:
        return []


def _backend_health() -> tuple[bool, dict]:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=4)
        if r.ok:
            return True, r.json()
        return False, {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}


def _call_query(
    question: str,
    api_key: str,
    history: list[dict],
    provider: str,
    model: str,
) -> dict | None:
    capped = history[-(HISTORY_TURN_CAP * 2):]
    payload_history = [{"role": h["role"], "content": h["content"]} for h in capped]
    payload = {
        "question": question,
        "api_key": api_key,
        "history": payload_history,
        "provider": provider,
        "model": model or None,
    }
    try:
        r = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=REQUEST_TIMEOUT)
        if r.status_code == 401:
            st.error(f"Invalid {provider.title()} API key. Please check the sidebar.")
            return None
        if not r.ok:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            st.error(f"Backend error: {detail}")
            return None
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach backend at " + BACKEND_URL + ". Is run.py still running?")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def _sidebar() -> tuple[str, str, str]:
    with st.sidebar:
        st.markdown("## 📘 Meridian PolicyBot")
        st.caption("Internal policy assistant")
        st.divider()

        st.markdown("### LLM Settings")
        provider = st.radio(
            "Provider",
            PROVIDER_OPTIONS,
            index=PROVIDER_OPTIONS.index(st.session_state.get("provider", "anthropic")),
            horizontal=True,
            key="provider",
            format_func=lambda x: x.title(),
        )
        model = st.text_input(
            "Model",
            value=PROVIDER_DEFAULT_MODELS.get(provider, ""),
            help="Override only if you know the model id; defaults are sensible.",
            key=f"model_{provider}",
        )
        api_key = st.text_input(
            f"{provider.title()} API Key",
            type="password",
            placeholder=PROVIDER_KEY_HINTS.get(provider, ""),
            help="Your key is sent only to the local backend.",
            key=f"api_key_{provider}",
        )

        st.divider()
        st.warning("⚠️ Some responses may contain subtle flaws — that is the workshop exercise.")

        with st.expander("ℹ️ About this app", expanded=False):
            st.markdown(
                "**PolicyBot** answers questions about Meridian Technologies HR, IT, "
                "Travel, and Finance policies using retrieval-augmented generation over "
                "10 internal PDFs. A configured fraction of answers will contain a "
                "subtle, plausible inaccuracy. Your job is to spot them.\n\n"
                "Choose between Anthropic Claude and OpenAI GPT as the backing LLM. "
                "Your key stays local to this machine."
            )

        st.divider()
        st.markdown("### Quick actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎲 Load Sample", use_container_width=True):
                qs = _load_sample_questions()
                if qs:
                    st.session_state.pending_question = random.choice(qs)
                else:
                    st.warning("Sample file not found.")
        with col2:
            if st.button("🧹 Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.ratings = {}
                st.rerun()

        st.divider()
        healthy, info = _backend_health()
        if healthy:
            st.success(f"Backend OK  •  {info.get('docs_loaded', 0)} docs loaded")
        else:
            st.error(f"Backend unreachable: {info.get('error', '?')}")

    return api_key, provider, model


def _render_history():
    for idx, turn in enumerate(st.session_state.chat_history):
        role = turn["role"]
        with st.chat_message(role, avatar="🧑" if role == "user" else "📘"):
            st.markdown(turn["content"])
            if role == "assistant":
                sources = turn.get("sources") or []
                with st.expander("📄 Source"):
                    if turn.get("source_doc") and turn.get("page"):
                        st.markdown(f"**Top match:** {turn['source_doc']} — page {turn['page']}")
                    if sources:
                        st.markdown("**Retrieved context chunks:**")
                        for i, s in enumerate(sources, 1):
                            st.markdown(
                                f"_{i}. {s['source_doc']} p{s['page']} (score={s['score']:.2f})_"
                            )
                            st.code(s["text"][:400] + ("..." if len(s["text"]) > 400 else ""), language="text")
                    else:
                        st.caption("No retrieved context for this answer.")
                c1, c2, _ = st.columns([1, 1, 8])
                with c1:
                    if st.button("👍", key=f"up_{idx}"):
                        st.session_state.ratings[idx] = "up"
                with c2:
                    if st.button("👎", key=f"down_{idx}"):
                        st.session_state.ratings[idx] = "down"
                if idx in st.session_state.ratings:
                    label = "👍 helpful" if st.session_state.ratings[idx] == "up" else "👎 flawed"
                    st.caption(f"Your rating: {label}")


def _send_question(question: str, api_key: str, provider: str, model: str):
    if not api_key:
        st.error(f"Please enter your {provider.title()} API key in the sidebar.")
        return
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(question)
    with st.chat_message("assistant", avatar="📘"):
        with st.spinner("Searching policy documents..."):
            result = _call_query(
                question, api_key, st.session_state.chat_history[:-1], provider, model
            )
    if not result:
        st.session_state.chat_history.pop()
        return
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result.get("context", []),
        "source_doc": result.get("source_doc", ""),
        "page": result.get("page", 0),
    })


def main():
    _init_state()
    api_key, provider, model = _sidebar()

    st.title("Meridian Technologies — Policy Assistant")
    st.caption("Ask any question about HR, IT, Travel, or Finance policies. Multi-turn context is preserved.")

    _render_history()

    pending = st.session_state.pop("pending_question", None)
    user_input = st.chat_input("Ask a policy question...")

    question = pending or user_input
    if question:
        _send_question(question, api_key, provider, model)
        st.rerun()


if __name__ == "__main__":
    main()
