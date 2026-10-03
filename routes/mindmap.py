from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from config import settings
from utils.db import Mindmap, get_session
from utils.llm import generate_mindmap_markdown
from utils.markmap import compile_markmap_html, save_mindmap

router = APIRouter(prefix="/mindmap", tags=["mindmap"])


class MindmapRequest(BaseModel):
    topic: str = Field(min_length=1)


class MindmapResponse(BaseModel):
    id: str
    topic: str
    html_url: str
    created_at: datetime | None = None


@router.post("", response_model=MindmapResponse)
def create_mindmap(body: MindmapRequest, session: Session = Depends(get_session)):
    try:
        md = generate_mindmap_markdown(body.topic)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Mindmap generation failed: {exc}") from exc
    html_doc = compile_markmap_html(md, title=body.topic)
    mindmap_id, path = save_mindmap(html_doc)

    row = Mindmap(id=mindmap_id, topic=body.topic, filename=path.name)
    session.add(row)
    session.commit()
    session.refresh(row)

    return MindmapResponse(
        id=mindmap_id,
        topic=body.topic,
        html_url=f"{settings.base_url}/mindmaps/{path.name}",
        created_at=row.created_at,
    )


@router.get("", response_model=list[MindmapResponse])
def list_mindmaps(session: Session = Depends(get_session)):
    rows = session.exec(select(Mindmap).order_by(Mindmap.created_at.desc())).all()
    return [
        MindmapResponse(
            id=r.id,
            topic=r.topic,
            html_url=f"{settings.base_url}/mindmaps/{r.filename}",
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{mindmap_id}", response_model=MindmapResponse)
def get_mindmap(mindmap_id: str, session: Session = Depends(get_session)):
    row = session.get(Mindmap, mindmap_id)
    if not row:
        raise HTTPException(404, "mindmap not found")
    return MindmapResponse(
        id=row.id,
        topic=row.topic,
        html_url=f"{settings.base_url}/mindmaps/{row.filename}",
        created_at=row.created_at,
    )
