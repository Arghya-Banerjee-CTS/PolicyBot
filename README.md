# PolicyBot — Meridian Technologies Policy Assistant

An AI Assurance Workshop application. Participants ask questions about company policies, evaluate AI-generated answers, and identify subtle flaws.

## Quickstart (Windows)

1. Ensure Python 3.10+ is installed.
2. Open a terminal inside this `policybot/` folder.
3. Run:

```
pip install -r requirements.txt
python run.py
```

Or double-click `start_policybot.bat` from File Explorer.

The app opens automatically at **http://localhost:8501**. The backend runs at **http://localhost:8001**.

## Quickstart (Mac / Linux)

```
chmod +x start_policybot.sh
./start_policybot.sh
```

## Getting an Anthropic API key

Sign in at https://console.anthropic.com and create a key. Paste it into the sidebar of the running app. The key is sent only to your local backend.

## What happens on first run

- 10 policy PDFs are generated into `knowledge_base/` (Meridian Technologies fictional company).
- Sample Q&A workbook is generated into `sample_data/`.
- The embedding model (`all-MiniLM-L6-v2`, ~80 MB) downloads once on first use into your Hugging Face cache.
- A FAISS index is built and saved into `vector_store/` so subsequent runs are instant.

## Using the sample Excel

`sample_data/PolicyBot_Sample_QA.xlsx` has three sheets:
- **Sample Questions** — 20 ready-to-ask questions covering all 10 policies.
- **Evaluation Sheet** — blank columns to record AI answers and your verdict.
- **Answer Key** — hidden by default; unhide via Excel to see the ground truth and the known flaw type per question.

## Workshop exercise

1. Pick a question from the sample sheet (or use **Load Sample** in the sidebar).
2. Ask it in the chat.
3. Read the AI response and its source. Use 👍 / 👎 to rate it.
4. Record your evaluation in Sheet 2 of the Excel.
5. After the session, reveal Sheet 3 to compare against the answer key.

## Facilitator notes

- Approximately **40%** of responses are intentionally flawed.
- Flaw types: `wrong_number`, `missing_clause`, `wrong_approver`, `hallucination`.
- A per-request log of which calls were flawed is written to `flaw_log.jsonl` in this folder.
- To adjust the rate, edit `FLAW_RATE` in `flaw_injector.py`.

## Programmatic access

The FastAPI backend is fully callable from Python:

```python
from api_client import PolicyBotClient

bot = PolicyBotClient(api_key="sk-ant-...")
print(bot.ask("How many earned leaves carry forward?")["answer"])
```

See `api_client.py` for the full client surface (`ask`, `ask_batch`, `health`, `clear_history`).
