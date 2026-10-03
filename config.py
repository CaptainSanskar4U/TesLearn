from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent
CLIPS_DIR = ROOT / "clips"
PODCASTS_DIR = ROOT / "podcasts"
MINDMAPS_DIR = ROOT / "mindmaps"
COMICS_DIR = ROOT / "comics"
NOTES_DIR = ROOT / "notes"
LABS_DIR = ROOT / "labs"
DB_PATH = ROOT / "app.db"
PROMPTS_DIR = ROOT / "prompts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_model: str = "openrouter/google/gemma-4-31b-it:free"
    llm_fallback: str = "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
    image_model: str = "gemini/gemini-2.5-flash-image-preview"
    image_size: str = "1024x1024"
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    live_model: str = "models/gemini-3.1-flash-live-preview"
    replicate_api_token: str = ""
    # minimax / speech-02-turbo voice ids on Replicate
    voice_male: str = "R8_71RSEH2W"
    voice_female: str = "Friendly_Person"
    voice_speed: str = "R8_GKYQ3UBG"
    voice_elon: str = "R8_71RSEH2W"
    voice_abdul: str = "R8_X6V884WQ"
    tts_emotion: str = "happy"
    tts_model: str = "minimax/speech-02-turbo"
    base_url: str = "http://127.0.0.1:8000"


settings = Settings()
CLIPS_DIR.mkdir(exist_ok=True)
PODCASTS_DIR.mkdir(exist_ok=True)
MINDMAPS_DIR.mkdir(exist_ok=True)
COMICS_DIR.mkdir(exist_ok=True)
NOTES_DIR.mkdir(exist_ok=True)
LABS_DIR.mkdir(exist_ok=True)
