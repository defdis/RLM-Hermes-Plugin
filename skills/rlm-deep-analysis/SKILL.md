---
name: rlm-deep-analysis
description: Recursive deep document analysis via RLM (Recursive Language Model). Use when comparing multiple files, analyzing large documents (500+ lines), cross-referencing contracts/specs, or any task where missing one piece of information would change the answer. Replaces shallow RAG search with model-driven recursive reading — the model decides what to read, in what order, and what to cross-check. NOT for short files (<200 lines), simple facts, or mechanical tasks.
license: MIT
compatibility: Requires Python 3.11+, git, OpenAI-compatible API endpoint. Works with Hermes Agent, Claude Code, Cursor, Codex, GitHub Copilot, and any agent with shell access to the rlm_complete tool.
metadata:
  author: defdis
  version: "1.0.0"
  category: agent-workflows
  tags: [rlm, deep-analysis, document-analysis, recursive, research, comparison, contracts]
---

# RLM Deep Analysis

Recursive Language Model — a tool for tasks where shallow search fails. Instead of returning top-K chunks like RAG, RLM recursively explores: reads files, spawns sub-questions, cross-references, and synthesizes a complete answer.

## When to Use

Call `rlm_complete` when:

- **Large documents** — 500+ lines where `read_file` would miss context
- **Multi-file comparison** — comparing contracts, specs, policies across 2+ files
- **Completeness-critical tasks** — legal analysis, compliance checks, security audits where missing one clause = wrong answer
- **Cross-reference research** — "find all mentions of X across these 10 files and trace dependencies"
- **Structured extraction** — "extract every liability clause from this 50-page contract and categorize by severity"

## When NOT to Use

Skip `rlm_complete` and use regular tools instead:

- **Short files** (<200 lines) — `read_file` is faster and cheaper
- **Simple facts** — "what's the capital of France?" → `web_search`
- **Mechanical tasks** — git operations, deploys, file creation → `terminal`
- **Single-file quick scan** — "does this file import pandas?" → `search_files`
- **When you already know the answer** — RLM is for discovery, not confirmation

## How to Use

### Tool: `rlm_complete`

```
rlm_complete(prompt, root_prompt?, model?, max_iterations?, timeout?)
```

### Writing a Good Prompt

The prompt is the most important part. A bad prompt wastes tokens; a good one gets precise results.

**Good prompt structure:**

1. **State the goal** — what answer do you need?
2. **List the files** — full paths, what to look for in each
3. **Specify dimensions** — what aspects to compare/extract
4. **Set expectations** — format, depth, what "complete" means

**Example — Good:**

```
Read these three contracts and compare their liability clauses:

Files:
- /home/user/contracts/vendor-a.pdf — look for "Limitation of Liability", "Indemnification"
- /home/user/contracts/vendor-b.pdf — look for "Liability", "Damages", "Cap"
- /home/user/contracts/vendor-c.pdf — look for "Responsibility", "Penalties", "Exclusions"

Compare across these dimensions:
1. Liability cap (absolute amount or multiplier)
2. Excluded damages (consequential, indirect, lost profits)
3. Indemnification scope (third-party IP, bodily injury, data breach)
4. Survival period after termination

Return a structured comparison table with exact clause references.
```

**Example — Bad (too vague):**

```
Compare the three contracts.
```

**Example — Bad (wrong tool for the job):**

```
What does git status do?
```

### Parameters

| Parameter | When to adjust | Default |
|---|---|---|
| `prompt` | Always required — the full task description | — |
| `root_prompt` | Optional short question for the root LM. Use when the task has a single core question: "Which vendor has the strongest liability protection?" | none |
| `model` | Override if the default model is too weak for complex legal/technical analysis | from `RLM_MODEL` env |
| `max_iterations` | Increase to 15-20 for very large documents (1000+ lines) or 5+ files | 10 |
| `timeout` | Increase to 600 for multi-file analysis with large documents | 300 (5 min) |

### Interpreting Results

RLM returns `{"success": true, "result": {"answer": "..."}}` or `{"success": false, "error": "..."}`.

- **Success** — the answer is a synthesized response. It may include inline references to specific sections.
- **Timeout** — increase `timeout` or reduce `max_iterations`. RLM hit the wall before finishing.
- **Error** — check that `RLM_OPENAI_BASE_URL` and `RLM_OPENAI_API_KEY` are set in `~/.hermes/.env`.

## Examples

### 1. Contract Comparison

**Task:** Find which of 3 vendor contracts has the strongest data protection.

**Prompt:**
```
Compare data protection clauses in:
- /contracts/vendor-a.md
- /contracts/vendor-b.md
- /contracts/vendor-c.md

For each, extract:
1. Data processing scope (what data, where stored)
2. Breach notification timeline
3. Subprocessor rules
4. Deletion/return policy after contract end

Rank them from strongest to weakest protection. Cite specific sections.
```

**Why RLM:** RAG would search "data protection" and return chunks — missing "subprocessor" or "deletion" sections that use different terminology. RLM reads each contract fully and cross-references.

### 2. Codebase Audit

**Task:** Find all places where user input reaches a SQL query without parameterization.

**Prompt:**
```
Audit /home/user/project/src/ for SQL injection vulnerabilities.

Read every file that contains SQL queries (search for "execute", "query", "raw", "sql").
For each, trace whether user input reaches the query and whether it's parameterized.
Flag any unparameterized user input as VULNERABLE.
Return a list of vulnerable locations with file:line and the risky code snippet.
```

**Why RLM:** Requires reading multiple files, tracing data flow, and understanding context. RAG would return isolated "execute" lines without the flow analysis.

### 3. Compliance Checklist

**Task:** Check a 100-page policy document against GDPR requirements.

**Prompt:**
```
Read /docs/privacy-policy.md (100+ pages).

Check compliance with GDPR Articles 5, 6, 7, 12-22, 25, 32, 33, 34.

For each article:
- [ ] Covered? (yes / partial / no)
- [ ] Section reference in the document
- [ ] Gap description if partial/no

Return a compliance checklist sorted by severity: missing → partial → covered.
```

**Why RLM:** 100 pages × 15 articles = impossible for chunk-based search. RLM reads systematically and checks each article against the full document.

### 4. Multi-Repo Dependency Trace

**Task:** Find every microservice that depends on a deprecated library.

**Prompt:**
```
Search across these repositories for usage of deprecated library "old-auth-lib":

- /home/user/services/api-gateway/
- /home/user/services/user-service/
- /home/user/services/order-service/
- /home/user/services/payment-service/
- /home/user/services/notification-service/

For each repo:
1. Check package.json / requirements.txt for direct dependency
2. Search imports for "old-auth-lib"
3. Trace what functions are called
4. Estimate migration effort (low/medium/high)

Return a migration priority list.
```

**Why RLM:** 5 repos × multiple file types × import tracing = RAG can't do this. RLM explores each repo recursively.

## Common Pitfalls

1. **Using RLM for short/simple tasks** — wastes tokens and time. If `read_file` + `search_files` can do it in 2 calls, don't use RLM.

2. **Vague prompts** — "analyze this file" tells RLM nothing. Specify what to look for, what dimensions matter, what output format you need.

3. **Forgetting file paths** — RLM in local mode cannot browse the filesystem. You must include the content or exact file paths in the prompt.

4. **Too many iterations on a simple task** — if the answer is on page 2, RLM doesn't need 20 iterations. Start with default (10) and increase only for genuinely large tasks.

5. **Expecting instant results** — RLM makes multiple LLM calls. A 5-file comparison can take 2-5 minutes. Set `timeout` accordingly.

6. **Not reading the error** — if RLM returns `{"success": false}`, the error message tells you exactly what's wrong. Don't retry blindly.

7. **Using RLM as a replacement for reading** — RLM is for analysis, not for "what's in this file?" Use `read_file` for that.

## Verification

After using `rlm_complete`:

- [ ] Did RLM return `success: true`?
- [ ] Does the answer address all dimensions you specified?
- [ ] Are there specific references (sections, line numbers, file paths)?
- [ ] Would a simpler tool (`read_file` + `search_files`) have sufficed? If yes, note for next time.
- [ ] If the task involved comparison, are all items compared on the same dimensions?

## Installation

If `rlm_complete` is not available, install the plugin:

```bash
# One command, all platforms
python3 install.py

# Or directly from GitHub
curl -O https://raw.githubusercontent.com/defdis/rlm-hermes-plugin/main/install.py
python3 install.py
```

Requires: Python 3.11+, git, any OpenAI-compatible API endpoint.

### Ollama Support

RLM plugin includes a built-in **OpenAI→Ollama proxy** (`proxy.py`) — zero dependencies, stdlib only. It translates `/v1/chat/completions` → `/api/chat` so RLM can use any Ollama instance (local or cloud).

**Setup for Ollama:**

```bash
# In ~/.hermes/.env:
RLM_BACKEND=ollama
RLM_OLLAMA_URL=http://localhost:11434          # or your Ollama Cloud URL
RLM_MODEL=qwen3.5:122b                          # or any model in ollama list
# No API key needed — Ollama is auth-free
```

The proxy starts automatically on first `rlm_complete` call (port 11435, localhost). No manual steps.

**How it works:**
1. Plugin detects `RLM_BACKEND=ollama` or Ollama-style URL
2. Starts `proxy.py` on `127.0.0.1:11435` (auto-managed, one instance per session)
3. RLM calls `http://127.0.0.1:11435/v1/chat/completions` (OpenAI format)
4. Proxy translates to Ollama `/api/chat` and forwards
5. Response translated back to OpenAI format

**Manual proxy (optional):**
```bash
python3 proxy.py --port 11435 --ollama-url http://your-ollama:11434
# Then set RLM_OPENAI_BASE_URL=http://127.0.0.1:11435/v1
```
