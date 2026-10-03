import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _http import call

if __name__ == "__main__":
    for prompt in ["photosynthesis", "watch Netflix all day", "hi"]:
        call("POST", "/api/guardrail/check", {"prompt": prompt}, timeout=30)
