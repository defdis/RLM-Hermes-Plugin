#!/usr/bin/env python3
"""
OpenAI → Ollama API proxy.
Translates /v1/chat/completions → /api/chat and /v1/models → /api/tags.

Usage:
  python3 proxy.py [--port PORT] [--ollama-url URL]

  Defaults: port=11435, ollama-url=http://localhost:11434

Zero dependencies — stdlib only. Works on any Python 3.9+.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple, Dict, Any


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


class ProxyHandler(BaseHTTPRequestHandler):
    """Translate OpenAI-format requests to Ollama native API."""

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _forward(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
        """Forward a request to Ollama and return (status, json_body)."""
        url = f"{OLLAMA_URL}{path}"
        req = urllib.request.Request(url, method="POST" if payload else "GET")
        req.add_header("Content-Type", "application/json")
        # Pass through Authorization header if present (for Ollama Cloud auth)
        auth = self.headers.get("Authorization", "")
        if auth:
            req.add_header("Authorization", auth)
        data = json.dumps(payload).encode() if payload else None
        try:
            with urllib.request.urlopen(req, data=data, timeout=300) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())
        except Exception as e:
            return 502, {"error": str(e)}

    def do_GET(self):
        if self.path == "/v1/models":
            status, data = self._forward("/api/tags")
            # Ollama /api/tags → OpenAI /v1/models format
            models = []
            for m in data.get("models", []):
                models.append({
                    "id": m.get("name", m.get("model", "unknown")),
                    "object": "model",
                    "owned_by": "ollama",
                })
            self._send_json({"object": "list", "data": models}, status)
        elif self.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        if self.path == "/v1/chat/completions":
            # Translate OpenAI → Ollama chat format
            ollama_payload = {
                "model": body.get("model", ""),
                "messages": body.get("messages", []),
                "stream": False,
            }
            # Pass through optional params
            for key in ("temperature", "top_p", "max_tokens", "stop"):
                if key in body:
                    ollama_payload["options"] = ollama_payload.get("options", {})
                    ollama_payload["options"][key] = body[key]

            status, ollama_resp = self._forward("/api/chat", ollama_payload)

            if status == 200:
                # Translate Ollama response → OpenAI format
                msg = ollama_resp.get("message", {})
                openai_resp = {
                    "id": "chatcmpl-ollama-proxy",
                    "object": "chat.completion",
                    "created": 0,
                    "model": body.get("model", ""),
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": msg.get("role", "assistant"),
                            "content": msg.get("content", ""),
                        },
                        "finish_reason": "stop",
                    }],
                    "usage": {
                        "prompt_tokens": ollama_resp.get("prompt_eval_count", 0),
                        "completion_tokens": ollama_resp.get("eval_count", 0),
                        "total_tokens": (
                            ollama_resp.get("prompt_eval_count", 0)
                            + ollama_resp.get("eval_count", 0)
                        ),
                    },
                }
                self._send_json(openai_resp, 200)
            else:
                self._send_json(ollama_resp, status)
        else:
            self._send_json({"error": f"unknown endpoint: {self.path}"}, 404)

    def log_message(self, format, *args):
        """Quiet logging — only to stderr."""
        print(f"[proxy] {args[0]}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="OpenAI → Ollama API proxy")
    parser.add_argument("--port", type=int, default=11435, help="Proxy port (default: 11435)")
    parser.add_argument("--ollama-url", default=OLLAMA_URL, help="Ollama base URL")
    args = parser.parse_args()

    global OLLAMA_URL
    OLLAMA_URL = args.ollama_url.rstrip("/")

    server = HTTPServer(("127.0.0.1", args.port), ProxyHandler)
    print(f"[proxy] Listening on http://127.0.0.1:{args.port}")
    print(f"[proxy] Forwarding to {OLLAMA_URL}")
    print(f"[proxy] Use RLM_OPENAI_BASE_URL=http://127.0.0.1:{args.port}/v1", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[proxy] Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
