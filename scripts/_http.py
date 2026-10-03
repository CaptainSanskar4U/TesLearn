import json
import os
import urllib.error
import urllib.request

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TOPIC = os.getenv("TEST_TOPIC", "photosynthesis")


def call(method: str, path: str, body: dict | None = None, timeout: int = 180):
    url = BASE + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    print(f"\n>>> {method} {url}")
    if body is not None:
        print("body:", json.dumps(body, indent=2))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            print("status:", resp.status)
            try:
                parsed = json.loads(raw)
                print("result:", json.dumps(parsed, indent=2, ensure_ascii=False)[:4000])
                return parsed
            except json.JSONDecodeError:
                print("result:", raw[:2000])
                return raw
    except urllib.error.HTTPError as e:
        print("status:", e.code)
        print("error:", e.read().decode()[:2000])
        return None
    except urllib.error.URLError as e:
        print("FAILED — is the server running?")
        print("  uv run uvicorn main:app --reload --port 8000")
        print("detail:", e)
        return None
