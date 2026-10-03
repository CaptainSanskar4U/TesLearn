"""Vercel serverless entrypoint — exposes the FastAPI app as `app`."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app  # noqa: E402,F401  (Vercel looks for `app`)
