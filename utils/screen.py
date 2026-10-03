import asyncio
import base64
import io
import traceback
from typing import Optional

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None  # type: ignore
try:
    import pyaudio  # type: ignore
except ImportError:  # fast local run without PortAudio
    pyaudio = None  # type: ignore
import PIL.Image
from google import genai
from google.genai import types
from google.genai.types import LiveConnectConfig

from config import settings

FORMAT = pyaudio.paInt16 if pyaudio else None
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
DEFAULT_MODE = "screen"


def _client():
    key = settings.gemini_api_key
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")
    return genai.Client(http_options={"api_version": "v1beta"}, api_key=key)

CONFIG: LiveConnectConfig = types.LiveConnectConfig(
    response_modalities=[types.Modality.AUDIO],
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Algenib")
        ),
    ),
    system_instruction=types.Content(
        parts=[
            types.Part(
                text=(
                    "You are a focused learning assistant for daily doubt solving, exam preparation, and deep subject understanding. "
                    "Always provide clear, structured, and concise explanations that help the user learn effectively.\n\n"
                    "If the input shows entertainment content (such as Netflix, videos, movies, or social media), "
                    "do not engage with it. Instead respond firmly with: "
                    "'You are wasting time on entertainment apps. Close it and get back to studying.'"
                )
            )
        ]
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=104857,
        sliding_window=types.SlidingWindow(target_tokens=52428),
    ),
)


class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode
        self.last_text = ""
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.audio_stream = None
        self.pya = None

    def _get_frame(self, cap):
        ret, frame = cap.read()
        if not ret:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail((1024, 1024))
        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)
        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_io.read()).decode(),
        }

    async def get_frames(self):
        if cv2 is None:
            raise RuntimeError("opencv not installed — camera mode disabled in fast local mode")
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        try:
            while True:
                frame = await asyncio.to_thread(self._get_frame, cap)
                if frame is None:
                    break
                await asyncio.sleep(1.0)
                if self.out_queue is None:
                    continue
                try:
                    self.out_queue.put_nowait(frame)
                except asyncio.QueueFull:
                    self.out_queue.get_nowait()
                    self.out_queue.put_nowait(frame)
        finally:
            cap.release()

    def _get_screen(self):
        import mss

        sct = mss.mss()
        monitor = sct.monitors[0]
        i = sct.grab(monitor)
        img = PIL.Image.frombytes("RGB", i.size, i.rgb)
        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)
        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_io.read()).decode(),
        }

    async def get_screen(self):
        while True:
            frame = await asyncio.to_thread(self._get_screen)
            await asyncio.sleep(1.0)
            if self.out_queue is None:
                continue
            try:
                self.out_queue.put_nowait(frame)
            except asyncio.QueueFull:
                self.out_queue.get_nowait()
                self.out_queue.put_nowait(frame)

    async def send_realtime(self):
        while True:
            if self.out_queue is None:
                await asyncio.sleep(0.1)
                continue
            msg = await self.out_queue.get()
            if self.session is None:
                continue
            mime = msg.get("mime_type", "")
            data = msg.get("data")
            if mime.startswith("audio/"):
                await self.session.send_realtime_input(audio={"data": data, "mime_type": mime})
            elif mime.startswith("video/") or mime.startswith("image/"):
                await self.session.send_realtime_input(video={"data": data, "mime_type": mime})

    async def listen_audio(self):
        if not self.pya:
            return
        mic_info = self.pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=int(mic_info["index"]),
            frames_per_buffer=CHUNK_SIZE,
        )
        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            if self.out_queue is None:
                continue
            payload = {"data": data, "mime_type": "audio/pcm"}
            try:
                self.out_queue.put_nowait(payload)
            except asyncio.QueueFull:
                self.out_queue.get_nowait()
                self.out_queue.put_nowait(payload)

    async def receive_audio(self):
        while True:
            if self.session is None:
                await asyncio.sleep(0.1)
                continue
            async for response in self.session.receive():
                if data := response.data:
                    if self.audio_in_queue is not None:
                        self.audio_in_queue.put_nowait(data)
                if text := response.text:
                    self.last_text = text
                    print(text, end="", flush=True)
            if self.audio_in_queue is not None:
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()

    async def play_audio(self):
        if not self.pya:
            return
        stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            while True:
                if self.audio_in_queue is not None:
                    bytestream = await self.audio_in_queue.get()
                    await asyncio.to_thread(stream.write, bytestream)
                else:
                    await asyncio.sleep(0.1)
        finally:
            stream.stop_stream()
            stream.close()

    async def run(self):
        if pyaudio is None:
            raise RuntimeError("pyaudio not installed — screen (server mic) disabled in fast local mode")
        self.pya = pyaudio.PyAudio()
        try:
            async with (
                _client().aio.live.connect(model=settings.live_model, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
                while True:
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception:
            traceback.print_exc()
        finally:
            if self.audio_stream:
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception:
                    pass
            if self.pya:
                self.pya.terminate()


class ScreenService:
    _instance = None
    _task: Optional[asyncio.Task] = None
    _audio_loop: Optional[AudioLoop] = None
    _mode: str = DEFAULT_MODE

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _running(self) -> bool:
        return self._task is not None and not self._task.done()

    def status(self) -> dict:
        loop = self._audio_loop
        return {
            "running": self._running(),
            "mode": self._mode,
            "last_text": loop.last_text if loop else "",
        }

    async def start(self, mode: str = "screen"):
        if self._running():
            return {"status": "already running", **self.status()}
        self._mode = mode
        self._audio_loop = AudioLoop(video_mode=mode)
        self._task = asyncio.create_task(self._audio_loop.run())
        return {"status": "started", "mode": mode}

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                return {"status": "error", "error": str(exc)}
            self._task = None
            self._audio_loop = None
            self._mode = DEFAULT_MODE
            return {"status": "stopped"}
        return {"status": "not running"}
