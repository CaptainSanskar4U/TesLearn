from fastapi import APIRouter
from pydantic import BaseModel

from utils.viva import VivaService

router = APIRouter(prefix="/viva", tags=["viva"])


class VivaStartRequest(BaseModel):
    topic: str = ""


@router.get("/status")
def viva_status():
    return VivaService().status()


@router.post("/start")
async def start_viva(body: VivaStartRequest | None = None):
    topic = (body.topic if body else "") or ""
    return await VivaService().start(topic)


@router.post("/stop")
async def stop_viva():
    return await VivaService().stop()
