import html
import uuid
from pathlib import Path

from config import MINDMAPS_DIR

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <style>
    html, body {{ margin: 0; height: 100%; background: #0f141f; }}
    .markmap {{
      width: 100%;
      height: 100vh;
      --markmap-text-color: #ffffff;
      --markmap-code-bg: #1c2433;
      --markmap-code-color: #ffffff;
    }}
    .markmap > svg {{ width: 100%; height: 100%; }}
    .markmap-foreign, .markmap-foreign * {{ color: #ffffff !important; }}
    .markmap text {{ fill: #ffffff; }}
  </style>
</head>
<body>
  <div class="markmap">
    <script type="text/template">
{markdown}
    </script>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.18.12"></script>
</body>
</html>
"""


def compile_markmap_html(markdown: str, title: str = "Mindmap") -> str:
    safe = markdown.replace("</script>", "<\\/script>")
    return TEMPLATE.format(title=html.escape(title), markdown=safe)


def save_mindmap(html_doc: str) -> tuple[str, Path]:
    mindmap_id = uuid.uuid4().hex[:12]
    path = MINDMAPS_DIR / f"{mindmap_id}.html"
    path.write_text(html_doc, encoding="utf-8")
    return mindmap_id, path
