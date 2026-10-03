import asyncio
import traceback
from typing import Optional

try:
    import pyaudio  # type: ignore
except ImportError:  # fast local run without PortAudio
    pyaudio = None  # type: ignore
from google import genai
from google.genai import types
from google.genai.types import LiveConnectConfig

from config import settings

FORMAT = pyaudio.paInt16 if pyaudio else None
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

VIVA_BASE_INSTRUCTION = (
    "You are a professional Viva Examiner for students. "
    "Conduct a rigorous viva voce (oral examination). "
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


def _viva_config(topic: str = "") -> LiveConnectConfig:
    instruction = VIVA_BASE_INSTRUCTION
    if topic.strip():
        instruction += (
            f"\n\nThe student's examination topic is: {topic.strip()}. "
            "Use this topic for the viva. Greet briefly and ask your first question."
        )
    return types.LiveConnectConfig(
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


class AudioLoop:
    def __init__(self, topic: str = ""):
        self.topic = topic.strip()
        self.last_text = ""
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.audio_stream = None
        self.pya = None

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
            raise RuntimeError("pyaudio not installed — viva (server mic) disabled in fast local mode")
        self.pya = pyaudio.PyAudio()
        try:
            async with (
                _client().aio.live.connect(
                    model=settings.live_model,
                    config=_viva_config(self.topic),
                ) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                if self.topic:
                    await session.send_client_content(
                        turns=types.Content(
                            role="user",
                            parts=[
                                types.Part(
                                    text=f'My examination topic is "{self.topic}". Please begin the viva.'
                                )
                            ],
                        ),
                        turn_complete=True,
                    )

                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
                while True:
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception:
            traceback.print_exc()
            raise
        finally:
            if self.audio_stream:
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception:
                    pass
            if self.pya:
                self.pya.terminate()


class VivaService:
    _instance = None
    _task: Optional[asyncio.Task] = None
    _audio_loop: Optional[AudioLoop] = None
    _topic: str = ""

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
            "last_text": loop.last_text if loop else "",
            "topic": self._topic,
        }

    async def start(self, topic: str = ""):
        if self._running():
            return {"status": "already running", **self.status()}
        self._topic = topic.strip()
        self._audio_loop = AudioLoop(topic=self._topic)
        self._task = asyncio.create_task(self._audio_loop.run())
        return {"status": "started", "topic": self._topic}

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
            self._topic = ""
            return {"status": "stopped"}
        return {"status": "not running"}
