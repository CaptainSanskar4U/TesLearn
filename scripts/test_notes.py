import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _http import TOPIC, call

if __name__ == "__main__":
    created = call(
        "POST",
        "/api/notes",
        {"topic": TOPIC, "summaries": "Plants make glucose from light, water, and CO2. Oxygen is released."},
        timeout=180,
    )
    call("GET", "/api/notes", timeout=20)
    if created and created.get("id"):
        call("GET", f"/api/notes/{created['id']}", timeout=20)
