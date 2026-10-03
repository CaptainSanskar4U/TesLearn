import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from utils.db import Note, get_session
from utils.notes import create_notes_record, generate_notes_images

router = APIRouter(prefix="/notes", tags=["notes"])


class NotesRequest(BaseModel):
    topic: str = Field(min_length=1)
    summaries: str = ""


class NotesResponse(BaseModel):
    id: str
    topic: str
    notes_markdown: str
    handwritten_urls: list[str]
    diagram_urls: list[str]
    images_status: str  # pending | generating | ready | failed
    created_at: datetime | None = None


def _to_response(row: Note) -> NotesResponse:
    return NotesResponse(
        id=row.id,
        topic=row.topic,
        notes_markdown=row.notes_markdown,
        handwritten_urls=json.loads(row.handwritten_json or "[]"),
        diagram_urls=json.loads(row.diagrams_json or "[]"),
        images_status=row.images_status,
        created_at=row.created_at,
    )


@router.post("", response_model=NotesResponse)
def create_notes(body: NotesRequest, background_tasks: BackgroundTasks):
    try:
        note_id, notes_md = create_notes_record(body.topic, body.summaries)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Notes generation failed: {exc}") from exc
    background_tasks.add_task(generate_notes_images, note_id)
    return NotesResponse(
        id=note_id,
        topic=body.topic,
        notes_markdown=notes_md,
        handwritten_urls=[],
        diagram_urls=[],
        images_status="pending",
    )


@router.get("", response_model=list[NotesResponse])
def list_notes(session: Session = Depends(get_session)):
    rows = session.exec(select(Note).order_by(Note.created_at.desc())).all()
    return [_to_response(r) for r in rows]


@router.get("/{note_id}", response_model=NotesResponse)
def get_notes(note_id: str, session: Session = Depends(get_session)):
    row = session.get(Note, note_id)
    if not row:
        raise HTTPException(404, "notes not found")
    return _to_response(row)
