import base64
import json
import os
import re
import urllib.request
from pathlib import Path

from litellm import completion, image_generation

from config import settings
from prompts import (
    build_chat_guardrail_prompt,
    build_chat_system_prompt,
    build_comic_image_prompt_maker,
    build_comic_script_prompt,
    build_guardrail_prompt,
    build_mindmap_prompt,
    build_notes_prompt,
    build_podcast_prompt,
    build_prompt,
    build_virtual_lab_prompt,
)


def _is_openrouter(model: str) -> bool:
    return model.strip().startswith("openrouter/")


def _api_key_for(model: str) -> str | None:
    """Return the right key for the model provider (OpenRouter first, then Gemini)."""
    if _is_openrouter(model):
        key = (
            settings.openrouter_api_key
            or os.getenv("OPENROUTER_API_KEY")
            or ""
        ).strip().strip('"').strip("'")
        if key:
            os.environ["OPENROUTER_API_KEY"] = key
            return key
        return None
    return _api_key()


def _api_key() -> str | None:
    key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        os.environ["GEMINI_API_KEY"] = key
        os.environ["GOOGLE_API_KEY"] = key
    return key or None


def _studio_model(name: str) -> str:
    """Force Google AI Studio (API key), never Vertex ADC. Pass openrouter/ through."""
    name = (name or "").strip()
    if name.startswith(("openrouter/", "gemini/", "openai/", "anthropic/", "replicate/")):
        return name
    # Default to OpenRouter free model when no Gemini key is configured
    if not (settings.gemini_api_key or os.getenv("GEMINI_API_KEY")):
        return name if name else "openrouter/google/gemma-4-31b-it:free"
    return f"gemini/{name}"


def _candidate_models() -> list[str]:
    primary = _studio_model(settings.llm_model)
    cands = [primary]
    fb = (_studio_model(getattr(settings, "llm_fallback", "") or "") or "").strip()
    if fb and fb not in cands:
        cands.append(fb)
    return cands


def _strip_fences(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:html|json|markdown|md)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json(text: str) -> dict | list:
    """Parse JSON even when the model adds prose/fences around it."""
    clean = _strip_fences(text or "")
    try:
        return json.loads(clean)
    except (json.JSONDecodeError, ValueError):
        pass
    start_candidates = [i for i in (clean.find("{"), clean.find("[")) if i >= 0]
    end_candidates = [i for i in (clean.rfind("}"), clean.rfind("]")) if i >= 0]
    if start_candidates and end_candidates:
        snippet = clean[min(start_candidates): max(end_candidates) + 1]
        return json.loads(snippet)
    raise ValueError("model did not return valid JSON")


def _do_completion(model: str, messages: list[dict], temperature: float, json_mode: bool):
    key = _api_key_for(model)
    if _is_openrouter(model) and not key:
        raise ValueError("OPENROUTER_API_KEY is not set — add it to .env")
    kwargs: dict = {"model": model, "messages": messages, "temperature": temperature}
    if key:
        kwargs["api_key"] = key
    # LiteLLM infers openrouter from the model prefix; only force provider for gemini
    if not _is_openrouter(model) and "gemini" in model:
        kwargs["custom_llm_provider"] = "gemini"
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        return completion(**kwargs)
    except Exception as exc:
        # Many free models reject response_format — retry as plain JSON instruction
        if json_mode and "response_format" in str(exc).lower():
            kwargs.pop("response_format", None)
            return completion(**kwargs)
        raise


def _chat(prompt: str, temperature: float = 0.4, *, json_mode: bool = False):
    messages = [{"role": "user", "content": prompt}]
    last_err: Exception | None = None
    for model in _candidate_models():
        try:
            try:
                return _do_completion(model, messages, temperature, json_mode)
            except Exception as exc:
                if json_mode and "response_format" not in str(exc).lower():
                    # json_mode unsupported-shape error already retried inside;
                    # fall through to plain retry once per model
                    pass
                raise
        except Exception as exc:
            last_err = exc
            # try plain (non-json-mode) once if strict mode failed for other reasons
            if json_mode and "json" in str(exc).lower():
                try:
                    return _do_completion(model, messages, temperature, False)
                except Exception as exc2:
                    last_err = exc2
            continue
    raise ValueError(f"LLM request failed on all models: {last_err}")


def _chat_json(prompt: str, temperature: float = 0.4) -> dict:
    # Nudge free models to emit pure JSON (they often add prose otherwise)
    strict = prompt + "\n\nReturn ONLY valid JSON, no prose, no markdown fences."
    try:
        resp = _chat(strict, temperature=temperature, json_mode=True)
    except Exception:
        resp = _chat(strict, temperature=temperature, json_mode=False)
    content = resp.choices[0].message.content or ""
    data = _extract_json(content)
    if not isinstance(data, dict):
        # podcast route sometimes returns a bare list — wrap for uniform callers
        if isinstance(data, list):
            return {"dialogues": data}  # type: ignore[return-value]
        raise ValueError("model did not return a JSON object")
    return data


def check_prompt_guardrail(prompt: str) -> dict:
    data = _chat_json(build_guardrail_prompt(prompt), temperature=0.1)
    allowed = bool(data.get("allowed", False))
    status = "success" if allowed else "error"
    if data.get("status") in ("success", "error"):
        status = data["status"]
    return {
        "status": status,
        "allowed": allowed,
        "reason": str(data.get("reason", "No reason provided")),
    }


def check_chat_message_guardrail(message: str) -> dict:
    """Lighter guardrail for in-session chat (allows hey, thanks, follow-ups)."""
    data = _chat_json(build_chat_guardrail_prompt(message), temperature=0.1)
    allowed = bool(data.get("allowed", False))
    status = "success" if allowed else "error"
    if data.get("status") in ("success", "error"):
        status = data["status"]
    return {
        "status": status,
        "allowed": allowed,
        "reason": str(data.get("reason", "No reason provided")),
    }


def chat_reply(topic: str, messages: list[dict]) -> str:
    """Multi-turn chat with system prompt scoped to topic."""
    system = build_chat_system_prompt(topic)
    llm_messages = [{"role": "system", "content": system}]
    for msg in messages:
        role = (msg.get("role") or "user").strip().lower()
        content = (msg.get("content") or "").strip()
        if not content or role not in ("user", "assistant"):
            continue
        llm_messages.append({"role": role, "content": content})
    if not any(m["role"] == "user" for m in llm_messages):
        raise ValueError("messages must include at least one user turn")

    last_err: Exception | None = None
    for model in _candidate_models():
        try:
            kwargs: dict = {"model": model, "messages": llm_messages, "temperature": 0.45}
            key = _api_key_for(model)
            if _is_openrouter(model) and not key:
                raise ValueError("OPENROUTER_API_KEY is not set — add it to .env")
            if key:
                kwargs["api_key"] = key
            if not _is_openrouter(model) and "gemini" in model:
                kwargs["custom_llm_provider"] = "gemini"
            resp = completion(**kwargs)
            reply = (resp.choices[0].message.content or "").strip()
            if not reply:
                raise ValueError("empty chat reply from model")
            return reply
        except Exception as exc:
            last_err = exc
            continue
    raise ValueError(f"Chat generation failed on all models: {last_err}")


def generate_html(topic: str, duration: int = 12) -> str:
    resp = _chat(build_prompt(topic, duration), temperature=0.4)
    html = _strip_fences(resp.choices[0].message.content or "")
    if "<!DOCTYPE html>" not in html and "<html" not in html.lower():
        raise ValueError("LLM did not return a full HTML document")
    return html


def generate_virtual_lab_html(topic: str) -> str:
    resp = _chat(build_virtual_lab_prompt(topic), temperature=0.45)
    html = _strip_fences(resp.choices[0].message.content or "")
    if "<!DOCTYPE html>" not in html and "<html" not in html.lower():
        raise ValueError("LLM did not return a full HTML document")
    return html


def generate_podcast_script(topic: str) -> list[dict]:
    data = _chat_json(build_podcast_prompt(topic), temperature=0.5)
    dialogues = data.get("dialogues") or data
    if not isinstance(dialogues, list) or len(dialogues) != 3:
        raise ValueError("podcast script must have exactly 3 dialogues")
    for d in dialogues:
        if "speaker" not in d or "text" not in d:
            raise ValueError("each dialogue needs speaker + text")
        d["speaker"] = d["speaker"].lower().strip()
        if d["speaker"] not in ("male", "female"):
            raise ValueError("speaker must be male or female")
    return dialogues


def generate_mindmap_markdown(topic: str) -> str:
    resp = _chat(build_mindmap_prompt(topic), temperature=0.4)
    md = _strip_fences(resp.choices[0].message.content or "")
    if not md.lstrip().startswith("---"):
        md = f"---\ntitle: {topic}\nmarkmap:\n  colorFreezeLevel: 2\n---\n\n## {topic}\n\n{md}"
    return md


def generate_comic_script(topic: str) -> dict:
    data = _chat_json(build_comic_script_prompt(topic), temperature=0.55)
    pages = data.get("pages") or []
    if len(pages) != 2:
        raise ValueError("comic must have exactly 2 pages")
    for page in pages:
        panels = page.get("panels") or []
        if len(panels) != 1:
            raise ValueError("each comic page must have exactly 1 panel")
    return data


def make_comic_image_prompts(script: dict) -> dict:
    """Prompt-maker layer: turn script into final image prompts + overlays."""
    data = _chat_json(
        build_comic_image_prompt_maker(json.dumps(script, ensure_ascii=False)),
        temperature=0.3,
    )
    panels = data.get("panels") or []
    if len(panels) != 2:
        raise ValueError("prompt maker must return exactly 2 panels")
    for p in panels:
        if not p.get("image_prompt"):
            raise ValueError("each panel needs image_prompt")
    return data


def generate_notes_markdown(topic: str, summaries: str = "") -> str:
    resp = _chat(build_notes_prompt(topic, summaries), temperature=0.35)
    md = _strip_fences(resp.choices[0].message.content or "")
    if not md.lstrip().startswith("#"):
        raise ValueError("notes model did not return markdown starting with #")
    return md


def _save_data_url(data_url: str, dest: Path) -> Path:
    if "," not in data_url:
        dest.write_bytes(base64.b64decode(data_url))
        return dest
    header, b64 = data_url.split(",", 1)
    dest.write_bytes(base64.b64decode(b64))
    return dest


def generate_panel_image(prompt: str, dest: Path) -> Path:
    """Image generation needs a paid image model — free OpenRouter text models can't do it."""
    model = _studio_model(settings.image_model)
    if _is_openrouter(model) and model.endswith(":free"):
        raise ValueError(
            "IMAGE_MODEL is a free text-only model — comic/notes images need a paid image model "
            "(e.g. openrouter/google/gemini-2.5-flash-image) or a GEMINI_API_KEY"
        )
    if _is_openrouter(model):
        key = _api_key_for(model)
        if not key:
            raise ValueError("OPENROUTER_API_KEY is not set — add it to .env")
        resp = image_generation(
            model=model,
            prompt=prompt,
            size=settings.image_size,
            n=1,
            api_key=key,
            response_format="b64_json",
        )
        item = resp.data[0]
        b64 = getattr(item, "b64_json", None) or (item.get("b64_json") if isinstance(item, dict) else None)
        if b64:
            dest.write_bytes(base64.b64decode(b64))
            return dest
        url = getattr(item, "url", None) or (item.get("url") if isinstance(item, dict) else None)
        if not url:
            raise ValueError("image model returned no image data")
        with urllib.request.urlopen(url) as r:
            dest.write_bytes(r.read())
        return dest

    key = _api_key()

    if "gemini" in model:
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is not set — comic/notes images need it "
                "(text features already work via OPENROUTER_API_KEY)"
            )
        resp = completion(
            model=model,
            custom_llm_provider="gemini",
            messages=[
                {
                    "role": "user",
                    "content": f"Generate exactly one image. Follow the prompt closely.\n\n{prompt}",
                }
            ],
            modalities=["image", "text"],
            api_key=key,
        )
        msg = resp.choices[0].message
        images = getattr(msg, "images", None) or []
        if images:
            first = images[0]
            if isinstance(first, dict):
                url = first.get("image_url", {}).get("url") or first.get("url")
            else:
                url = getattr(getattr(first, "image_url", None), "url", None)
            if url:
                return _save_data_url(url, dest)

        content = msg.content or ""
        if isinstance(content, str) and "base64" in content:
            return _save_data_url(content, dest)
        raise ValueError("Gemini image model returned no image")

    resp = image_generation(
        model=model,
        prompt=prompt,
        size=settings.image_size,
        n=1,
        api_key=key,
        response_format="b64_json",
    )
    item = resp.data[0]
    b64 = getattr(item, "b64_json", None) or (item.get("b64_json") if isinstance(item, dict) else None)
    if b64:
        dest.write_bytes(base64.b64decode(b64))
        return dest

    url = getattr(item, "url", None) or (item.get("url") if isinstance(item, dict) else None)
    if not url:
        raise ValueError("image model returned no image data")
    with urllib.request.urlopen(url) as r:
        dest.write_bytes(r.read())
    return dest
