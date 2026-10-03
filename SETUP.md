# TesLearn Backend — Complete Project Documentation

> **TesLearn** is an AI-powered EdTech backend that transforms any study topic into
> rich multi-modal learning content — animated videos, podcasts, mind maps, comic strips,
> AI-generated notes with diagrams, interactive virtual labs, and live AI tutoring via audio.

---

## 📖 Project Idea

Students learn differently. Some understand better through visuals, others through audio,
some through storytelling, and others through hands-on experimentation. TesLearn solves the
"one-size-fits-all" problem in education by generating **7 distinct learning formats** from a
single topic string, powered by Google's Gemini AI family.

The backend is designed to be consumed by a Flutter/FlutterFlow mobile app but also ships
a minimal HTML test frontend.

### Core Features

| Feature | Route | Description |
|---|---|---|
| 🎬 **Motion Video** | `POST /api/video` | Generates a GSAP-animated SVG explainer video (HTML) for any topic |
| 🎙️ **Podcast** | `POST /api/podcast` | Generates a 3-turn Male/Female dialogue script then synthesizes real MP3 audio via MiniMax TTS |
| 🗺️ **Mind Map** | `POST /api/mindmap` | Generates an interactive Markmap HTML mind map |
| 🦸 **Comic Strip** | `POST /api/comic` | Creates a 2-panel AI-generated comic with captions & dialogue using Gemini image models |
| 📝 **Smart Notes** | `POST /api/notes` | Generates structured Markdown notes + 2 handwritten-style images + 2 diagram images |
| 🧪 **Virtual Lab** | `POST /api/lab` | Generates a fully interactive HTML5 virtual science lab simulation |
| 💬 **Chat Tutor** | `POST /api/chat` | Multi-turn Socratic AI tutor scoped to a topic with guardrails |
| 🎓 **Viva Examiner** | `POST /api/viva/start` | Real-time live audio oral exam with Gemini Live |
| 🖥️ **Screen Assistant** | `POST /api/screen/start` | Live AI tutor watching your screen/camera via Gemini Live |
| 🔌 **WebSocket Client** | `WS /api/client/ws` | Generic WebSocket relay for Flutter app to Gemini Live |
| 🛡️ **Guardrail** | `POST /api/guardrail/check` | Content filter to block off-topic or harmful prompts |

---

## 🏗️ Technical Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL CLIENTS                               │
│           Flutter App  ·  HTML Test Frontend  ·  REST Clients        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  HTTP REST + WebSocket
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION (main.py)                   │
│   CORS Middleware → Static File Mounts → API Routers                 │
│                                                                       │
│  ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌────────────────────┐ │
│  │  /api/chat │ │/api/video  │ │/api/notes│ │  /api/guardrail    │ │
│  │  /api/viva │ │/api/podcast│ │/api/comic│ │  /api/mindmap      │ │
│  │  /api/screen│ /api/lab   │ │/api/client│ └────────────────────┘ │
│  └────────────┘ └────────────┘ └──────────┘                        │
│                                                                       │
│  ┌─────────────────────── UTILS LAYER ─────────────────────────────┐ │
│  │  llm.py      LiteLLM wrapper (Gemini text + image completions)  │ │
│  │  tts.py      Replicate / MiniMax TTS for podcast audio          │ │
│  │  db.py       SQLModel/SQLite ORM (Clip, Podcast, Mindmap,       │ │
│  │              Comic, Note, Lab tables)                            │ │
│  │  viva.py     PyAudio + Gemini Live SDK (server-side mic)        │ │
│  │  screen.py   PyAudio + OpenCV/mss + Gemini Live (screen grab)   │ │
│  │  client_live.py   WebSocket relay to Gemini Live                │ │
│  │  notes.py    Background image generation for notes              │ │
│  │  comic.py    Multi-step comic script + image pipeline           │ │
│  │  markmap.py  Markdown → Markmap HTML compiler                   │ │
│  │  storage.py  UUID-keyed HTML file storage (clips, labs)         │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌──────────────── PROMPTS LAYER (prompts/*.txt) ──────────────────┐ │
│  │  motion_graphics  podcast  mindmap  comic_script                │ │
│  │  comic_image_prompts  notes  notes_handwritten  notes_diagram   │ │
│  │  virtual_lab  guardrail  chat_guardrail  chat                   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────────────┘
              ┌──────────────┴──────────────────┐
              ▼                                 ▼
┌─────────────────────────┐       ┌─────────────────────────────────┐
│  Google Gemini AI       │       │  Replicate / MiniMax TTS        │
│  gemini-2.0-flash       │       │  speech-02-turbo                │
│    (text generation)    │       │  Voice IDs: Male, Female,       │
│  gemini-2.5-flash-      │       │  Speed, Elon, Abdul             │
│    image-preview        │       └─────────────────────────────────┘
│    (comic/note images)  │
│  gemini-live-001        │
│    (real-time audio)    │
└─────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   LOCAL FILE STORAGE (auto-created)                  │
│   clips/      GSAP animated HTML videos                             │
│   podcasts/   MP3 audio files + duration_map.json                   │
│   mindmaps/   Markmap HTML files                                    │
│   comics/     PNG images + meta.json                                │
│   notes/      notes.md + hw1.png + hw2.png + d1.png + d2.png       │
│   labs/       Interactive HTML5 lab simulations                     │
│   app.db      SQLite database (all records)                         │
└──────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **LiteLLM** is used as a universal LLM gateway — all text and image completions go through it with the `gemini/` prefix to force Google AI Studio routing (not Vertex AI).
- **SQLModel + SQLite** provides zero-config persistent storage — no external database needed.
- **Background Tasks** (FastAPI) handle the 4-image generation for notes asynchronously so the API returns immediately with markdown while images generate in the background.
- **Singleton Services** (`VivaService`, `ScreenService`) maintain the state of live audio loops as `asyncio.Task` objects — one session at a time.
- **Guardrails** run on every chat message and on new content creation requests to filter off-topic or harmful content.
- The **client WebSocket** (`/api/client/ws`) enables Flutter to stream mic audio + camera/screen frames directly to Gemini Live from the device, keeping the server as a pure relay.

---

## ⚙️ Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | >= 3.13 | Required by `pyproject.toml` |
| `uv` (package manager) | Latest | Recommended; or use `pip` |
| Google Gemini API Key | — | https://aistudio.google.com/app/apikey |
| Replicate API Token | — | https://replicate.com/account/api-tokens (only for podcast) |
| PortAudio | — | System library for `pyaudio` (mic/speaker) |

### Installing PortAudio on Windows
```powershell
# Option A: via conda
conda install -c conda-forge portaudio

# Option B: pre-built wheel (no compiler needed)
pip install pipwin
pipwin install pyaudio
```

---

## 🚀 Quick Start (Local Development)

### Step 1 — Clone and enter the project
```powershell
git clone https://github.com/kevinnadar22/flutterflow-teslearn-backend.git
cd flutterflow-teslearn-backend
```

### Step 2 — Create and fill `.env`
```powershell
copy .env.example .env
# Then open .env and fill in your GEMINI_API_KEY and REPLICATE_API_TOKEN
```

### Step 3 — Install dependencies

**Using `uv` (recommended):**
```powershell
pip install uv           # install uv if not already installed
uv sync                  # installs all deps from uv.lock
```

**Using `pip` (alternative):**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### Step 4 — Start the server
```powershell
# Using uv (recommended)
uv run uvicorn main:app --reload --port 8000

# Using pip/venv
uvicorn main:app --reload --port 8000
```

The API is now live at **http://127.0.0.1:8000**

### Step 5 — Explore the API
- **Interactive docs:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health
- **ReDoc:** http://127.0.0.1:8000/redoc

---

## 🧪 Running Tests (Scripts)

The `scripts/` directory has standalone HTTP test scripts. Make sure the server is running first.

```powershell
cd scripts

python test_health.py
python test_guardrail.py
python test_video.py
python test_podcast.py    # requires REPLICATE_API_TOKEN
python test_mindmap.py
python test_comic.py      # slow — generates images
python test_notes.py
python test_lab.py
python test_client.py
python test_screen.py
python test_viva.py
```

**Override the topic or base URL:**
```powershell
$env:TEST_TOPIC="Newton's Laws of Motion"; python test_video.py
$env:BASE_URL="https://your-server.com"; python test_notes.py
```

---

## 🐳 Running with Docker

```powershell
# Build the image
docker build -t teslearn-backend .

# Run with your .env file
docker run -p 8000:8000 --env-file .env teslearn-backend
```

> Note: The Docker image includes PortAudio, libGL, and GLib for OpenCV and PyAudio support.

---

## 📡 API Reference

### Base URL: `http://127.0.0.1:8000`

#### Guardrail
```
POST /api/guardrail/check
Body: { "prompt": "string" }
Response: { "status": "success|error", "allowed": bool, "reason": "string" }
```

#### Chat Tutor
```
POST /api/chat
Body: {
  "topic": "Photosynthesis",
  "messages": [
    { "role": "user", "content": "What is the light reaction?" }
  ]
}
Response: { "reply": "string", "topic": "string" }
```

#### Motion Video
```
POST /api/video
Body: { "topic": "Photosynthesis", "duration": 12 }   # duration: 4-30 seconds
Response: { "id", "topic", "duration", "embed_url", "iframe", "created_at" }

GET /api/video            # list all
GET /api/video/{id}       # get one
```

#### Podcast
```
POST /api/podcast
Body: { "topic": "Photosynthesis" }
Response: { "id", "topic", "audio_url", "created_at" }

GET /api/podcast          # list all
GET /api/podcast/{id}     # get one
```

#### Mind Map
```
POST /api/mindmap
Body: { "topic": "Photosynthesis" }
Response: { "id", "topic", "html_url", "created_at" }

GET /api/mindmap          # list all
GET /api/mindmap/{id}     # get one
```

#### Comic Strip
```
POST /api/comic
Body: { "topic": "Photosynthesis" }
Response: { "id", "topic", "title", "image_urls": [], "panels": [], "created_at" }

GET /api/comic            # list all
GET /api/comic/{id}       # get one
```

#### Smart Notes
```
POST /api/notes
Body: { "topic": "Photosynthesis", "summaries": "optional context" }
Response: {
  "id", "topic", "notes_markdown",
  "handwritten_urls": [],  # populated async
  "diagram_urls": [],      # populated async
  "images_status": "pending|generating|ready|failed",
  "created_at"
}

GET /api/notes            # list all
GET /api/notes/{id}       # poll for image status
```

#### Virtual Lab
```
POST /api/lab
Body: { "topic": "Boyle's Law" }
Response: { "id", "topic", "html_url", "created_at" }

GET /api/lab              # list all
GET /api/lab/{id}         # get one
```

#### Viva Examiner (Live Audio — Server Mic)
```
GET  /api/viva/status     # { running, last_text, topic }
POST /api/viva/start      # Body: { "topic": "optional" }
POST /api/viva/stop
```

#### Screen/Camera Assistant (Live Audio — Server Camera)
```
GET  /api/screen/status   # { running, mode, last_text }
POST /api/screen/start    # ?mode=screen|camera
POST /api/screen/stop
```

#### WebSocket Client Relay (Device Mic/Camera -> Gemini Live)
```
GET /api/client/info
WS  /api/client/ws?mode=camera|screen|viva[&topic=...]

# Send (from device):
{ "type": "audio", "mime_type": "audio/pcm", "data": "<base64 PCM 16kHz mono s16le>" }
{ "type": "image", "mime_type": "image/jpeg", "data": "<base64 JPEG>" }

# Receive (from server):
{ "type": "audio", "mime_type": "audio/pcm;rate=24000", "data": "<base64>" }
{ "type": "text",  "text": "..." }
{ "type": "status", "status": "connecting|connected", "mode": "..." }
```

---

## 🗂️ Project Structure

```
flutterflow-teslearn-backend/
├── main.py              # FastAPI app: registers all routers + static mounts
├── config.py            # Settings (pydantic-settings), dir paths, DB path
├── pyproject.toml       # Project metadata and dependencies
├── Dockerfile           # Docker image with PortAudio + OpenCV deps
├── .env                 # YOUR secrets go here (gitignored)
├── .env.example         # Template for .env
├── SETUP.md             # This file
│
├── routes/              # FastAPI APIRouters (one file per feature)
│   ├── chat.py          # POST /api/chat
│   ├── video.py         # POST/GET /api/video
│   ├── podcast.py       # POST/GET /api/podcast
│   ├── mindmap.py       # POST/GET /api/mindmap
│   ├── comic.py         # POST/GET /api/comic
│   ├── notes.py         # POST/GET /api/notes
│   ├── lab.py           # POST/GET /api/lab
│   ├── screen.py        # GET/POST /api/screen
│   ├── viva.py          # GET/POST /api/viva
│   ├── client.py        # WS /api/client/ws
│   └── guardrail.py     # POST /api/guardrail/check
│
├── utils/               # Business logic and third-party integrations
│   ├── llm.py           # LiteLLM text + image completions via Gemini
│   ├── tts.py           # Replicate MiniMax TTS synthesis
│   ├── db.py            # SQLModel ORM models + SQLite engine
│   ├── notes.py         # Notes creation + background image generation
│   ├── comic.py         # Comic multi-step pipeline
│   ├── markmap.py       # Markdown to Markmap HTML compiler
│   ├── storage.py       # UUID-keyed file save helpers
│   ├── viva.py          # VivaService (Gemini Live + PyAudio, server-side)
│   ├── screen.py        # ScreenService (Gemini Live + OpenCV/mss, server-side)
│   └── client_live.py   # WebSocket to Gemini Live relay for device clients
│
├── prompts/             # All LLM prompt templates (.txt files)
│   ├── __init__.py      # Prompt builder functions
│   ├── motion_graphics.txt
│   ├── podcast.txt
│   ├── mindmap.txt
│   ├── comic_script.txt
│   ├── comic_image_prompts.txt
│   ├── notes.txt
│   ├── notes_handwritten.txt
│   ├── notes_diagram.txt
│   ├── virtual_lab.txt
│   ├── guardrail.txt
│   ├── chat_guardrail.txt
│   └── chat.txt
│
├── scripts/             # Standalone HTTP test scripts
│   ├── _http.py         # Shared HTTP call helper
│   ├── test_health.py
│   ├── test_video.py
│   ├── test_podcast.py
│   ├── test_mindmap.py
│   ├── test_comic.py
│   ├── test_notes.py
│   ├── test_lab.py
│   ├── test_client.py
│   ├── test_screen.py
│   ├── test_viva.py
│   └── test_guardrail.py
│
├── frontend/            # Minimal HTML/JS test UI
│   ├── index.html       # Feature selector dashboard
│   ├── live.html        # WebSocket Live session tester
│   ├── result.html      # Content viewer
│   └── ...
│
├── virtual_lab.html     # Example lab HTML (used as prompt context)
├── virtual_lab_3d.html  # Example 3D lab HTML
└── index.html           # Root test page
```

---

## 🔧 Remaining Work (from todo.md)

- [ ] **Test Viva route end-to-end** — verify `POST /api/viva/start` correctly starts the Gemini Live session, and `POST /api/viva/stop` cleanly cancels it.
- [ ] **Test Screen route end-to-end** — verify `POST /api/screen/start?mode=screen` and `?mode=camera` work with real PyAudio + OpenCV/mss on the server machine.
- [ ] **Run `test_viva.py` and `test_screen.py`** from the `scripts/` directory.

---

## 🔑 Secret Keys Summary

| Variable | Where to Get | Required For |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey | Everything — LLM text, image gen, Gemini Live |
| `REPLICATE_API_TOKEN` | https://replicate.com/account/api-tokens | Podcast audio synthesis only |

---

## 💡 Tips

- For development, `--reload` makes uvicorn hot-reload on code changes.
- The SQLite `app.db` is auto-created on first run — no migration step needed.
- All media folders (`clips/`, `podcasts/`, etc.) are auto-created on startup.
- Notes image generation runs in the background; poll `GET /api/notes/{id}` until `images_status == "ready"`.
- The Viva and Screen routes use **server-side** mic/speaker. The WebSocket client route (`/api/client/ws`) is for **device-side** mic/camera (Flutter app).
