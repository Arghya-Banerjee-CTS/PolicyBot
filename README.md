# PolicyBot — Meridian Technologies Policy Assistant

PolicyBot is a simple AI chatbot that answers questions about a fictional company's internal policies (HR, IT, Travel, Finance). It is built for an AI Assurance Workshop: about 40% of the answers are intentionally flawed (wrong numbers, missing clauses, wrong approvers, or hallucinations), and workshop participants practice spotting them.

## What it does

- Reads 10 PDF policy documents from `knowledge_base/`.
- Builds a local FAISS vector index over them using the `all-MiniLM-L6-v2` embedding model.
- When you ask a question, it retrieves the most relevant policy chunks and asks an LLM (OpenAI or Anthropic) to answer using only that context.
- Keeps multi-turn conversation memory per session.
- Logs every flaw-injection decision to `flaw_log.jsonl` so a facilitator can audit answers later.

Two pieces run together:
- **Backend** — FastAPI on `http://localhost:8001` (RAG + LLM calls).
- **Frontend** — Streamlit chat UI on `http://localhost:8501`.

## Requirements

- Python 3.10 or newer
- An API key for either OpenAI or Anthropic (pasted into the app's sidebar on first launch)

## Install

From inside the `policybot/` folder:

```
pip install -r requirements.txt
```

## Run

One command starts everything (PDF generation on first run, backend, then the UI):

```
python run.py
```

Then open **http://localhost:8501** in your browser. Press `Ctrl+C` in the terminal to stop.

## Optional: pre-download the embedding model

The embedding model (~80 MB) downloads automatically on first use. To fetch it ahead of time (useful for offline machines):

```
python fetch_model.py
```

## First-time configuration

1. Launch the app with `python run.py`.
2. In the left sidebar pick a **Provider** (`openai` or `anthropic`).
3. Enter your **API Key**. For OpenAI, also fill in **Base URL** and **API Version**.
4. Click **Save Configuration**. The values are written to `config.yaml`.
5. Type a question in the chat box and press **Send**.

## Calling the backend from Python

The backend is also usable directly without the UI:

```python
from api_client import PolicyBotClient

bot = PolicyBotClient(api_key="sk-ant-...")
print(bot.ask("How many earned leaves carry forward?")["answer"])
```

See [api_client.py](api_client.py) for the full client (`ask`, `ask_batch`, `health`, `clear_history`).

## Useful files

- [run.py](run.py) — single entry point (starts backend + UI)
- [backend.py](backend.py) — FastAPI endpoints (`/health`, `/config`, `/query`, `/batch`, `/session/clear`)
- [app.py](app.py) — Streamlit chat UI
- [rag_engine.py](rag_engine.py) — PDF loading, chunking, FAISS index
- [flaw_injector.py](flaw_injector.py) — controls the intentional-flaw behavior (`FLAW_RATE`)
- [config.yaml](config.yaml) — saved provider / model / key
- `knowledge_base/` — generated policy PDFs
- `vector_store/` — FAISS index (rebuilt automatically if missing)
- `flaw_log.jsonl` — audit log of which answers were flawed

## Troubleshooting

- **Port already in use** — close any other process on `8001` or `8501`, or change the ports in [run.py](run.py).
- **Backend never becomes healthy** — usually the embedding model is still downloading on first run. Wait a minute, or run `python fetch_model.py` first.
- **"Invalid API key"** — re-enter the key in the sidebar and click **Save Configuration**.
- **Want to rebuild the index** — delete the `vector_store/` folder and restart.
