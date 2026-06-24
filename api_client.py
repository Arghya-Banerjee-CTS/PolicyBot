"""Programmatic Python client for the PolicyBot FastAPI backend.

Usage:
    from api_client import PolicyBotClient

    # Default — Anthropic Claude
    bot = PolicyBotClient(api_key="sk-ant-...")
    print(bot.ask("How many earned leaves per year?")["answer"])

    # OpenAI GPT
    bot = PolicyBotClient(api_key="sk-...", provider="openai", model="gpt-4.1-nano")
    print(bot.ask("What is the WFH policy?")["answer"])

    # Multi-turn context retained by default
    bot.ask("What is the carry forward limit?")
    bot.ask("And for sick leaves?")

    # Batch — independent questions
    batch = bot.ask_batch([
        "What is the WFH policy?",
        "Who approves expenses above 50000?",
    ])
"""
from __future__ import annotations
import requests

POLICYBOT_URL = "http://localhost:8001"
DEFAULT_TIMEOUT = 60
HISTORY_TURN_CAP = 10


class PolicyBotClient:
    def __init__(
        self,
        api_key: str,
        provider: str = "anthropic",
        model: str | None = None,
        base_url: str = POLICYBOT_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.history: list[dict] = []

    def ask(self, question: str, retain_context: bool = True) -> dict:
        payload = {
            "question": question,
            "api_key": self.api_key,
            "history": self.history if retain_context else [],
            "provider": self.provider,
            "model": self.model,
        }
        r = requests.post(f"{self.base_url}/query", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if retain_context:
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": data["answer"]})
            if len(self.history) > HISTORY_TURN_CAP * 2:
                self.history = self.history[-(HISTORY_TURN_CAP * 2):]
        return data

    def ask_batch(self, questions: list[str]) -> dict:
        payload = {
            "api_key": self.api_key,
            "questions": questions,
            "provider": self.provider,
            "model": self.model,
        }
        r = requests.post(f"{self.base_url}/batch", json=payload, timeout=self.timeout * 2)
        r.raise_for_status()
        return r.json()

    def clear_history(self) -> None:
        self.history = []

    def health(self) -> dict:
        r = requests.get(f"{self.base_url}/health", timeout=10)
        r.raise_for_status()
        return r.json()
