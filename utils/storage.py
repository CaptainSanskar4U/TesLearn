import uuid
from pathlib import Path

from config import CLIPS_DIR, LABS_DIR


def save_clip(html: str) -> tuple[str, Path]:
    clip_id = uuid.uuid4().hex[:12]
    path = CLIPS_DIR / f"{clip_id}.html"
    path.write_text(html, encoding="utf-8")
    return clip_id, path


def save_lab(html: str) -> tuple[str, Path]:
    lab_id = uuid.uuid4().hex[:12]
    path = LABS_DIR / f"{lab_id}.html"
    path.write_text(html, encoding="utf-8")
    return lab_id, path
