from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from config import settings
from utils.db import Clip, get_session
from utils.llm import generate_html
from utils.storage import save_clip

router = APIRouter(prefix="/video", tags=["video"])


class VideoRequest(BaseModel):
    topic: str = Field(min_length=1)
    duration: int = Field(default=12, ge=4, le=30)


class VideoResponse(BaseModel):
    id: str
    topic: str
    duration: int
    embed_url: str
    iframe: str
    created_at: datetime | None = None


@router.post("", response_model=VideoResponse)
def create_video(body: VideoRequest, session: Session = Depends(get_session)):
    try:
        html = generate_html(body.topic, body.duration)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Video generation failed: {exc}") from exc
    clip_id, path = save_clip(html)
    clip = Clip(id=clip_id, topic=body.topic, duration=body.duration, filename=path.name)
    session.add(clip)
    session.commit()
    session.refresh(clip)

    embed_url = f"{settings.base_url}/clips/{clip_id}.html"
    return VideoResponse(
        id=clip_id,
        topic=body.topic,
        duration=body.duration,
        embed_url=embed_url,
        iframe=f'<iframe src="{embed_url}" width="960" height="540" frameborder="0" allowfullscreen></iframe>',
        created_at=clip.created_at,
    )


@router.get("", response_model=list[VideoResponse])
def list_videos(session: Session = Depends(get_session)):
    clips = session.exec(select(Clip).order_by(Clip.created_at.desc())).all()
    return [
        VideoResponse(
            id=c.id,
            topic=c.topic,
            duration=c.duration,
            embed_url=f"{settings.base_url}/clips/{c.filename}",
            iframe=f'<iframe src="{settings.base_url}/clips/{c.filename}" width="960" height="540" frameborder="0" allowfullscreen></iframe>',
            created_at=c.created_at,
        )
        for c in clips
    ]


@router.get("/{clip_id}", response_model=VideoResponse)
def get_video(clip_id: str, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(404, "video not found")
    url = f"{settings.base_url}/clips/{clip.filename}"
    return VideoResponse(
        id=clip.id,
        topic=clip.topic,
        duration=clip.duration,
        embed_url=url,
        iframe=f'<iframe src="{url}" width="960" height="540" frameborder="0" allowfullscreen></iframe>',
        created_at=clip.created_at,
    )
