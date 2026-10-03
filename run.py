"""
run.py — TesLearn Backend Quick Start Script
============================================
Run this script to start the TesLearn backend server.

Usage:
    python run.py              # start in development mode (auto-reload)
    python run.py --prod       # start in production mode (no reload)
    python run.py --port 9000  # use a different port
    python run.py --check      # only check environment, don't start
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"

REQUIRED_VARS = {
    "OPENROUTER_API_KEY": "Get it at https://openrouter.ai/keys (free models work without Gemini)",
    "REPLICATE_API_TOKEN": "Get it at https://replicate.com/account/api-tokens (needed for podcast TTS)",
}

OPTIONAL_VARS = {
    "LLM_MODEL": "openrouter/google/gemma-4-31b-it:free",
    "LLM_FALLBACK": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    "IMAGE_MODEL": "gemini/gemini-2.5-flash-image-preview",
    "LIVE_MODEL": "models/gemini-2.0-flash-live-001",
    "TTS_MODEL": "minimax/speech-02-turbo",
    "BASE_URL": "http://127.0.0.1:8000",
}

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ████████╗███████╗███████╗██╗     ███████╗ █████╗ ██████╗  ║
║      ██╔══╝██╔════╝██╔════╝██║     ██╔════╝██╔══██╗██╔══██╗ ║
║      ██║   █████╗  ███████╗██║     █████╗  ███████║██████╔╝ ║
║      ██║   ██╔══╝  ╚════██║██║     ██╔══╝  ██╔══██║██╔══██╗ ║
║      ██║   ███████╗███████║███████╗███████╗██║  ██║██║  ██║ ║
║      ╚═╝   ╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ║
║                  AI-Powered EdTech Backend                   ║
╚══════════════════════════════════════════════════════════════╝
"""


def print_banner():
    print(BANNER)


def load_env_file() -> dict[str, str]:
    """Load variables from .env file into a dict (without setting os.environ)."""
    env_vars: dict[str, str] = {}
    if not ENV_FILE.exists():
        return env_vars
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            env_vars[key.strip()] = val.strip()
    return env_vars


def check_env() -> bool:
    """Validate that required env vars are set. Returns True if all OK."""
    print("🔍  Checking environment configuration...\n")

    # Load .env file first
    file_vars = load_env_file()
    # Merge: file_vars + actual os.environ (os.environ takes priority)
    effective = {**file_vars, **os.environ}

    all_ok = True

    if not ENV_FILE.exists():
        print(f"  ⚠️  No .env file found at {ENV_FILE}")
        print("      Create one by copying .env.example:")
        print("      copy .env.example .env\n")

    # Check required vars
    print("  Required secrets:")
    for var, help_text in REQUIRED_VARS.items():
        val = effective.get(var, "")
        if not val or val.startswith("your-") or val == "r8_xxxx...":
            print(f"  ❌  {var} — NOT SET")
            print(f"       {help_text}")
            all_ok = False
        else:
            masked = val[:8] + "..." + val[-4:] if len(val) > 16 else "***"
            print(f"  ✅  {var} = {masked}")

    # Show optional vars
    print("\n  Optional settings (showing effective values):")
    for var, default in OPTIONAL_VARS.items():
        val = effective.get(var, default)
        print(f"  ℹ️   {var} = {val}")

    print()
    return all_ok


def check_python_version():
    """Ensure Python >= 3.13."""
    if sys.version_info < (3, 13):
        print(f"  ❌  Python 3.13+ required, you have {sys.version}")
        print("      Install Python 3.13 from https://python.org/downloads/")
        sys.exit(1)
    print(f"  ✅  Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def check_dependencies():
    """Check if required packages are importable."""
    print("\n🔍  Checking dependencies...\n")
    packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("litellm", "litellm"),
        ("google.genai", "google-genai"),
        ("sqlmodel", "sqlmodel"),
        ("replicate", "replicate"),
        ("pyaudio", "pyaudio"),
        ("cv2", "opencv-python"),
        ("PIL", "pillow"),
        ("mss", "mss"),
        ("mutagen", "mutagen"),
        ("pydantic_settings", "pydantic-settings"),
    ]
    all_ok = True
    for module, package in packages:
        try:
            __import__(module)
            print(f"  ✅  {package}")
        except ImportError:
            print(f"  ❌  {package} — not installed")
            all_ok = False
    if not all_ok:
        print("\n  Run:  uv sync   or   pip install -e .")
    return all_ok


def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Start the uvicorn server."""
    print(f"\n🚀  Starting TesLearn Backend...\n")
    print(f"    Host:    {host}")
    print(f"    Port:    {port}")
    print(f"    Reload:  {'enabled' if reload else 'disabled'}")
    print(f"\n    Docs:    http://{host}:{port}/docs")
    print(f"    Health:  http://{host}:{port}/health\n")
    print("─" * 60 + "\n")

    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port)]
    if reload:
        cmd.append("--reload")

    os.chdir(ROOT)
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n\n  Server stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="TesLearn Backend — Quick Start",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--prod", action="store_true", help="Run in production mode (no auto-reload)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--check", action="store_true", help="Only check environment, don't start server")
    parser.add_argument("--skip-check", action="store_true", help="Skip environment checks and start immediately")
    args = parser.parse_args()

    print_banner()
    print(f"  Working directory: {ROOT}\n")
    check_python_version()

    if args.check:
        ok = check_env()
        check_dependencies()
        if ok:
            print("✅  Environment looks good! Run: python run.py")
        else:
            print("❌  Fix the issues above before starting the server.")
            sys.exit(1)
        return

    if not args.skip_check:
        env_ok = check_env()
        deps_ok = check_dependencies()
        if not env_ok:
            print("\n⚠️   Some required secrets are missing.")
            print("    Fill in your .env file, then run again.")
            print("    (Or run with --skip-check to start anyway)\n")
            # Don't hard-exit — server may still start for testing with defaults
        if not deps_ok:
            print("\n❌  Missing dependencies. Run: uv sync")
            sys.exit(1)

    start_server(
        host=args.host,
        port=args.port,
        reload=not args.prod,
    )


if __name__ == "__main__":
    main()
