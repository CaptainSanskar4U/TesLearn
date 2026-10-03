import asyncio
import base64
import json

from google import genai
from google.genai import types
from google.genai.types import LiveConnectConfig
from starlette.websockets import WebSocket

from config import settings

SCREEN_INSTRUCTION = (
    "You are a focused learning assistant for daily doubt solving, exam preparation, and deep subject understanding. "
    "Always provide clear, structured, and concise explanations that help the user learn effectively.\n\n"
    "If the input shows entertainment content (such as Netflix, videos, movies, or social media), "
    "do not engage with it. Instead respond firmly with: "
    "'You are wasting time on entertainment apps. Close it and get back to studying.'"
)

VIVA_INSTRUCTION = (
    "You are a professional Viva Examiner for students. "
    "Begin by asking the student for their chosen topic of examination; do not decide the topic yourself. "
    "Once the topic is established, conduct a rigorous viva voce (oral examination). "
    "Ask one clinical/technical question at a time and wait for the student's response. "
    "Follow up on their answers, probe for deeper understanding, and maintain a formal, academic tone. "
    "Note: You do not have access to any visual input (screen or camera) in this session. "
    "Focus purely on the conversation and the student's verbal explanations."
)


def _client():
    key = settings.gemini_api_key
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")
    return genai.Client(http_options={"api_version": "v1beta"}, api_key=key)


def live_config(mode: str, topic: str = "") -> LiveConnectConfig:
    instruction = VIVA_INSTRUCTION if mode == "viva" else SCREEN_INSTRUCTION
    if mode == "viva" and topic.strip():
        instruction += (
            f"\n\nThe student's examination topic is: {topic.strip()}. "
            "Use this topic for the viva. Greet briefly and ask your first question."
        )
    kwargs = dict(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Algenib")
            )
        ),
        system_instruction=types.Content(parts=[types.Part(text=instruction)]),
        context_window_compression=types.ContextWindowCompressionConfig(
            trigger_tokens=104857,
            sliding_window=types.SlidingWindow(target_tokens=52428),
        ),
    )
    if mode != "viva":
        kwargs["media_resolution"] = types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
    return types.LiveConnectConfig(**kwargs)


def _b64_to_bytes(data) -> bytes:
    if isinstance(data, bytes):
        return data
    return base64.b64decode(data)


async def run_client_session(ws: WebSocket, mode: str, topic: str = "") -> None:
    """Relay client camera/mic (and optional frames) to Gemini Live; stream audio back."""
    async with _client().aio.live.connect(
        model=settings.live_model,
        config=live_config(mode, topic),
    ) as session:
        await ws.send_json({"type": "status", "status": "connected", "mode": mode})

        if mode == "viva" and topic.strip():
            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part(text=f'My examination topic is "{topic.strip()}". Please begin the viva.')],
                ),
                turn_complete=True,
            )

        async def from_client():
            while True:
                msg = await ws.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                payload = msg.get("text")
                if payload is None:
                    raw = msg.get("bytes")
                    if raw:
                        await session.send_realtime_input(
                            audio={"data": raw, "mime_type": "audio/pcm"}
                        )
                    continue
                data = json.loads(payload)
                kind = data.get("type")
                mime = data.get("mime_type", "")
                blob = data.get("data")
                if kind in ("audio",) or mime.startswith("audio/"):
                    await session.send_realtime_input(
                        audio={
                            "data": _b64_to_bytes(blob),
                            "mime_type": mime or "audio/pcm",
                        }
                    )
                elif kind == "activity_start":
                    await session.send_realtime_input(
                        activity_start=types.ActivityStart()
                    )
                elif kind in ("activity_end", "turn_complete"):
                    await session.send_realtime_input(activity_end=types.ActivityEnd())
                    await session.send_realtime_input(audio_stream_end=True)
                elif kind == "text" and data.get("text"):
                    await session.send_client_content(
                        turns=types.Content(
                            role="user",
                            parts=[types.Part(text=str(data["text"]))],
                        ),
                        turn_complete=True,
                    )
                elif mode != "viva" and (
                    kind in ("image", "video", "frame")
                    or mime.startswith("image/")
                    or mime.startswith("video/")
                ):
                    await session.send_realtime_input(
                        video={"data": blob, "mime_type": mime or "image/jpeg"}
                    )

        async def to_client():
            async for response in session.receive():
                if data := response.data:
                    chunk = data if isinstance(data, bytes) else bytes(data)
                    await ws.send_json(
                        {
                            "type": "audio",
                            "mime_type": "audio/pcm;rate=24000",
                            "data": base64.b64encode(chunk).decode(),
                        }
                    )
                if text := response.text:
                    await ws.send_json({"type": "text", "text": text})

        await asyncio.gather(from_client(), to_client())
