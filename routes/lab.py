from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from config import settings
from utils.db import Lab, get_session
from utils.llm import generate_virtual_lab_html
from utils.storage import save_lab

router = APIRouter(prefix="/lab", tags=["lab"])


class LabRequest(BaseModel):
    topic: str = Field(min_length=1)


class LabResponse(BaseModel):
    id: str
    topic: str
    html_url: str
    created_at: datetime | None = None


@router.post("", response_model=LabResponse)
def create_lab(body: LabRequest, session: Session = Depends(get_session)):
    try:
        html = generate_virtual_lab_html(body.topic)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Lab generation failed: {exc}") from exc
    lab_id, path = save_lab(html)
    row = Lab(id=lab_id, topic=body.topic, filename=path.name)
    session.add(row)
    session.commit()
    session.refresh(row)
    return LabResponse(
        id=lab_id,
        topic=body.topic,
        html_url=f"{settings.base_url}/labs/{path.name}",
        created_at=row.created_at,
    )


@router.get("", response_model=list[LabResponse])
def list_labs(session: Session = Depends(get_session)):
    rows = session.exec(select(Lab).order_by(Lab.created_at.desc())).all()
    return [
        LabResponse(
            id=r.id,
            topic=r.topic,
            html_url=f"{settings.base_url}/labs/{r.filename}",
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{lab_id}", response_model=LabResponse)
def get_lab(lab_id: str, session: Session = Depends(get_session)):
    row = session.get(Lab, lab_id)
    if not row:
        raise HTTPException(404, "lab not found")
    return LabResponse(
        id=row.id,
        topic=row.topic,
        html_url=f"{settings.base_url}/labs/{row.filename}",
        created_at=row.created_at,
    )
