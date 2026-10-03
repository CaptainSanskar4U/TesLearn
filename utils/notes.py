import json
import uuid

from sqlmodel import Session

from config import NOTES_DIR, settings
from prompts import build_notes_diagram_prompt, build_notes_handwritten_prompt
from utils.db import Note, engine
from utils.llm import generate_notes_markdown, generate_panel_image


def create_notes_record(topic: str, summaries: str = "") -> tuple[str, str]:
    notes_md = generate_notes_markdown(topic, summaries)
    note_id = uuid.uuid4().hex[:12]
    folder = NOTES_DIR / note_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "notes.md").write_text(notes_md, encoding="utf-8")

    with Session(engine) as session:
        session.add(
            Note(
                id=note_id,
                topic=topic,
                notes_markdown=notes_md,
                handwritten_json="[]",
                diagrams_json="[]",
                images_status="pending",
            )
        )
        session.commit()
    return note_id, notes_md


def generate_notes_images(note_id: str) -> None:
    with Session(engine) as session:
        row = session.get(Note, note_id)
        if not row:
            return
        topic = row.topic
        row.images_status = "generating"
        session.add(row)
        session.commit()

    try:
        folder = NOTES_DIR / note_id
        folder.mkdir(parents=True, exist_ok=True)

        handwritten_urls: list[str] = []
        diagram_urls: list[str] = []

        hw_prompt = build_notes_handwritten_prompt(topic)
        for i in (1, 2):
            name = f"hw{i}.png"
            generate_panel_image(f"{hw_prompt} Variation {i}.", folder / name)
            handwritten_urls.append(f"{settings.base_url}/notes-assets/{note_id}/{name}")

        dg_prompt = build_notes_diagram_prompt(topic)
        for i in (1, 2):
            name = f"d{i}.png"
            generate_panel_image(f"{dg_prompt} Variation {i}.", folder / name)
            diagram_urls.append(f"{settings.base_url}/notes-assets/{note_id}/{name}")

        with Session(engine) as session:
            row = session.get(Note, note_id)
            if not row:
                return
            row.handwritten_json = json.dumps(handwritten_urls)
            row.diagrams_json = json.dumps(diagram_urls)
            row.images_status = "ready"
            session.add(row)
            session.commit()
    except Exception as exc:
        with Session(engine) as session:
            row = session.get(Note, note_id)
            if not row:
                return
            row.images_status = "failed"
            row.error = str(exc)[:500]
            session.add(row)
            session.commit()
