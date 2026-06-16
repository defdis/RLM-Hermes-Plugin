#!/usr/bin/env python3
"""
Quick smoke test for RLM plugin.
Run after install: python3 test.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def green(s):  return f"\033[0;32m{s}\033[0m" if os.name != "nt" else s
def red(s):    return f"\033[0;31m{s}\033[0m" if os.name != "nt" else s
def yellow(s): return f"\033[1;33m{s}\033[0m" if os.name != "nt" else s


def find_hermes_home():
    home = os.environ.get("HERMES_HOME", "")
    if home:
        return Path(home)
    if os.name == "nt":
        candidates = [
            Path(os.environ.get("USERPROFILE", "")) / ".hermes",
        ]
    else:
        candidates = [Path.home() / ".hermes"]
    for c in candidates:
        if (c / "config.yaml").exists():
            return c
    return None


def find_rlm_python(hermes_home: Path):
    candidates = [
        hermes_home / "rlm" / ".venv" / "bin" / "python",
        hermes_home / "rlm" / ".venv" / "bin" / "python3",
        hermes_home / "rlm" / ".venv" / "Scripts" / "python.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def main():
    print(yellow("RLM Plugin Smoke Test"))
    print("=" * 50)
    print()

    errors = 0

    # 1. Hermes home
    hermes_home = find_hermes_home()
    if not hermes_home:
        print(red("FAIL") + " Hermes not found")
        sys.exit(1)
    print(green("PASS") + f" Hermes home: {hermes_home}")

    # 2. Plugin exists
    plugin = hermes_home / "plugins" / "rlm" / "__init__.py"
    manifest = hermes_home / "plugins" / "rlm" / "plugin.yaml"
    if not plugin.exists():
        print(red("FAIL") + " Plugin __init__.py not installed")
        errors += 1
    else:
        print(green("PASS") + " Plugin __init__.py installed")
    if not manifest.exists():
        print(yellow("WARN") + " plugin.yaml not found (optional)")
    else:
        print(green("PASS") + " Plugin manifest installed")

    # 3. RLM venv exists
    rlm_python = find_rlm_python(hermes_home)
    if not rlm_python:
        print(red("FAIL") + " RLM venv not found")
        errors += 1
    else:
        print(green("PASS") + f" RLM venv: {rlm_python}")

    # 4. RLM import works
    if rlm_python:
        try:
            subprocess.run(
                [rlm_python, "-c", "import sys; from pathlib import Path; sys.path.insert(0, str(Path.home() / '.hermes' / 'rlm' / 'repo')); from rlm import RLM; print('OK')"],
                check=True, capture_output=True, text=True, timeout=15
            )
            print(green("PASS") + " RLM import OK")
        except Exception as e:
            print(red("FAIL") + f" RLM import: {e}")
            errors += 1

    # 5. Env vars set
    env_file = hermes_home / ".env"
    if env_file.exists():
        content = env_file.read_text()
        has_url = "RLM_OPENAI_BASE_URL" in content
        has_key = "RLM_OPENAI_API_KEY" in content
        has_model = "RLM_MODEL" in content
        if has_url and has_key:
            print(green("PASS") + " RLM env vars set")
        else:
            missing = []
            if not has_url: missing.append("RLM_OPENAI_BASE_URL")
            if not has_key: missing.append("RLM_OPENAI_API_KEY")
            if not has_model: missing.append("RLM_MODEL")
            print(yellow("WARN") + f" Missing env vars: {', '.join(missing)}")
    else:
        print(red("FAIL") + " .env file not found")
        errors += 1

    # 6. API connectivity (optional, may fail if no network)
    base_url = os.environ.get("RLM_OPENAI_BASE_URL", "")
    api_key = os.environ.get("RLM_OPENAI_API_KEY", "")
    if base_url and api_key:
        import urllib.request
        import urllib.error
        url = base_url.rstrip("/") + "/models"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {api_key}")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                count = len(data.get("data", data))
                print(green("PASS") + f" API reachable — {count} models")
        except Exception as e:
            print(yellow("WARN") + f" API check: {e}")
    else:
        print(yellow("SKIP") + " API check (no credentials in env)")

    # ─── Summary ──────────────────────────────────────────────────────────────
    print()
    print("=" * 50)
    if errors == 0:
        print(green("ALL TESTS PASSED"))
        print("RLM plugin is ready. Restart Hermes and try:")
        print('  "Compare RAG and RLM in 3 bullet points"')
    else:
        print(red(f"{errors} TEST(S) FAILED"))
        print("Run install.py first, then retry.")
    print()

    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()
