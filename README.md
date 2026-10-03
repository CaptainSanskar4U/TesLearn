<div align="center">

<pre>
████████╗███████╗███████╗██╗     ███████╗ █████╗ ██████╗ ███╗   ██╗
╚══██╔══╝██╔════╝██╔════╝██║     ██╔════╝██╔══██╗██╔══██╗████╗  ██║
   ██║   █████╗  ███████╗██║     █████╗  ███████║██████╔╝██╔██╗ ██║
   ██║   ██╔══╝  ╚════██║██║     ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║
   ██║   ███████╗███████║███████╗███████╗██║  ██║██║  ██║██║ ╚████║
   ╚═╝   ╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
</pre>

# Type one topic. Get a whole school.

**TesLearn turns any study topic into 7 AI-generated learning experiences — animated video, virtual lab, mind map, smart notes, podcast, comic strip, and a Socratic AI tutor — from a single backend.**

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-powered-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-free_models-purple?style=for-the-badge)](https://openrouter.ai)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-100+_models-orange?style=for-the-badge)](https://docs.litellm.ai)
[![SQLite](https://img.shields.io/badge/SQLite-zero_config-lightgrey?style=for-the-badge)](https://sqlite.org)

**Live in 60 seconds:** `uvicorn main:app --port 8000` → open `/ui` · API docs at `/docs` · health at `/health`

</div>

---

## 👀 TL;DR for judges (30 seconds)

| # | Fact |
|---|------|
| 1 | **One input → 7 outputs.** Student types *"Photosynthesis"* and gets video + lab + mindmap + notes + podcast + comic + tutor chat. |
| 2 | **Runs on FREE AI.** Default model `openrouter/google/gemma-4-31b-it:free` (262k context) with automatic fallback — no paid key needed for the core demo. |
| 3 | **Real product shape.** 11 API routers, guardrailed tutor, SQLite persistence, static hosting of every artifact, test UI at `/ui`, interactive docs at `/docs`. |
| 4 | **Honest limits.** Audio MP3s need Replicate, images need an image model, live mic needs a Gemini key — everything else works free, and failures return clean `502` messages, never silent 500s. |
| 5 | **Big future.** Real live human-teacher support: escalate stuck AI sessions to a teacher, scheduled live classes, proctored viva mode. See [Future](#-future-real-live-teacher-support). |

---

## ❌ The Problem

Education is **one-size-fits-all**, but students aren't:

- 📖 Some learn by **reading**, others by **watching**, **listening**, **doing**, or **story**.
- 🎓 A single textbook chapter leaves visual, auditory, and hands-on learners behind.
- 🤖 Generic chatbots answer questions but don't **generate curriculum** in multiple formats.
- 💸 Existing content studios are slow and expensive — teachers can't produce a video + lab + comic for every topic by hand.

**Problem statement:** *How can one topic string instantly become a full multi-modal learning experience that any student, on any device, can learn from — for near-zero cost?*

---

## ✅ The Solution: TesLearn

A **FastAPI backend** that takes `{ "topic": "Newton's Laws" }` and orchestrates LLMs into finished learning artifacts:

```
Student topic ─┐
               ▼
        ┌─────────────┐     ┌──────────────────────────────────┐
        │  FastAPI    │────▶│  utils/llm.py (LiteLLM gateway)  │
        │  11 routers │     │  OpenRouter free → fallback chain │
        └──────┬──────┘     └──────────────────────────────────┘
               │                       │ JSON / HTML / Markdown
               ▼                       ▼
   ┌─────────────────────┐   ┌─────────────────────┐
   │ SQLite (SQLModel)   │   │ Static files served  │
   │ clips, labs, notes… │   │ /clips /labs /ui…    │
   └─────────────────────┘   └─────────────────────┘
```

Every generation is **guardrailed** (off-topic / harmful prompts rejected), **persisted** (re-open any past generation), and **demoable** from the built-in test UI — no mobile app required to judge it.

---

## ✨ What it generates (feature tour)

| | Feature | Endpoint | Output | Free-key status |
|---|---|---|---|---|
| 🎬 | **Motion Video** | `POST /api/video` | GSAP-animated SVG explainer HTML + iframe embed | ✅ works |
| 🧪 | **Virtual Lab** | `POST /api/lab` | Interactive HTML5 science simulation | ✅ works |
| 🗺️ | **Mind Map** | `POST /api/mindmap` | Interactive Markmap HTML | ✅ works |
| 📝 | **Smart Notes** | `POST /api/notes` | Structured Markdown (images unlock with image key) | ✅ text works |
| 🎙️ | **Podcast** | `POST /api/podcast` | 3-turn Male/Female dialogue script → MP3 | ✅ script works · 🔊 MP3 needs Replicate |
| 🦸 | **Comic Strip** | `POST /api/comic` | 2-panel story script → PNG images | ✅ script works · 🖼️ PNGs need image model |
| 💬 | **Chat Tutor** | `POST /api/chat` | Multi-turn Socratic tutor scoped to the topic | ✅ works |
| 🛡️ | **Guardrail** | `POST /api/guardrail/check` | `{ allowed, reason }` content filter | ✅ works |
| 🎓 | **Viva Examiner** | `POST /api/viva/start` | Live oral exam (server mic) | 🔑 needs Gemini Live + mic |
| 🖥️ | **Screen Assistant** | `POST /api/screen/start` | Live tutor watching screen/camera | 🔑 needs Gemini Live + mic |
| 🔌 | **Device Relay** | `WS /api/client/ws` | Flutter/device mic+camera → Gemini Live relay | 🔑 needs Gemini key |

> ✅ = verified working on the free OpenRouter key · 🔑 = needs a paid/extra key (returns a clear `502` explaining exactly what's missing).

---

## 💰 Business Model

| Tier | Price logic | What's included |
|------|-------------|-----------------|
| **Free** | $0 — acquisition | Text/HTML/JSON generations on free models (video, lab, mindmap, notes text, scripts, tutor). Rate-limited. |
| **Pro (students)** | Subscription | Unlimited generations + podcast MP3s + comic/note images + history sync + offline packs. |
| **Schools / Institutions** | Per-seat SaaS | Teacher dashboard, class analytics, curriculum packs, proctored viva, admin controls. |
| **API / OEM** | Usage-based | The same REST + WebSocket API sold to Flutter/FlutterFlow apps (`/api/*`, `/api/client/ws`). |
| **Live-teacher minutes** | Pay-per-session | Human tutor escalation and scheduled live classes (see Future). Highest margin. |

Why it wins: **marginal cost per topic ≈ $0** on free models; paid features (audio, images, live minutes) map 1:1 to revenue tiers.

---

## 🚀 Future: Real Live Teacher Support

The backend is already shaped for humans-in-the-loop:

1. **AI → human escalation.** When the tutor detects 3 failed explanations (or the student taps "I need a teacher"), the session — topic, history, guardrail log — is packaged into a help ticket a teacher can pick up live.
2. **Scheduled live classes.** The existing `WS /api/client/ws` relay already streams device mic/camera to an AI; the same socket multiplexes a teacher's audio/video alongside the AI co-pilot.
3. **Teacher dashboard.** `history.html` + SQLite rows become per-student analytics: topics attempted, viva scores, weak areas, time-on-task.
4. **Proctored viva mode.** Lock the lab/video tabs, record the oral exam via the viva service, auto-score with the AI examiner, let the teacher override.
5. **Marketplace.** Teachers publish topic packs (video + lab + notes bundles); revenue share on every Pro unlock.

---

## 🔑 API keys (pick one — both supported)

| Key | Get it at | Unlocks |
|-----|-----------|---------|
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys (free models, no card) | Everything text/HTML/JSON: video, lab, mindmap, notes text, podcast + comic scripts, tutor chat |
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey | Same via Google direct: set `LLM_MODEL=gemini/gemini-2.0-flash`. Also powers image generation (`IMAGE_MODEL`), podcast voice is separate |
| `REPLICATE_API_TOKEN` | https://replicate.com/account/api-tokens | Podcast MP3 audio (MiniMax TTS) |

> The app auto-detects the provider from `LLM_MODEL`: `openrouter/...` uses the OpenRouter key, `gemini/...` uses the Gemini key, with automatic fallback to `LLM_FALLBACK`. Image models (`generate_panel_image`) and live mic sessions (`viva`/`screen`) use the Gemini key path.

## ⚡ Quickstart (60 seconds)

**Prerequisites:** Python 3.13+ · an [OpenRouter key](https://openrouter.ai/keys) (free models, no card).

```powershell
# 1. Configure
copy .env.example .env
# → put your key in .env: OPENROUTER_API_KEY=sk-or-v1-...
#   (or GEMINI_API_KEY=... with LLM_MODEL=gemini/gemini-2.0-flash — see .env.example)

# 2. Lean install (fast: skips mic/camera system deps)
uv venv .venv-fast --python 3.13
uv pip install --python .\.venv-fast\Scripts\python.exe `
  fastapi uvicorn litellm sqlmodel pydantic-settings `
  python-dotenv replicate google-genai pillow mutagen

# 3. Run
.\.venv-fast\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000

# 4. Open
# UI:      http://127.0.0.1:8000/ui/
# Docs:    http://127.0.0.1:8000/docs
# Health:  http://127.0.0.1:8000/health
```

> Full install (viva/screen server-mic) needs PortAudio + compiler for `pyaudio`/`opencv` — see `SETUP.md`. The lean path above runs everything a judge needs.

---

## 🔌 API cheat sheet

```
POST /api/guardrail/check   { "prompt": "..." }              → { allowed, reason }
POST /api/chat              { "topic", "messages": [...] }   → { reply, topic }
POST /api/video             { "topic", "duration": 12 }      → { embed_url, iframe, ... }
POST /api/mindmap           { "topic": "..." }               → { html_url, ... }
POST /api/lab               { "topic": "..." }               → { html_url, ... }
POST /api/notes             { "topic", "summaries?": "..." } → { notes_markdown, images_status, ... }
POST /api/podcast           { "topic": "..." }               → { audio_url, ... }   (MP3 needs Replicate)
POST /api/comic             { "topic": "..." }               → { image_urls, panels } (PNGs need image model)
GET  /api/viva/status       → { running, last_text, topic }
POST /api/viva/start        { "topic?": "..." }
POST /api/viva/stop
GET  /api/screen/status     → { running, mode, last_text }
POST /api/screen/start?mode=screen|display|camera
WS   /api/client/ws?mode=camera|screen|viva&topic=...
```

---

## 🧠 How it works (tech)

- **LLM gateway** (`utils/llm.py`): LiteLLM with provider-aware routing — `openrouter/*` models use `OPENROUTER_API_KEY`, `gemini/*` uses `GEMINI_API_KEY`. Automatic fallback model, strict-JSON retry, prose-tolerant JSON parsing for free models.
- **Default brain:** `openrouter/google/gemma-4-31b-it:free` (262k context, structured output) → fallback `openrouter/nvidia/nemotron-3-super-120b-a12b:free`.
- **Prompts** (`prompts/*.txt`): versioned templates for every format — motion graphics, podcast, mindmap, comic script, notes, virtual lab, guardrails, chat.
- **Storage:** SQLModel + SQLite (`app.db`, auto-created) + UUID-keyed static folders (`clips/`, `labs/`, `mindmaps/`, `comics/`, `notes/`, `podcasts/`).
- **Errors that respect you:** LLM failures surface as `400` (bad content) or `502` with the exact missing key — the UI never sees a mystery 500.
- **Frontend** (`frontend/`): zero-build test UI — topic → resources → result/history/live pages.

---

## 🗂️ Project structure

```
TesLearn/
├── main.py            # FastAPI app: routers + static mounts + /health
├── config.py          # Settings (OpenRouter/Gemini/Replicate) + storage dirs
├── run.py             # Quick-start + env checker  (python run.py --check)
├── routes/            # chat, video, podcast, mindmap, comic, notes, lab,
│                      # viva, screen, client (WS relay), guardrail
├── utils/             # llm (gateway), tts, db, comic, notes, markmap,
│                      # storage, viva, screen, client_live
├── prompts/           # all LLM templates (*.txt)
├── frontend/          # test UI (index → resources → result/history/live)
├── scripts/           # per-endpoint HTTP test scripts
├── SETUP.md           # deep dev documentation
└── .env.example       # copy to .env and fill keys
```

---

## 🗺️ Roadmap

- [x] Guardrail + chat + video + mindmap + lab + notes-text on free models
- [x] Podcast/comic script generation on free models
- [x] Clean 502 degradation for audio/image/live features
- [ ] Podcast MP3 without Replicate (pluggable TTS)
- [ ] Comic/notes images on affordable image endpoint
- [ ] Teacher-escalation tickets + live-class multiplexing
- [ ] Proctored viva + scoring dashboard
- [ ] Mobile (Flutter) client on `/api/*` + `/api/client/ws`

---

<div align="center">

**TesLearn — don't just learn. *Experience.***

Built with FastAPI · LiteLLM · OpenRouter · SQLite — deploys anywhere Python runs.

</div>
