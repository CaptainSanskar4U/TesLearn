import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _http import call

if __name__ == "__main__":
    call("POST", "/api/viva/start", timeout=30)
    call("POST", "/api/viva/stop", timeout=30)
