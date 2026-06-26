"""Single entry point for PolicyBot.

Usage (from inside the policybot/ folder):
    python run.py

This will:
  1. Generate the 10 policy PDFs (if missing).
  2. Generate the sample Excel (if missing).
  3. Start the FastAPI backend on port 8001 as a child process.
  4. Wait until the backend's /health endpoint responds before launching the UI.
  5. Start the Streamlit frontend on port 8501 in the foreground.
  6. On Ctrl+C or exit, kill the backend's process tree so its port is released.
"""
from __future__ import annotations
from pathlib import Path
import atexit
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "knowledge_base"
SAMPLE_DIR = BASE_DIR / "sample_data"
KB_MARKER = KB_DIR / "HR_Leave_Policy.pdf"
EXCEL_MARKER = SAMPLE_DIR / "PolicyBot_Sample_QA.xlsx"

BACKEND_PORT = 8001
FRONTEND_PORT = 8501
BACKEND_HEALTH_URL = f"http://127.0.0.1:{BACKEND_PORT}/health"
BACKEND_STARTUP_TIMEOUT = 600

IS_WINDOWS = sys.platform.startswith("win")

_backend_proc: subprocess.Popen | None = None


def _terminate_backend():
    global _backend_proc
    proc = _backend_proc
    _backend_proc = None
    if not proc or proc.poll() is not None:
        return
    if IS_WINDOWS:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    else:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def _start_backend() -> subprocess.Popen:
    return subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "backend:app",
            "--port", str(BACKEND_PORT),
        ],
        cwd=str(BASE_DIR),
    )


def _wait_for_backend() -> bool:
    deadline = time.time() + BACKEND_STARTUP_TIMEOUT
    while time.time() < deadline:
        if _backend_proc and _backend_proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(BACKEND_HEALTH_URL, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            pass
        time.sleep(1)
    return False


def _run_frontend():
    subprocess.run(
        [
            sys.executable, "-m", "streamlit", "run",
            str(BASE_DIR / "app.py"),
            "--server.port", str(FRONTEND_PORT),
            "--server.headless", "false",
        ],
        cwd=str(BASE_DIR),
    )


def main():
    global _backend_proc
    print("=" * 60)
    print("  PolicyBot - AI Assurance Workshop App")
    print("=" * 60)

    if not KB_MARKER.exists():
        print("\n[1/3] Generating knowledge base PDFs (one-time)...")
        result = subprocess.run([sys.executable, str(BASE_DIR / "generate_pdfs.py")], cwd=str(BASE_DIR))
        if result.returncode != 0:
            print("PDF generation failed. See errors above. Exiting.")
            sys.exit(1)
    else:
        print("\n[1/3] Knowledge base already exists, skipping.")

    if not EXCEL_MARKER.exists():
        print("\n[2/3] Generating sample Excel...")
        result = subprocess.run([sys.executable, str(BASE_DIR / "generate_excel.py")], cwd=str(BASE_DIR))
        if result.returncode != 0:
            print("Excel generation failed. See errors above. Exiting.")
            sys.exit(1)
    else:
        print("\n[2/3] Sample Excel already exists, skipping.")

    print(f"\n[3/3] Starting backend (port {BACKEND_PORT})...")
    atexit.register(_terminate_backend)
    _backend_proc = _start_backend()

    print("      waiting for backend to become healthy (this includes embedding-model load)...")
    if not _wait_for_backend():
        print("\nBackend failed to start within the timeout window.")
        print(f"Check that port {BACKEND_PORT} is free and that dependencies are installed.")
        _terminate_backend()
        sys.exit(1)
    print("      backend ready.")

    print(f"\n>>> Open your browser at: http://localhost:{FRONTEND_PORT}")
    print(">>> Press Ctrl+C in this window to stop\n")

    try:
        _run_frontend()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        _terminate_backend()


if __name__ == "__main__":
    main()
