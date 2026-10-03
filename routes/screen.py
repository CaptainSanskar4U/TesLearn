from fastapi import APIRouter

from utils.screen import ScreenService

router = APIRouter(prefix="/screen", tags=["screen"])


@router.get("/status")
def screen_status():
    return ScreenService().status()


@router.post("/start")
async def start_screen(mode: str = "screen"):
    return await ScreenService().start(mode)


@router.post("/stop")
async def stop_screen():
    return await ScreenService().stop()
