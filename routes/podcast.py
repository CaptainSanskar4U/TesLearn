import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from config import settings
from utils.db import Podcast, get_session
from utils.llm import generate_podcast_script
from utils.tts import synthesize_podcast

router = APIRouter(prefix="/podcast", tags=["podcast"])


class PodcastRequest(BaseModel):
    topic: str = Field(min_length=1)


class PodcastResponse(BaseModel):
    id: str
    topic: str
    audio_url: str
    created_at: datetime | None = None


@router.post("", response_model=PodcastResponse)
def create_podcast(body: PodcastRequest, session: Session = Depends(get_session)):
    try:
        dialogues = generate_podcast_script(body.topic)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Podcast script generation failed: {exc}") from exc
    try:
        podcast_id, _combined, lines = synthesize_podcast(dialogues)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            502,
            f"Podcast audio needs REPLICATE_API_TOKEN (script OK): {exc}",
        ) from exc

    row = Podcast(
        id=podcast_id,
        topic=body.topic,
        filename=f"{podcast_id}/episode.mp3",
        script_json=json.dumps(lines),
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    return PodcastResponse(
        id=podcast_id,
        topic=body.topic,
        audio_url=f"{settings.base_url}/podcasts/{podcast_id}/episode.mp3",
        created_at=row.created_at,
    )


@router.get("", response_model=list[PodcastResponse])
def list_podcasts(session: Session = Depends(get_session)):
    rows = session.exec(select(Podcast).order_by(Podcast.created_at.desc())).all()
    return [
        PodcastResponse(
            id=r.id,
            topic=r.topic,
            audio_url=f"{settings.base_url}/podcasts/{r.filename}",
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{podcast_id}", response_model=PodcastResponse)
def get_podcast(podcast_id: str, session: Session = Depends(get_session)):
    row = session.get(Podcast, podcast_id)
    if not row:
        raise HTTPException(404, "podcast not found")
    return PodcastResponse(
        id=row.id,
        topic=row.topic,
        audio_url=f"{settings.base_url}/podcasts/{row.filename}",
        created_at=row.created_at,
    )
