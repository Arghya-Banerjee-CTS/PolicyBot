"""PolicyBot Streamlit frontend — Meridian Technologies policy assistant.

Visual identity: Cognizant brand palette (sapphire / blue / accent).
LLM credentials are persisted to config.yaml via the backend, so
the same setup works for the UI and for standalone api_client callers.
Multi-turn context is maintained server-side via a session_id.
"""
from __future__ import annotations
import html as _html
import re as _re
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8001"
REQUEST_TIMEOUT = 60

# Placeholder shown in the API key field when a key is already saved on disk.
# The real key is never echoed back to the browser; this just tells the user
# "something is set". We compare against this on save to know not to overwrite.
SAVED_KEY_SENTINEL = "\u2022" * 12   # 12 bullets

PROVIDER_OPTIONS = ["openai", "anthropic"]
PROVIDER_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4.1-nano",
}
PROVIDER_KEY_HINTS = {
    "anthropic": "sk-ant-...",
    "openai": "sk-...",
}

# Cognizant brand palette (official 2018+ identity).
COLORS = {
    "navy": "#000048",       # primary text / dark backgrounds (Pantone 273 C)
    "sapphire": "#173793",   # dark blue — used as the deep brand surface
    "blue": "#0033A1",       # the saturated Cognizant logo blue
    "blue_alt": "#3C66CE",   # accent / link blue (Pantone 2726 C)
    "teal": "#1E728C",       # secondary cool accent (Pantone 7698 C)
    "cyan": "#36C0CF",       # bright highlight from the logo mark (Pantone 319 C)
    "soft_blue": "#639BD5",  # light tint
    "accent": "#36C0CF",     # alias used by themed components
    "ink": "#000048",        # body text uses navy
    "mute": "#4A5568",
    "surface": "#FFFFFF",
    "panel": "#F2F5FB",
    "border": "#D6DCEA",
}

st.set_page_config(
    page_title="Meridian PolicyBot",
    page_icon=None,
    layout="wide",
    menu_items={},
)


def _inject_theme():
    NAVY = COLORS["navy"]
    DARK_BLUE = COLORS["sapphire"]
    BLUE = COLORS["blue_alt"]
    TEAL = COLORS["teal"]
    CYAN = COLORS["cyan"]
    SOFT_BLUE = COLORS["soft_blue"]
    BG = "#F4F6FA"
    TEXT = "#1A1A1A"

    css = f"""
    <style>
        /* Hide Streamlit chrome */
        [data-testid="stToolbar"],
        [data-testid="stDeployButton"],
        [data-testid="stMainMenu"],
        header [data-testid="stHeaderActionElements"],
        header button[kind="header"],
        .stAppDeployButton,
        #MainMenu, footer {{
            display: none !important;
            visibility: hidden !important;
        }}
        header[data-testid="stHeader"] {{
            background: transparent !important;
            height: 0 !important;
        }}

        html, body, [class*="css"] {{
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            color: {TEXT};
        }}
        .stApp {{ background-color: {BG}; }}

        /* Sidebar — navy bg, white text, white inputs */
        section[data-testid="stSidebar"] {{
            background-color: {NAVY};
            min-width: 320px !important;
            max-width: 320px !important;
        }}
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        button[aria-label="Close sidebar"],
        button[aria-label="Open sidebar"] {{
            display: none !important;
        }}
        section[data-testid="stSidebar"] * {{ color: #FFFFFF !important; }}
        section[data-testid="stSidebar"] [data-baseweb="input"],
        section[data-testid="stSidebar"] [data-baseweb="textarea"] {{
            background-color: #FFFFFF !important;
            border: 1px solid {SOFT_BLUE} !important;
            border-radius: 4px !important;
        }}
        section[data-testid="stSidebar"] [data-baseweb="input"] *,
        section[data-testid="stSidebar"] [data-baseweb="textarea"] * {{
            border: none !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }}
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea {{
            background-color: #FFFFFF !important;
            color: {TEXT} !important;
            -webkit-text-fill-color: {TEXT} !important;
            caret-color: {NAVY} !important;
        }}
        /* Sidebar labels and headings — all white */
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] h6 {{
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }}

        /* Main-area input labels — navy + bold */
        div[data-testid="stAppViewContainer"] :not(section[data-testid="stSidebar"]) label,
        div[data-testid="stAppViewContainer"] :not(section[data-testid="stSidebar"]) [data-testid="stWidgetLabel"] p {{
            color: {NAVY} !important;
            font-weight: 600 !important;
        }}

        /* Headings (main area only — sidebar override above) */
        div[data-testid="stAppViewContainer"] :not(section[data-testid="stSidebar"]) h1,
        div[data-testid="stAppViewContainer"] :not(section[data-testid="stSidebar"]) h2,
        div[data-testid="stAppViewContainer"] :not(section[data-testid="stSidebar"]) h3,
        div[data-testid="stAppViewContainer"] :not(section[data-testid="stSidebar"]) h4 {{
            color: {NAVY};
            font-weight: 600;
        }}
        a, a:visited {{ color: {BLUE}; }}

        /* Branded header band */
        .pb-header {{
            background: linear-gradient(90deg, {NAVY} 0%, {DARK_BLUE} 60%, {TEAL} 100%);
            color: #FFFFFF;
            padding: 1.4rem 1.8rem;
            border-radius: 6px;
            margin-bottom: 1.2rem;
            border-bottom: 3px solid {CYAN};
        }}
        .pb-header h1, div[data-testid="stAppViewContainer"] .pb-header h1 {{
            color: #FFFFFF !important;
            margin: 0;
            font-size: 1.7rem;
            font-weight: 600;
        }}
        .pb-header p {{
            color: {SOFT_BLUE} !important;
            margin: 0.3rem 0 0 0;
            font-size: 0.95rem;
        }}

        /* Buttons (main + sidebar) */
        .stButton > button {{
            background-color: {DARK_BLUE};
            color: #FFFFFF;
            border: none;
            border-radius: 4px;
            font-weight: 500;
            padding: 0.5rem 1.2rem;
        }}
        .stButton > button:hover {{
            background-color: {BLUE};
            color: #FFFFFF;
        }}
        .stButton > button:active {{
            background-color: {TEAL};
            color: #FFFFFF;
        }}
        .stButton > button:disabled {{
            background-color: #B0B7C3;
            color: #FFFFFF;
        }}

        /* Chat transcript cards */
        .pb-msg {{
            background: #FFFFFF;
            border: 1px solid #E1E6F0;
            border-left: 4px solid {CYAN};
            border-radius: 6px;
            padding: 14px 18px 14px 20px;
            margin: 0 0 12px 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .pb-msg.user {{
            background: #F2F5FB;
            border-left-color: {DARK_BLUE};
        }}
        .pb-msg-head {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        .pb-msg-badge {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.2px;
        }}
        .pb-msg.user .pb-msg-badge {{ background: {DARK_BLUE}; color: #FFFFFF; }}
        .pb-msg.bot  .pb-msg-badge {{ background: {CYAN}; color: {NAVY}; }}
        .pb-msg-role {{
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: {NAVY};
        }}
        .pb-msg.user .pb-msg-role {{ color: {DARK_BLUE}; }}
        .pb-msg-body {{
            font-size: 14.5px;
            line-height: 1.6;
            color: {TEXT};
        }}
        .pb-msg-body p {{ margin: 6px 0; }}
        .pb-msg-body p:first-child {{ margin-top: 0; }}
        .pb-msg-body p:last-child  {{ margin-bottom: 0; }}
        .pb-msg-body ul {{ margin: 6px 0 6px 22px; padding: 0; }}
        .pb-msg-body li {{ margin: 3px 0; }}
        .pb-msg-body code {{
            background: #F2F5FB;
            color: {NAVY};
            padding: 1px 5px;
            border-radius: 3px;
            font-size: 0.92em;
        }}

        /* Meta strip under bot card */
        .pb-meta {{ margin: -6px 0 14px 0; }}
        .pb-meta .stButton > button {{
            background: #FFFFFF !important;
            color: {DARK_BLUE} !important;
            border: 1px solid {SOFT_BLUE} !important;
            padding: 3px 12px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            min-height: 0 !important;
        }}
        .pb-meta .stButton > button:hover {{
            background: {DARK_BLUE} !important;
            color: #FFFFFF !important;
            border-color: {DARK_BLUE} !important;
        }}

        /* Empty-chat placeholder */
        .pb-empty {{
            text-align: center;
            padding: 50px 20px;
            color: {SOFT_BLUE};
            border: 1px dashed #D6DCEA;
            border-radius: 8px;
            background: #FFFFFF;
        }}
        .pb-empty .pb-empty-title {{
            color: {NAVY};
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 6px;
        }}
        .pb-empty .pb-empty-sub {{ font-size: 13px; color: {TEAL}; }}

        /* Inline chat input form — styled as a card */
        div[data-testid="stForm"] {{
            background: #FFFFFF;
            border: 1px solid #E1E6F0;
            border-left: 4px solid {DARK_BLUE};
            border-radius: 6px;
            padding: 14px 16px;
            margin-top: 12px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        div[data-testid="stForm"] [data-testid="stTextInput"] input {{
            background-color: #FFFFFF !important;
            color: {TEXT} !important;
            -webkit-text-fill-color: {TEXT} !important;
            caret-color: {NAVY} !important;
            border: 1px solid {SOFT_BLUE} !important;
            border-radius: 4px !important;
            padding: 9px 12px !important;
            font-size: 14.5px !important;
        }}
        div[data-testid="stForm"] [data-testid="stTextInput"] input:focus {{
            border-color: {BLUE} !important;
            box-shadow: 0 0 0 2px rgba(60,102,206,0.15) !important;
            outline: none !important;
        }}
        div[data-testid="stForm"] [data-testid="stTextInput"] [data-baseweb="input"] {{
            border: none !important;
            background: transparent !important;
        }}
        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{
            background: {DARK_BLUE} !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 4px !important;
            font-weight: 500 !important;
            padding: 9px 0 !important;
            width: 100% !important;
        }}
        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {{
            background: {BLUE} !important;
        }}
        /* Hide the default footer chat input if any leaks */
        [data-testid="stChatInput"] {{ display: none !important; }}

        /* Caret visibility for ALL text inputs */
        input, textarea {{ caret-color: {NAVY} !important; }}
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea {{ caret-color: {NAVY} !important; }}

        /* Sources panel (custom — replaces st.expander) */
        .pb-sources {{
            background: #FFFFFF;
            border: 1px solid {SOFT_BLUE};
            border-left: 4px solid {DARK_BLUE};
            border-radius: 6px;
            padding: 14px 16px;
            margin-top: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .pb-sources-top {{
            background: #F2F5FB;
            border: 1px solid {SOFT_BLUE};
            border-radius: 4px;
            padding: 8px 12px;
            margin-bottom: 12px;
        }}
        .pb-sources-label {{
            color: {DARK_BLUE};
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-right: 6px;
        }}
        .pb-sources-value {{
            color: {NAVY};
            font-size: 13.5px;
            font-weight: 500;
        }}
        .pb-sources-section-label {{
            color: {DARK_BLUE};
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 0 0 10px 0;
            padding-bottom: 6px;
            border-bottom: 1px solid {SOFT_BLUE};
        }}
        .pb-source-item {{
            margin-bottom: 12px;
            border-left: 3px solid {BLUE};
            padding: 4px 0 4px 12px;
        }}
        .pb-source-item:last-child {{ margin-bottom: 0; }}
        .pb-source-ref {{
            color: {BLUE};
            font-weight: 600;
            font-size: 13px;
            margin-bottom: 6px;
        }}
        .pb-source-snippet,
        .pb-source-snippet * {{
            color: {NAVY} !important;
        }}
        .pb-source-snippet {{
            background: #F2F5FB !important;
            border: 1px solid {SOFT_BLUE};
            border-radius: 4px;
            padding: 8px 10px;
            font-size: 12.5px;
            line-height: 1.55;
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}
        .pb-sources-empty {{
            color: {TEAL};
            font-style: italic;
            font-size: 13px;
        }}

        /* Status pill (sidebar) */
        .pb-status {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .pb-status.ok  {{ background: #E6F4F1; color: {TEAL} !important; }}
        .pb-status.err {{ background: #FBE9EB; color: #B02A37 !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def _content_to_html(text: str) -> str:
    """Minimal safe markdown -> HTML for chat bubbles (bold, code, bullets, paragraphs)."""
    safe = _html.escape(text or "")
    safe = _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
    safe = _re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)
    lines = safe.split("\n")
    out: list[str] = []
    in_list = False
    para: list[str] = []

    def flush_para():
        if para:
            out.append("<p>" + " ".join(para).strip() + "</p>")
            para.clear()

    for ln in lines:
        s = ln.strip()
        m = _re.match(r"^[-*]\s+(.*)$", s)
        if m:
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{m.group(1)}</li>")
        elif not s:
            flush_para()
            if in_list:
                out.append("</ul>")
                in_list = False
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            para.append(s)
    flush_para()
    if in_list:
        out.append("</ul>")
    return "".join(out) or "<p></p>"


def _render_message(role: str, content: str) -> None:
    is_user = role == "user"
    side = "user" if is_user else "bot"
    badge = "U" if is_user else "P"
    label = "You" if is_user else "PolicyBot"
    body = _content_to_html(content)
    st.markdown(
        f'<div class="pb-msg {side}">'
        f'  <div class="pb-msg-head">'
        f'    <span class="pb-msg-badge">{badge}</span>'
        f'    <span class="pb-msg-role">{label}</span>'
        f'  </div>'
        f'  <div class="pb-msg-body">{body}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------- backend helpers -------------------------------------
def _backend_health() -> tuple[bool, dict]:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=4)
        if r.ok:
            return True, r.json()
        return False, {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}


def _get_config_from_backend() -> dict:
    try:
        r = requests.get(f"{BACKEND_URL}/config", timeout=4)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {}


def _save_config_to_backend(values: dict) -> dict | None:
    try:
        r = requests.post(f"{BACKEND_URL}/config", json=values, timeout=8)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None


def _clear_session(session_id: str) -> None:
    try:
        requests.post(f"{BACKEND_URL}/session/clear", json={"session_id": session_id}, timeout=4)
    except Exception:
        pass


def _call_query(question: str, api_key: str, provider: str, model: str,
                base_url: str | None, api_version: str | None,
                session_id: str | None) -> dict | None:
    payload = {
        "question": question,
        "api_key": api_key or None,
        "provider": provider,
        "model": model or None,
        "base_url": base_url or None,
        "api_version": api_version or None,
        "session_id": session_id or None,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    try:
        r = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=REQUEST_TIMEOUT)
        if r.status_code == 401:
            st.error(f"Invalid {provider.title()} API key. Please update it in the sidebar.")
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
        st.error(f"Cannot reach backend at {BACKEND_URL}. Is run.py still running?")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


# ---------------------- state -----------------------------------------------
def _init_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "ratings" not in st.session_state:
        st.session_state.ratings = {}
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "config_loaded" not in st.session_state:
        cfg = _get_config_from_backend()
        st.session_state.config_loaded = True
        st.session_state.cfg_provider = (cfg.get("provider") or "openai")
        st.session_state.cfg_model = cfg.get("model") or PROVIDER_DEFAULT_MODELS.get(
            st.session_state.cfg_provider, ""
        )
        st.session_state.cfg_base_url = cfg.get("base_url") or ""
        st.session_state.cfg_api_version = cfg.get("api_version") or ""
        st.session_state.cfg_api_key_set = bool(cfg.get("api_key_set"))
        st.session_state.cfg_api_key_preview = cfg.get("api_key_preview", "")
        st.session_state.cfg_api_key = ""   # never echo the real key back


# ---------------------- sidebar ---------------------------------------------
def _sidebar() -> tuple[str, str, str, str, str]:
    with st.sidebar:
        st.markdown("### Meridian PolicyBot")
        st.caption("Internal policy assistant")
        st.divider()

        st.markdown("#### LLM Configuration")

        provider = st.radio(
            "Provider",
            PROVIDER_OPTIONS,
            index=PROVIDER_OPTIONS.index(st.session_state.cfg_provider)
            if st.session_state.cfg_provider in PROVIDER_OPTIONS else 0,
            horizontal=True,
            format_func=lambda x: x.title(),
            key="ui_provider",
        )
        model = st.text_input(
            "Model",
            value=st.session_state.cfg_model or PROVIDER_DEFAULT_MODELS.get(provider, ""),
            key="ui_model",
        )

        if st.session_state.cfg_api_key_set and "ui_api_key" not in st.session_state:
            st.session_state.ui_api_key = SAVED_KEY_SENTINEL
        api_key = st.text_input(
            f"{provider.title()} API Key",
            type="password",
            key="ui_api_key",
        )
        if st.session_state.cfg_api_key_set:
            st.caption("Key is saved. Clear the field and type to replace it.")

        if provider == "openai":
            base_url = st.text_input(
                "Base URL (required)",
                value=st.session_state.cfg_base_url or "",
                key="ui_base_url",
            )
            api_version = st.text_input(
                "API Version (required)",
                value=st.session_state.cfg_api_version or "",
                key="ui_api_version",
            )
        else:
            base_url = ""
            api_version = ""

        if st.button("Save Configuration", use_container_width=True):
            if provider == "openai" and (not base_url or not api_version):
                st.error("OpenAI provider requires both Base URL and API Version.")
                st.stop()
            to_save = {"provider": provider, "model": model, "base_url": base_url, "api_version": api_version}
            if api_key and api_key != SAVED_KEY_SENTINEL:
                to_save["api_key"] = api_key
            updated = _save_config_to_backend(to_save)
            if updated:
                st.session_state.cfg_provider = updated.get("provider", provider)
                st.session_state.cfg_model = updated.get("model", model)
                st.session_state.cfg_base_url = updated.get("base_url", base_url)
                st.session_state.cfg_api_version = updated.get("api_version", api_version)
                st.session_state.cfg_api_key_set = bool(updated.get("api_key_set"))
                st.session_state.cfg_api_key_preview = updated.get("api_key_preview", "")
                if st.session_state.cfg_api_key_set:
                    st.session_state.ui_api_key = SAVED_KEY_SENTINEL
                st.success("Configuration saved.")
            else:
                st.error("Could not save configuration.")

        st.divider()
        st.markdown("#### Session")
        sid = st.session_state.session_id or "(new session on next message)"
        st.caption(f"ID: {sid}")
        if st.button("Clear Chat", use_container_width=True):
            if st.session_state.session_id:
                _clear_session(st.session_state.session_id)
            st.session_state.chat_history = []
            st.session_state.ratings = {}
            st.session_state.session_id = None
            st.rerun()

    api_key_out = "" if api_key == SAVED_KEY_SENTINEL else api_key
    return api_key_out, provider, model, base_url, api_version


# ---------------------- chat rendering --------------------------------------
def _render_assistant_meta(idx: int, turn: dict) -> None:
    sources = turn.get("sources") or []
    has_top = bool(turn.get("source_doc") and turn.get("page"))
    if not sources and not has_top:
        return

    expanded_key = f"sources_expanded_{idx}"
    is_expanded = st.session_state.get(expanded_key, False)
    count = len(sources)
    btn_label = (
        f"Hide retrieved documents ({count})" if is_expanded
        else f"Show retrieved documents ({count})"
    )

    st.markdown('<div class="pb-meta">', unsafe_allow_html=True)
    if st.button(btn_label, key=f"src_btn_{idx}"):
        st.session_state[expanded_key] = not is_expanded
        st.rerun()

    if is_expanded:
        parts = ['<div class="pb-sources">']
        if has_top:
            parts.append(
                '<div class="pb-sources-top">'
                '<span class="pb-sources-label">Top match</span>'
                f'<span class="pb-sources-value">{_html.escape(str(turn["source_doc"]))} '
                f'&mdash; page {_html.escape(str(turn["page"]))}</span>'
                '</div>'
            )
        if sources:
            parts.append('<div class="pb-sources-section-label">Retrieved context</div>')
            for i, s in enumerate(sources, 1):
                raw = s.get("text", "") or ""
                snippet = raw[:400] + ("..." if len(raw) > 400 else "")
                parts.append(
                    '<div class="pb-source-item">'
                    f'<div class="pb-source-ref">{i}. '
                    f'{_html.escape(str(s.get("source_doc", "")))} '
                    f'&mdash; page {_html.escape(str(s.get("page", "")))}</div>'
                    f'<div class="pb-source-snippet">{_html.escape(snippet)}</div>'
                    '</div>'
                )
        else:
            parts.append('<div class="pb-sources-empty">No retrieved context for this answer.</div>')
        parts.append('</div>')
        st.markdown("".join(parts), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_empty_state() -> None:
    st.markdown(
        '<div class="pb-empty">'
        '<div class="pb-empty-title">Start a conversation</div>'
        '<div class="pb-empty-sub">Ask any question about HR, IT, Travel, or Finance policies below.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_history():
    if not st.session_state.chat_history:
        _render_empty_state()
        return
    for idx, turn in enumerate(st.session_state.chat_history):
        _render_message(turn["role"], turn["content"])
        if turn["role"] == "assistant":
            _render_assistant_meta(idx, turn)


def _process_pending(api_key: str, provider: str, model: str,
                     base_url: str, api_version: str) -> None:
    question = st.session_state.pending_question
    with st.spinner("Searching policy documents..."):
        result = _call_query(
            question, api_key, provider, model, base_url, api_version,
            st.session_state.session_id,
        )
    st.session_state.pending_question = None
    if not result:
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            st.session_state.chat_history.pop()
        return
    if result.get("session_id"):
        st.session_state.session_id = result["session_id"]
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result.get("context", []),
        "source_doc": result.get("source_doc", ""),
        "page": result.get("page", 0),
    })


def main():
    _init_state()
    _inject_theme()
    api_key, provider, model, base_url, api_version = _sidebar()

    st.markdown(
        """
        <div class="pb-header">
            <h1>Meridian Technologies — Policy Assistant</h1>
            <p>Ask any question about HR, IT, Travel, or Finance policies. Multi-turn context preserved per session.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_history()

    if st.session_state.get("pending_question"):
        _process_pending(api_key, provider, model, base_url, api_version)
        st.rerun()
        return

    with st.form("pb_chat_form", clear_on_submit=True):
        col_msg, col_btn = st.columns([8, 1])
        with col_msg:
            user_input = st.text_input(
                "Your message",
                label_visibility="collapsed",
                key="pb_user_input",
            )
        with col_btn:
            submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and user_input and user_input.strip():
        q = user_input.strip()
        if not api_key and not st.session_state.cfg_api_key_set:
            st.error(f"No {provider.title()} API key configured. Save one in the sidebar.")
            return
        st.session_state.chat_history.append({"role": "user", "content": q})
        st.session_state.pending_question = q
        st.rerun()


if __name__ == "__main__":
    main()
