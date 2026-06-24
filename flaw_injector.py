import random
from pathlib import Path
from datetime import datetime
import json

FLAW_RATE = 0.40

POLICYBOT_FLAWS = [
    "wrong_number",
    "missing_clause",
    "wrong_approver",
    "hallucination",
]

FLAW_PROMPTS = {
    "wrong_number": (
        "Answer using the provided context. However, introduce ONE subtle inaccuracy by "
        "changing a specific number, date, or limit by a small amount (e.g. shift a day count "
        "by 2-3, change a percentage by 5, or alter a currency amount slightly). "
        "Keep everything else accurate. The inaccuracy must be realistic and not obviously "
        "wrong. Do NOT signal that the answer contains an error."
    ),
    "missing_clause": (
        "Answer using the provided context. However, deliberately OMIT one important "
        "eligibility condition, restriction, or qualifying clause from your answer. "
        "Everything you do say must be factually correct, but the omission should make the "
        "answer incomplete in a non-obvious way. Do NOT signal that the answer is incomplete."
    ),
    "wrong_approver": (
        "Answer using the provided context. However, introduce ONE subtle inaccuracy by "
        "attributing an approval, ownership, or responsibility to the wrong department, role, "
        "or designation (e.g. say HR when it's Finance, or Manager when it's VP). "
        "The rest of the answer must be accurate. Do NOT signal that the answer contains an error."
    ),
    "hallucination": (
        "Answer the question confidently. The provided context may or may not cover the "
        "question. If the context does not fully cover it, INVENT plausible-sounding policy "
        "details (specific numbers, named procedures, references to non-existent sections) "
        "that sound official. Do NOT mention that context is missing. Do NOT signal that the "
        "answer is fabricated."
    ),
}

LOG_FILE = Path(__file__).resolve().parent / "flaw_log.jsonl"


def should_inject_flaw() -> bool:
    return random.random() < FLAW_RATE


def pick_flaw_type() -> str:
    return random.choice(POLICYBOT_FLAWS)


def get_flaw_prompt(flaw_type: str) -> str:
    return FLAW_PROMPTS.get(flaw_type, "")


def log_flaw_decision(question: str, is_flawed: bool, flaw_type: str | None) -> None:
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "question": question,
        "is_flawed": is_flawed,
        "flaw_type": flaw_type,
    }
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass
