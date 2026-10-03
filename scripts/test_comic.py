import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _http import TOPIC, call

if __name__ == "__main__":
    created = call("POST", "/api/comic", {"topic": TOPIC}, timeout=300)
    call("GET", "/api/comic", timeout=20)
    if created and created.get("id"):
        call("GET", f"/api/comic/{created['id']}", timeout=20)
