"""RAG engine for PolicyBot.

Loads all PDFs from knowledge_base/, splits them into per-page chunks, embeds
them with sentence-transformers, indexes with FAISS, and persists the index
to vector_store/. Subsequent runs reload from disk.

Public API:
    engine = RAGEngine()
    engine.ensure_index()
    hits = engine.search("How many earned leaves...", k=5)
    # hits -> list[dict] with text, source_doc, page, score
"""
from __future__ import annotations
from pathlib import Path
import json
import os
import re
import pickle


_BASE_DIR_BOOT = Path(__file__).resolve().parent
_LOCAL_MODEL_DIR = _BASE_DIR_BOOT / "models" / "all-MiniLM-L6-v2"


def _prefer_local_model() -> bool:
    """Force fully-offline mode when the bundled model directory exists.

    Must run BEFORE importing huggingface_hub / sentence_transformers, which
    snapshot these env vars at import time.
    """
    if _LOCAL_MODEL_DIR.exists() and any(_LOCAL_MODEL_DIR.iterdir()):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        return True
    return False


_OFFLINE = _prefer_local_model()

import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "knowledge_base"
INDEX_DIR = BASE_DIR / "vector_store"
INDEX_FILE = INDEX_DIR / "faiss.index"
META_FILE = INDEX_DIR / "chunks.pkl"
MANIFEST_FILE = INDEX_DIR / "manifest.json"

EMBED_MODEL_HUB_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_MODEL_NAME = str(_LOCAL_MODEL_DIR) if _OFFLINE else EMBED_MODEL_HUB_ID
CHUNK_TARGET_CHARS = 900
CHUNK_OVERLAP_CHARS = 150


def _load_embed_model() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL_NAME)


def _split_text(text: str, target: int = CHUNK_TARGET_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= target:
        return [text]
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + target, n)
        if end < n:
            slice_text = text[start:end]
            cut = max(slice_text.rfind(". "), slice_text.rfind("? "), slice_text.rfind("! "))
            if cut > target * 0.5:
                end = start + cut + 1
        chunks.append(text[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def _kb_manifest() -> dict:
    items = {}
    if not KB_DIR.exists():
        return items
    for p in sorted(KB_DIR.glob("*.pdf")):
        st = p.stat()
        items[p.name] = {"size": st.st_size, "mtime": int(st.st_mtime)}
    return items


class RAGEngine:
    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._index: faiss.IndexFlatIP | None = None
        self._chunks: list[dict] = []

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = _load_embed_model()
        return self._model

    @property
    def docs_loaded(self) -> int:
        names = {c["source_doc"] for c in self._chunks}
        return len(names)

    def _embed(self, texts: list[str]) -> np.ndarray:
        vecs = self.model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
        return vecs.astype("float32")

    def _build_from_pdfs(self) -> None:
        chunks: list[dict] = []
        pdf_paths = sorted(KB_DIR.glob("*.pdf"))
        if not pdf_paths:
            raise FileNotFoundError(
                f"No PDFs found in {KB_DIR}. Run generate_pdfs.py first."
            )

        for pdf_path in pdf_paths:
            try:
                reader = PdfReader(str(pdf_path))
            except Exception as e:
                print(f"  [warn] could not read {pdf_path.name}: {e}")
                continue
            for page_idx, page in enumerate(reader.pages, start=1):
                try:
                    raw = page.extract_text() or ""
                except Exception:
                    raw = ""
                for chunk_text in _split_text(raw):
                    chunks.append({
                        "text": chunk_text,
                        "source_doc": pdf_path.name,
                        "page": page_idx,
                    })
        if not chunks:
            raise RuntimeError("No text extracted from any PDF.")

        print(f"  embedding {len(chunks)} chunks with {EMBED_MODEL_NAME} ...")
        vecs = self._embed([c["text"] for c in chunks])
        dim = vecs.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(vecs)

        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(INDEX_FILE))
        with META_FILE.open("wb") as f:
            pickle.dump(chunks, f)
        with MANIFEST_FILE.open("w", encoding="utf-8") as f:
            json.dump(_kb_manifest(), f, indent=2)

        self._index = index
        self._chunks = chunks

    def _load_from_disk(self) -> bool:
        if not (INDEX_FILE.exists() and META_FILE.exists() and MANIFEST_FILE.exists()):
            return False
        try:
            with MANIFEST_FILE.open("r", encoding="utf-8") as f:
                saved = json.load(f)
        except Exception:
            return False
        if saved != _kb_manifest():
            return False
        try:
            self._index = faiss.read_index(str(INDEX_FILE))
            with META_FILE.open("rb") as f:
                self._chunks = pickle.load(f)
            return True
        except Exception:
            return False

    def ensure_index(self) -> None:
        if self._index is not None:
            return
        if self._load_from_disk():
            print(f"  loaded FAISS index from {INDEX_DIR} ({len(self._chunks)} chunks)")
            return
        print("  building FAISS index from knowledge_base/ ...")
        self._build_from_pdfs()
        print(f"  built index ({len(self._chunks)} chunks)")

    def search(self, query: str, k: int = 5) -> list[dict]:
        self.ensure_index()
        if not query.strip():
            return []
        qv = self._embed([query])
        scores, idx = self._index.search(qv, min(k, len(self._chunks)))
        hits = []
        for score, i in zip(scores[0].tolist(), idx[0].tolist()):
            if i < 0 or i >= len(self._chunks):
                continue
            c = self._chunks[i]
            hits.append({
                "text": c["text"],
                "source_doc": c["source_doc"],
                "page": c["page"],
                "score": float(score),
            })
        return hits


if __name__ == "__main__":
    eng = RAGEngine()
    eng.ensure_index()
    print(f"docs_loaded={eng.docs_loaded}, total_chunks={len(eng._chunks)}")
    for h in eng.search("How many earned leaves carry forward?", k=3):
        print(f"  [{h['score']:.3f}] {h['source_doc']} p{h['page']}: {h['text'][:120]}...")
