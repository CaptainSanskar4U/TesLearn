import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from config import COMICS_DIR, settings
from utils.comic import build_comic
from utils.db import Comic, get_session

router = APIRouter(prefix="/comic", tags=["comic"])


class ComicRequest(BaseModel):
    topic: str = Field(min_length=1)


class ComicPanel(BaseModel):
    url: str
    caption: str = ""
    dialogue: str = ""


class ComicResponse(BaseModel):
    id: str
    topic: str
    title: str
    image_urls: list[str]
    panels: list[ComicPanel] = []
    created_at: datetime | None = None


def _urls_from_row(row: Comic) -> list[str]:
    if row.filename.startswith("["):
        rels = json.loads(row.filename)
        return [f"{settings.base_url}/comics/{row.id}/{name}" for name in rels]
    return [
        f"{settings.base_url}/comics/{row.id}/p1_1.png",
        f"{settings.base_url}/comics/{row.id}/p2_1.png",
    ]


def _panel_text(panel: dict, *keys: str) -> str:
    for key in keys:
        value = panel.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _panels_from_meta(comic_id: str, urls: list[str]) -> list[ComicPanel]:
    meta_path = COMICS_DIR / comic_id / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        panels: list[ComicPanel] = []
        for i, panel in enumerate(meta.get("panels", [])):
            panels.append(
                ComicPanel(
                    url=panel.get("url") or (urls[i] if i < len(urls) else ""),
                    caption=_panel_text(panel, "overlay_caption", "caption"),
                    dialogue=_panel_text(panel, "overlay_dialogue", "dialogue"),
                )
            )
        if panels:
            return panels
    return [ComicPanel(url=url) for url in urls]


def _panels_from_build_meta(meta: dict) -> list[ComicPanel]:
    return [
        ComicPanel(
            url=panel["url"],
            caption=_panel_text(panel, "overlay_caption", "caption"),
            dialogue=_panel_text(panel, "overlay_dialogue", "dialogue"),
        )
        for panel in meta.get("panels", [])
    ]


def _response_from_row(row: Comic) -> ComicResponse:
    urls = _urls_from_row(row)
    return ComicResponse(
        id=row.id,
        topic=row.topic,
        title=row.title,
        image_urls=urls,
        panels=_panels_from_meta(row.id, urls),
        created_at=row.created_at,
    )


@router.post("", response_model=ComicResponse)
def create_comic(body: ComicRequest, session: Session = Depends(get_session)):
    try:
        comic_id, meta = build_comic(body.topic)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            502,
            f"Comic image generation needs a paid image model or GEMINI_API_KEY (script works via OpenRouter): {exc}",
        ) from exc
    names = [p["filename"] for p in meta["panels"]]
    row = Comic(
        id=comic_id,
        topic=body.topic,
        title=meta["title"],
        filename=json.dumps(names),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    panels = _panels_from_build_meta(meta)
    return ComicResponse(
        id=comic_id,
        topic=body.topic,
        title=meta["title"],
        image_urls=meta["image_urls"],
        panels=panels,
        created_at=row.created_at,
    )


@router.get("", response_model=list[ComicResponse])
def list_comics(session: Session = Depends(get_session)):
    rows = session.exec(select(Comic).order_by(Comic.created_at.desc())).all()
    return [_response_from_row(r) for r in rows]


@router.get("/{comic_id}", response_model=ComicResponse)
def get_comic(comic_id: str, session: Session = Depends(get_session)):
    row = session.get(Comic, comic_id)
    if not row:
        raise HTTPException(404, "comic not found")
    return _response_from_row(row)
