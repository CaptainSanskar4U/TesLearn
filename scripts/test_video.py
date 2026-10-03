import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _http import TOPIC, call

if __name__ == "__main__":
    created = call("POST", "/api/video", {"topic": TOPIC, "duration": 12}, timeout=180)
    call("GET", "/api/video", timeout=20)
    if created and created.get("id"):
        call("GET", f"/api/video/{created['id']}", timeout=20)
