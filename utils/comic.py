import json
import uuid

from config import COMICS_DIR, settings
from utils.llm import generate_comic_script, generate_panel_image, make_comic_image_prompts


def build_comic(topic: str) -> tuple[str, dict]:
    script = generate_comic_script(topic)
    prompt_pack = make_comic_image_prompts(script)

    comic_id = uuid.uuid4().hex[:12]
    folder = COMICS_DIR / comic_id
    folder.mkdir(parents=True, exist_ok=True)

    image_urls: list[str] = []
    panels_meta = []
    for panel in prompt_pack["panels"]:
        filename = f"p{panel['page']}_{panel['panel']}.png"
        dest = folder / filename
        generate_panel_image(panel["image_prompt"], dest)
        url = f"{settings.base_url}/comics/{comic_id}/{filename}"
        image_urls.append(url)
        panels_meta.append({**panel, "filename": filename, "url": url})

    title = script.get("title") or topic
    meta = {
        "title": title,
        "script": script,
        "prompt_pack": prompt_pack,
        "panels": panels_meta,
        "image_urls": image_urls,
    }
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return comic_id, meta
