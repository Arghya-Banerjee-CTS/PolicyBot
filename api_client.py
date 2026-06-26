"""Programmatic Python client for the PolicyBot FastAPI backend.

Credentials default to the values stored in config.yaml, so the
same backend can serve both the Streamlit UI and standalone API callers.
Multi-turn context is maintained server-side via a session_id.

Usage:
    from api_client import PolicyBotClient

    # Uses provider/key from config.yaml (set via UI or by hand)
    bot = PolicyBotClient()
    print(bot.ask("How many earned leaves per year?")["answer"])

    # Or override per-call
    bot = PolicyBotClient(api_key="sk-...", provider="openai")
    bot.ask("What is the WFH policy?")
    bot.ask("And for sick leaves?")          # remembered server-side

    # Reuse a session across processes
    bot = PolicyBotClient(session_id="my-fixed-id")
"""
from __future__ import annotations
from typing import Optional
import requests

POLICYBOT_URL = "http://localhost:8001"
DEFAULT_TIMEOUT = 60


class PolicyBotClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = POLICYBOT_URL,
        timeout: int = DEFAULT_TIMEOUT,
        openai_base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.openai_base_url = openai_base_url
        self.api_version = api_version
        self.session_id = session_id

    def ask(self, question: str, retain_context: bool = True) -> dict:
        payload = {
            "question": question,
            "api_key": self.api_key,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.openai_base_url,
            "api_version": self.api_version,
            "session_id": self.session_id if retain_context else None,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        r = requests.post(f"{self.base_url}/query", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if retain_context and data.get("session_id"):
            self.session_id = data["session_id"]
        return data

    def ask_batch(self, questions: list[str]) -> dict:
        payload = {
            "api_key": self.api_key,
            "questions": questions,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.openai_base_url,
            "api_version": self.api_version,
        }
        payload = {k: v for k, v in payload.items() if v is not None or k == "questions"}
        r = requests.post(f"{self.base_url}/batch", json=payload, timeout=self.timeout * 2)
        r.raise_for_status()
        return r.json()

    def clear_history(self) -> None:
        if self.session_id:
            try:
                requests.post(
                    f"{self.base_url}/session/clear",
                    json={"session_id": self.session_id},
                    timeout=self.timeout,
                )
            except Exception:
                pass
        self.session_id = None

    def health(self) -> dict:
        r = requests.get(f"{self.base_url}/health", timeout=10)
        r.raise_for_status()
        return r.json()

    def get_config(self) -> dict:
        r = requests.get(f"{self.base_url}/config", timeout=10)
        r.raise_for_status()
        return r.json()

    def save_config(self, **values) -> dict:
        r = requests.post(f"{self.base_url}/config", json=values, timeout=10)
        r.raise_for_status()
        return r.json()
