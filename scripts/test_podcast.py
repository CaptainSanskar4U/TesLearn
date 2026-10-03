import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _http import TOPIC, call

if __name__ == "__main__":
    created = call("POST", "/api/podcast", {"topic": TOPIC}, timeout=240)
    call("GET", "/api/podcast", timeout=20)
    if created and created.get("id"):
        call("GET", f"/api/podcast/{created['id']}", timeout=20)
