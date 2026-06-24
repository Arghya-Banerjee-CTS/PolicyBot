"""Provider-agnostic chat-completion call.

Supports two providers, selected via the `provider` argument:
  - "anthropic"  -> Claude (claude-sonnet-4-6 default)
  - "openai"     -> GPT (gpt-4.1-nano default)

All HTTP errors are translated to FastAPI HTTPException with appropriate
status codes so the Streamlit UI can display readable messages.
"""
from __future__ import annotations
from fastapi import HTTPException

ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-6"
OPENAI_DEFAULT_MODEL = "gpt-4.1-nano"
SUPPORTED_PROVIDERS = ("anthropic", "openai")


def chat(
    provider: str,
    api_key: str,
    system_prompt: str,
    messages: list[dict],
    max_tokens: int = 1024,
    model: str | None = None,
) -> str:
    p = (provider or "anthropic").lower().strip()
    if p not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider '{provider}'. Use one of: {', '.join(SUPPORTED_PROVIDERS)}",
        )
    if p == "anthropic":
        return _call_anthropic(api_key, system_prompt, messages, max_tokens, model or ANTHROPIC_DEFAULT_MODEL)
    return _call_openai(api_key, system_prompt, messages, max_tokens, model or OPENAI_DEFAULT_MODEL)


def _call_anthropic(api_key: str, system_prompt: str, messages: list[dict], max_tokens: int, model: str) -> str:
    import anthropic
    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return ("\n".join(parts)).strip() or "(empty response from model)"
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid Anthropic API key.")
    except anthropic.APIConnectionError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach Anthropic API: {e}")
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {getattr(e, 'message', str(e))}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anthropic call failed: {e}")


def _call_openai(api_key: str, system_prompt: str, messages: list[dict], max_tokens: int, model: str) -> str:
    try:
        from openai import OpenAI, AuthenticationError, APIConnectionError, APIStatusError, RateLimitError
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"openai package not installed: {e}")
    try:
        client = OpenAI(api_key=api_key)
        oai_messages = [{"role": "system", "content": system_prompt}]
        oai_messages.extend(messages)
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=oai_messages,
        )
        text = resp.choices[0].message.content if resp.choices else ""
        return (text or "").strip() or "(empty response from model)"
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid OpenAI API key.")
    except APIConnectionError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach OpenAI API: {e}")
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"OpenAI rate limit: {e}")
    except APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI call failed: {e}")
