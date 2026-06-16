"""
RLM Plugin for Hermes — Recursive Language Model.

Provides rlm_complete: recursive task solving where the model
reads files, explores sub-questions, and cross-references on its own.

Cross-platform: Linux, macOS, Windows.
"""

import json
import os
import subprocess
import sys


def _find_rlm_python() -> str | None:
    """Find RLM venv Python across platforms."""
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    candidates = [
        os.path.join(hermes_home, "rlm", ".venv", "bin", "python"),       # Linux/macOS
        os.path.join(hermes_home, "rlm", ".venv", "bin", "python3"),      # Linux/macOS alt
        os.path.join(hermes_home, "rlm", ".venv", "Scripts", "python.exe"), # Windows
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _call_rlm(
    prompt: str,
    root_prompt: str | None = None,
    model: str | None = None,
    max_iterations: int = 10,
    timeout: int = 300,
) -> dict:
    """Call RLM completion via subprocess. Prompt passed via stdin (safe from injection)."""
    rlm_python = _find_rlm_python()
    if not rlm_python:
        return {"success": False, "error": "RLM venv not found. Run install.py first."}

    base_url = os.environ.get("RLM_OPENAI_BASE_URL", "")
    api_key = os.environ.get("RLM_OPENAI_API_KEY", "")
    if not base_url or not api_key:
        return {"success": False, "error": "RLM_OPENAI_BASE_URL and RLM_OPENAI_API_KEY must be set in ~/.hermes/.env"}

    # Use model from env if not specified
    if not model:
        model = os.environ.get("RLM_MODEL", "gpt-4o")

    # Build payload as JSON — safe from injection
    payload = {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "max_iterations": max_iterations,
        "timeout": timeout,
        "prompt": prompt,
        "root_prompt": root_prompt or "",
    }

    # Script that reads JSON from stdin, runs RLM, prints JSON result
    script = r'''
import json, sys, os
sys.path.insert(0, os.path.expanduser("~/.hermes/rlm/repo"))
from rlm import RLM

data = json.load(sys.stdin)

rlm = RLM(
    backend="openai",
    backend_kwargs={
        "base_url": data["base_url"],
        "api_key": data["api_key"],
        "model_name": data["model"],
    },
    max_iterations=data["max_iterations"],
    max_timeout=data["timeout"],
    verbose=False,
)

result = rlm.completion(
    prompt=data["prompt"],
    root_prompt=data["root_prompt"] if data["root_prompt"] else None,
)
answer = result.response if hasattr(result, "response") else str(result)
print(json.dumps({"answer": answer}, ensure_ascii=False))
'''

    try:
        proc = subprocess.run(
            [rlm_python, "-c", script],
            input=json.dumps(payload),
            capture_output=True, text=True,
            timeout=timeout + 60,  # extra buffer for RLM overhead
            env={**os.environ, "PYTHONPATH": os.path.expanduser("~/.hermes/rlm/repo")},
        )
        if proc.returncode != 0:
            return {"success": False, "error": proc.stderr.strip() or "RLM failed"}
        return {"success": True, "result": json.loads(proc.stdout.strip())}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"RLM timed out after {timeout}s. Try reducing max_iterations or increasing timeout."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def register(ctx):
    ctx.register_tool(
        name="rlm_complete",
        toolset="rlm",
        schema={
            "name": "rlm_complete",
            "description": "Solve a complex task using Recursive Language Model. Unlike RAG (which returns top-K chunks), RLM recursively explores the problem: reads files, spawns sub-questions, cross-references, and synthesizes a complete answer. Use for: analyzing large documents, comparing multiple files, complex research questions, legal/contract analysis, or any task where missing one piece would change the answer. The prompt should describe the task and mention any file paths to read.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Full task description. Include file paths to read, questions to answer, comparison dimensions. E.g. 'Read /path/to/contract.pdf and extract all liability clauses. Compare them with standard Russian civil code requirements.'"
                    },
                    "root_prompt": {
                        "type": "string",
                        "description": "Optional short question that the root LM sees directly. E.g. 'What are the key liability differences?'"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model for RLM. Default: from RLM_MODEL env var, or gpt-4o."
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Max recursive iterations. Higher = deeper analysis but slower. Default 10.",
                        "default": 10
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max seconds. Default 300 (5 min). Increase for very complex tasks.",
                        "default": 300
                    }
                },
                "required": ["prompt"]
            },
        },
        handler=lambda params, **kw: json.dumps(_call_rlm(
            prompt=params.get("prompt"),
            root_prompt=params.get("root_prompt"),
            model=params.get("model"),
            max_iterations=params.get("max_iterations", 10),
            timeout=params.get("timeout", 300),
        )),
        description="Recursive task solving — reads files, spawns sub-questions, cross-references. For complex analysis where completeness matters.",
    )
