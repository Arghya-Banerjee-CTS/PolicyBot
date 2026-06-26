"""One-time helper: materialize the embedding model at models/all-MiniLM-L6-v2/
so the app is fully offline-capable.

Strategy:
  1. If the model is already in the local Hugging Face cache, copy the snapshot
     contents (resolving symlinks) into models/all-MiniLM-L6-v2/.
  2. Otherwise, fall back to downloading via sentence-transformers and saving.

Usage:
    python fetch_model.py
"""
from __future__ import annotations
from pathlib import Path
import os
import shutil
import sys

BASE_DIR = Path(__file__).resolve().parent
TARGET_DIR = BASE_DIR / "models" / "all-MiniLM-L6-v2"
HUB_ID = "sentence-transformers/all-MiniLM-L6-v2"
HUB_CACHE_FOLDER = "models--sentence-transformers--all-MiniLM-L6-v2"


def _hub_cache_root() -> Path:
    return Path(
        os.environ.get("HF_HUB_CACHE")
        or (Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub")
    )


def _find_snapshot() -> Path | None:
    snapshots = _hub_cache_root() / HUB_CACHE_FOLDER / "snapshots"
    if not snapshots.exists():
        return None
    candidates = [p for p in snapshots.iterdir() if p.is_dir()]
    return candidates[0] if candidates else None


def _copy_from_cache(snapshot: Path) -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for entry in snapshot.iterdir():
        src = entry.resolve()
        dst = TARGET_DIR / entry.name
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        print(f"  {entry.name}")


def main() -> int:
    if TARGET_DIR.exists() and any(TARGET_DIR.iterdir()):
        print(f"Model already present at {TARGET_DIR}. Nothing to do.")
        return 0

    snapshot = _find_snapshot()
    if snapshot is not None:
        print(f"Copying from HF cache: {snapshot}")
        _copy_from_cache(snapshot)
        print(f"Done. Model materialized at {TARGET_DIR}")
        return 0

    print("No local HF cache found; attempting network download...")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"sentence-transformers not installed: {e}")
        return 1
    TARGET_DIR.parent.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(HUB_ID)
    model.save(str(TARGET_DIR))
    print(f"Done. Model saved to {TARGET_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
