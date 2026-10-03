import json
import os
import uuid
from pathlib import Path

import replicate
from mutagen.mp3 import MP3

from config import PODCASTS_DIR, settings


def _ensure_token() -> None:
    token = settings.replicate_api_token or os.getenv("REPLICATE_API_TOKEN", "")
    if not token:
        raise ValueError("REPLICATE_API_TOKEN is not set")
    os.environ["REPLICATE_API_TOKEN"] = token


def resolve_voice_id(speaker: str) -> str:
    s = speaker.lower().strip()
    if s in ("male", "elon", "elonmusk", "elon musk"):
        return settings.voice_elon or settings.voice_male
    if s in ("speed", "ishowspeed"):
        return settings.voice_speed
    if s in ("abdul", "dr. kalam", "apj abdul kalam"):
        return settings.voice_abdul
    if s in ("female",):
        return settings.voice_female
    return settings.voice_female


def get_audio_duration(path: Path) -> float:
    return float(MP3(str(path)).info.length)


def synthesize_speech(
    text: str,
    *,
    voice_id: str,
    output_filename: Path,
    emotion: str | None = None,
) -> None:
    _ensure_token()
    clean = text.replace("*", "").replace("$", "").replace("\\", "")
    output = replicate.run(
        settings.tts_model,
        input={
            "text": clean,
            "emotion": emotion or settings.tts_emotion,
            "voice_id": voice_id,
            "language_boost": "English",
            "english_normalization": True,
        },
    )
    output_filename.parent.mkdir(parents=True, exist_ok=True)
    with output_filename.open("wb") as f:
        f.write(output.read())


def merge_mp3_files(paths: list[Path], dest: Path) -> None:
    with dest.open("wb") as out:
        for path in paths:
            out.write(path.read_bytes())


def synthesize_podcast(dialogues: list[dict]) -> tuple[str, Path, list[dict]]:
    podcast_id = uuid.uuid4().hex[:12]
    folder = PODCASTS_DIR / podcast_id
    folder.mkdir(parents=True, exist_ok=True)

    lines: list[dict] = []
    duration_map: list[dict] = []
    total_dur = 0.0
    part_paths: list[Path] = []

    for i, d in enumerate(dialogues):
        speaker = d["speaker"]
        if speaker.lower() == "narrator":
            continue

        voice_id = resolve_voice_id(speaker)
        filename = f"{i}_{speaker}.mp3"
        path = folder / filename
        synthesize_speech(d["text"], voice_id=voice_id, output_filename=path)

        duration = get_audio_duration(path)
        duration_map.append(
            {
                "speaker": speaker,
                "from_duration": total_dur,
                "to_duration": total_dur + duration,
            }
        )
        total_dur += duration
        part_paths.append(path)

        lines.append(
            {
                "index": i,
                "role": d.get("role", f"line_{i}"),
                "speaker": speaker,
                "text": d["text"],
                "filename": filename,
                "url": f"/podcasts/{podcast_id}/{filename}",
                "duration": duration,
            }
        )

    combined = folder / "episode.mp3"
    merge_mp3_files(part_paths, combined)
    (folder / "duration_map.json").write_text(
        json.dumps(duration_map, indent=2),
        encoding="utf-8",
    )

    return podcast_id, combined, lines
