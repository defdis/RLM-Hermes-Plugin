# 🧠 RLM Plugin for Hermes Agent

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Hermes](https://img.shields.io/badge/Hermes-Agent-orange)](https://hermes-agent.nousresearch.com)
[![skills.sh](https://img.shields.io/badge/skills.sh-listed-6366f1)](https://www.skills.sh)

**Recursive Language Model** — deep recursive analysis instead of shallow RAG search. Works as a Hermes plugin AND an Agent Skill (skills.sh compatible).

---

## TL;DR

- **RLM vs RAG:** модель сама решает что читать, а не получает готовые куски от векторной БД
- **Любой OpenAI-совместимый API:** OpenAI, OpenRouter, Ollama, vLLM — что угодно
- **Кроссплатформенно:** Linux, macOS, Windows — один скрипт `python3 install.py`
- **Хранится в `~/.hermes/rlm/`:** постоянно, не чистится системой, переживает ребуты
- **Инструмент `rlm_complete`:** агент вызывает когда нужен глубокий анализ
- **Для:** больших документов, сравнения файлов, задач где нельзя ошибиться
- **Не для:** коротких файлов, простых фактов, механических задач
- **Валидация API при установке:** проверяет что endpoint отвечает до записи в .env
- **Фиксированная версия RLM:** pinned commit, не сломается от обновлений upstream
- **Тесты:** `python3 test.py` — проверяет всё после установки

---

## What it does

| | RAG | RLM |
|---|---|---|
| **Who searches** | Vector DB (dumb) | The model itself (smart) |
| **How** | Embedding similarity | Document structure |
| **Completeness** | Top-K chunks — can miss critical info | Can read **everything** |
| **Complex tasks** | Fails on comparison, cross-analysis | Handles naturally |

RLM works like a human researcher: open document → scan structure → find relevant sections → compare → synthesize. The model decides what to read, in what order, where to go back, what to cross-check.

```
┌─────────────────────────────────────────────────┐
│                    RLM FLOW                      │
│                                                  │
│  User: "Compare liability clauses in 3 contracts"│
│                                                  │
│  RLM:                                           │
│    ├─ Read contract A → find "Responsibility"   │
│    ├─ Read contract B → find "Liability"         │
│    ├─ Read contract C → find "Penalties"         │
│    ├─ Cross-reference all three                  │
│    └─ Synthesize: "A has X, B has Y, C has Z"   │
│                                                  │
│  RAG would:                                      │
│    └─ Search "liability" → return chunks → miss  │
│       "penalties" section entirely               │
└─────────────────────────────────────────────────┘
```

**Use for:**
- Analyzing large documents (500+ lines)
- Comparing multiple files/contracts/specs
- Tasks where "missing one piece = disaster"
- Deep research with cross-references

**Don't use for:**
- Short files (<200 lines) — regular `read_file` is faster
- Simple facts — `web_search` is faster
- Mechanical tasks (git, deploy) — `terminal` is faster

---

## Quick Install

**Linux / macOS / Windows — one command:**

```bash
python3 install.py
```

Or directly from GitHub:

```bash
# Linux / macOS
curl -O https://raw.githubusercontent.com/defdis/rlm-hermes-plugin/main/install.py
python3 install.py

# Windows (PowerShell)
Invoke-WebRequest -Uri https://raw.githubusercontent.com/defdis/rlm-hermes-plugin/main/install.py -OutFile install.py
python install.py
```

The installer will:
1. Check Python 3.11+, git, and Hermes
2. Ask for your API credentials (any OpenAI-compatible endpoint)
3. **Validate the API** — checks endpoint responds before saving
4. Clone and install the RLM library (**pinned commit** — won't break on upstream updates)
5. Create the Hermes plugin
6. Restart Hermes

**Cross-platform:** works on Linux, macOS, and Windows. No bash required.

---

## Verify

After install, run the smoke test:

```bash
python3 test.py
```

Or ask your agent: **"Compare RAG and RLM in 3 bullet points."**

If it responds meaningfully — it works.

---

## Requirements

- **Hermes Agent** (any version with plugin support)
- **Python 3.11+**
- **git**
- **Any OpenAI-compatible API** — OpenAI, OpenRouter, Ollama, vLLM, local models, etc.
- API key with sufficient token budget (RLM makes multiple iterations)

---

## Supported API Providers

| Provider | Base URL | Notes |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | Native |
| OpenRouter | `https://openrouter.ai/api/v1` | Native |
| vLLM | `http://your-server:8000/v1` | Native |
| **Ollama** (local/cloud) | `http://localhost:11434` | Via built-in proxy |
| Any OpenAI-compatible | your endpoint | Native |

### Ollama via Built-in Proxy

RLM doesn't support Ollama natively (Ollama uses `/api/chat`, not `/v1/chat/completions`). The plugin includes `proxy.py` — a zero-dependency OpenAI→Ollama translator that starts automatically.

**Setup:**

```bash
# In ~/.hermes/.env:
RLM_BACKEND=ollama
RLM_OLLAMA_URL=http://localhost:11434          # or your Ollama Cloud URL
RLM_MODEL=qwen3.5:122b                          # any model in ollama list
# No API key needed
```

The proxy starts on first `rlm_complete` call (port 11435, localhost). No manual steps.

**Manual proxy (optional):**
```bash
python3 proxy.py --port 11435 --ollama-url http://your-ollama:11434
# Then set RLM_OPENAI_BASE_URL=http://127.0.0.1:11435/v1
```

---

## Manual Install

### 1. Install RLM library (pinned commit)

```bash
# Linux / macOS
mkdir -p ~/.hermes/rlm
git clone https://github.com/alexzhang13/rlm.git ~/.hermes/rlm/repo
git -C ~/.hermes/rlm/repo checkout 156fd725411b9cae822f5920a6cbf102a5473baa
python3.12 -m venv ~/.hermes/rlm/.venv
~/.hermes/rlm/.venv/bin/pip install -e ~/.hermes/rlm/repo

# Windows
mkdir %USERPROFILE%\.hermes\rlm
git clone https://github.com/alexzhang13/rlm.git %USERPROFILE%\.hermes\rlm\repo
git -C %USERPROFILE%\.hermes\rlm\repo checkout 156fd725411b9cae822f5920a6cbf102a5473baa
python -m venv %USERPROFILE%\.hermes\rlm\.venv
%USERPROFILE%\.hermes\rlm\.venv\Scripts\pip install -e %USERPROFILE%\.hermes\rlm\repo
```

### 2. Configure environment

Add to `~/.hermes/.env`:

```bash
RLM_OPENAI_BASE_URL=https://your-api-endpoint/v1
RLM_OPENAI_API_KEY=your_api_key_here
RLM_MODEL=gpt-4o
```

### 3. Create plugin

```bash
mkdir -p ~/.hermes/plugins/rlm
cp __init__.py ~/.hermes/plugins/rlm/__init__.py
cp plugin.yaml ~/.hermes/plugins/rlm/plugin.yaml
```

### 4. Restart Hermes

Restart your Hermes agent so it loads the new plugin:

- **If Hermes runs as a service:** `systemctl --user restart hermes-gateway-*.service`
- **If Hermes runs in terminal:** stop it (Ctrl+C) and start again
- **Or from within Hermes chat:** send `/restart` command

---

## How it works

The plugin registers a `rlm_complete` tool in Hermes. When called:

1. Hermes agent passes the task to RLM
2. RLM spawns a Python REPL environment
3. The model recursively explores: reads, asks sub-questions, cross-references
4. Returns a synthesized answer

**Security:** prompt is passed via stdin as JSON — safe from injection. No string escaping into Python code.

---

## Agent Skill (skills.sh)

This repo is also an **Agent Skill** — compatible with [skills.sh](https://www.skills.sh) and any agent that follows the [Agent Skills spec](https://agentskills.io/specification) (Claude Code, Cursor, Codex, GitHub Copilot, Windsurf, Gemini, and others).

The skill lives at `skills/rlm-deep-analysis/SKILL.md` — the standard layout for skills.sh compatibility.

**Install as a skill:**

```bash
npx skills add defdis/rlm-hermes-plugin
```

The skill appears automatically on the [skills.sh leaderboard](https://www.skills.sh) through anonymous installation telemetry.

---

## Notes

- RLM in local mode cannot read files directly — pass content in the prompt
- Each iteration consumes tokens — use regular tools for simple tasks
- `model_name` in `backend_kwargs` is required
- `result.response` (not `.answer`) contains the final answer
- Works with any OpenAI-compatible endpoint
- **Pinned RLM commit:** `156fd72` — won't break on upstream API changes
- **API validated at install time** — catches bad credentials before they hit .env
- **Timeout default 300s** (5 min) — increase for very complex tasks

---

## Uninstall

```bash
# Linux / macOS
rm -rf ~/.hermes/plugins/rlm/ ~/.hermes/rlm/

# Windows
rmdir /s %USERPROFILE%\.hermes\plugins\rlm
rmdir /s %USERPROFILE%\.hermes\rlm

# Remove RLM_* lines from ~/.hermes/.env
# Restart Hermes: systemctl --user restart hermes-gateway-*.service, or /restart in chat
```

---

## Credits

- **RLM library:** [alexzhang13/rlm](https://github.com/alexzhang13/rlm) — Alex Zhang, Tim Kraska, Omar Khattab (MIT)
- **Hermes Agent:** [Nous Research](https://hermes-agent.nousresearch.com)
- **Plugin author:** [defdis](https://github.com/defdis)
