from config import PROMPTS_DIR, ROOT


def load_prompt(name: str, **kwargs) -> str:
    text = (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")
    for key, value in kwargs.items():
        text = text.replace("{" + key + "}", str(value))
    return text


def build_prompt(topic: str, duration: int = 12) -> str:
    example_path = PROMPTS_DIR / "motion_example.html"
    example = (
        example_path.read_text(encoding="utf-8")
        if example_path.exists()
        else "(Follow the hard requirements above. Use GSAP + SVG + the dark board theme.)"
    )
    return load_prompt(
        "motion_graphics",
        topic=topic,
        duration=duration,
        example=example,
    )


def build_podcast_prompt(topic: str) -> str:
    return load_prompt("podcast", topic=topic)


def build_mindmap_prompt(topic: str) -> str:
    return load_prompt("mindmap", topic=topic)


def build_comic_script_prompt(topic: str) -> str:
    return load_prompt("comic_script", topic=topic)


def build_comic_image_prompt_maker(script_json: str) -> str:
    return load_prompt("comic_image_prompts", script_json=script_json)


def build_notes_prompt(topic: str, summaries: str) -> str:
    return load_prompt(
        "notes",
        topic=topic,
        summaries=summaries
        or "(none provided — use only clear, basic facts implied by the topic title)",
    )


def build_notes_handwritten_prompt(topic: str) -> str:
    return load_prompt("notes_handwritten", topic=topic)


def build_notes_diagram_prompt(topic: str) -> str:
    return load_prompt("notes_diagram", topic=topic)


def build_virtual_lab_prompt(topic: str) -> str:
    example = (ROOT / "virtual_lab.html").read_text(encoding="utf-8")
    return load_prompt("virtual_lab", topic=topic, example=example)


def build_guardrail_prompt(prompt: str) -> str:
    return load_prompt("guardrail", prompt=prompt)


def build_chat_guardrail_prompt(message: str) -> str:
    return load_prompt("chat_guardrail", prompt=message)


def build_chat_system_prompt(topic: str) -> str:
    return load_prompt("chat", topic=topic)
