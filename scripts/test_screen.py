import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _http import call

if __name__ == "__main__":
    call("POST", "/api/screen/start?mode=screen", timeout=30)
    call("POST", "/api/screen/stop", timeout=30)
