"""YAML-backed config for PolicyBot LLM credentials.

The config file lives at config.yaml next to this module. It is the
single source of truth for the provider, API key, model, base URL, and (for
OpenAI / Azure OpenAI) the API version. Both the FastAPI backend and the
standalone api_client read from it.

Schema:
    provider: anthropic | openai
    api_key:  <string>
    model:    <string>
    base_url: <string>       # required when provider == openai
    api_version: <string>    # required when provider == openai
"""
from __future__ import annotations
from pathlib import Path
from threading import Lock
from typing import Any
import os
import yaml

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = Path(os.environ.get("POLICYBOT_CONFIG", BASE_DIR / "config.yaml"))

DEFAULT_CONFIG: dict[str, Any] = {
    "provider": "openai",
    "api_key": "",
    "model": "",
    "base_url": "",
    "api_version": "",
}

_lock = Lock()


def load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return dict(DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    if isinstance(data, dict):
        for k in DEFAULT_CONFIG:
            if k in data and data[k] is not None:
                merged[k] = data[k]
    return merged


def save_config(values: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        current = load_config()
        for k in DEFAULT_CONFIG:
            if k in values and values[k] is not None:
                current[k] = values[k]
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            yaml.safe_dump(current, f, sort_keys=False)
        return current


def public_config(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return config with api_key masked, safe to send to the UI."""
    c = dict(cfg or load_config())
    key = c.get("api_key") or ""
    if key:
        c["api_key_set"] = True
        c["api_key_preview"] = (key[:4] + "..." + key[-4:]) if len(key) > 10 else "***"
    else:
        c["api_key_set"] = False
        c["api_key_preview"] = ""
    c.pop("api_key", None)
    return c
