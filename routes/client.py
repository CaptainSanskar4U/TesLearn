from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from utils.client_live import run_client_session

router = APIRouter(prefix="/client", tags=["client"])


@router.get("/info")
def client_info():
    return {
        "ws": "/api/client/ws?mode=camera",
        "modes": ["camera", "screen", "viva"],
        "send": [
            {"type": "image", "mime_type": "image/jpeg", "data": "<base64 jpeg>"},
            {
                "type": "audio",
                "mime_type": "audio/pcm",
                "data": "<base64 pcm 16khz mono s16le>",
            },
        ],
        "recv": [
            {"type": "audio", "mime_type": "audio/pcm;rate=24000", "data": "<base64>"},
            {"type": "text", "text": "..."},
        ],
        "note": "Capture camera/mic/screen on the DEVICE. Server only relays to Gemini Live.",
    }


@router.websocket("/ws")
async def client_ws(ws: WebSocket, mode: str = "camera", topic: str = ""):
    if mode not in ("camera", "screen", "viva"):
        await ws.close(code=4400)
        return
    await ws.accept()
    await ws.send_json({"type": "status", "status": "linking", "mode": mode})
    try:
        await run_client_session(ws, mode, topic=topic.strip())
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await ws.send_json({"type": "error", "error": str(exc)})
        except Exception:
            pass
        await ws.close()
