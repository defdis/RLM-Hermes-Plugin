#!/usr/bin/env bash
set -euo pipefail

# ─── RLM Plugin for Hermes Agent — Auto Installer ───────────────────────────
# This script installs the RLM (Recursive Language Model) plugin for Hermes.
# Works on any Linux/macOS with Python 3.12+ and an OpenAI-compatible API.
# ──────────────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     RLM Plugin Installer for Hermes Agent                ║${NC}"
echo -e "${CYAN}║     Recursive Language Model — deep analysis             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Check Python ────────────────────────────────────────────────────────────
PYTHON=""
for py in python3.12 python3.11 python3.13 python3; do
    if command -v "$py" &>/dev/null; then
        ver=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}ERROR: Python 3.11+ required. Install it first:${NC}"
    echo "  Ubuntu/Debian: sudo apt install python3.12 python3.12-venv"
    echo "  macOS:         brew install python@3.12"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python: $PYTHON ($($PYTHON --version))"

# ─── Check Hermes ────────────────────────────────────────────────────────────
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
if [ ! -d "$HERMES_HOME" ]; then
    echo -e "${RED}ERROR: Hermes not found at $HERMES_HOME${NC}"
    echo "  Install Hermes first: https://hermes-agent.nousresearch.com"
    exit 1
fi
echo -e "${GREEN}✓${NC} Hermes found at $HERMES_HOME"

# ─── API Credentials ─────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}API Configuration${NC}"
echo "RLM needs an OpenAI-compatible API endpoint."
echo ""
echo "Examples:"
echo "  OpenAI:      https://api.openai.com/v1"
echo "  OpenRouter:  https://openrouter.ai/api/v1"
echo "  Ollama:      http://localhost:11434/v1"
echo "  vLLM:        http://your-server:8000/v1"
echo ""

read -r -p "API Base URL: " BASE_URL
read -r -p "API Key: " API_KEY
read -r -p "Model name [gpt-4o]: " MODEL
MODEL="${MODEL:-gpt-4o}"

# ─── Install RLM library ─────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}Installing RLM library...${NC}"

RLM_DIR="$HERMES_HOME/rlm"
RLM_REPO="$RLM_DIR/repo"
RLM_VENV="$RLM_DIR/.venv"
PINNED_COMMIT="156fd72"

mkdir -p "$RLM_DIR"

if [ ! -d "$RLM_REPO" ]; then
    git clone https://github.com/alexzhang13/rlm.git "$RLM_REPO"
    cd "$RLM_REPO" && git checkout "$PINNED_COMMIT" && cd - > /dev/null
fi

$PYTHON -m venv "$RLM_VENV"
"$RLM_VENV/bin/pip" install -q -e "$RLM_REPO"

echo -e "${GREEN}✓${NC} RLM library installed"

# ─── Configure environment ───────────────────────────────────────────────────
echo ""
echo -e "${CYAN}Configuring environment...${NC}"

ENV_FILE="$HERMES_HOME/.env"

# Remove old RLM lines if present
if [ -f "$ENV_FILE" ]; then
    sed -i '/^RLM_OPENAI_/d' "$ENV_FILE"
fi

cat >> "$ENV_FILE" <<EOF
RLM_OPENAI_BASE_URL=$BASE_URL
RLM_OPENAI_API_KEY=$API_KEY
RLM_MODEL=$MODEL
EOF

echo -e "${GREEN}✓${NC} Environment configured"

# ─── Install plugin ──────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}Installing Hermes plugin...${NC}"

PLUGIN_DIR="$HERMES_HOME/plugins/rlm"
mkdir -p "$PLUGIN_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/plugin/__init__.py" ]; then
    cp "$SCRIPT_DIR/plugin/__init__.py" "$PLUGIN_DIR/__init__.py"
else
    echo -e "${RED}ERROR: plugin/__init__.py not found. Are you running from the repo root?${NC}"
    exit 1
fi

# Copy SKILL.md so the agent knows when and how to use rlm_complete
if [ -f "$SCRIPT_DIR/skills/rlm-deep-analysis/SKILL.md" ]; then
    cp "$SCRIPT_DIR/skills/rlm-deep-analysis/SKILL.md" "$PLUGIN_DIR/SKILL.md"
    echo -e "${GREEN}✓${NC} Skill installed (agent instructions)"
fi

echo -e "${GREEN}✓${NC} Plugin installed"

# ─── Restart Hermes ──────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}Restarting Hermes...${NC}"
echo -e "${YELLOW}⚠${NC} Please restart Hermes manually to load the new plugin."
echo "   If using systemd: sudo systemctl restart hermes-gateway-*.service"
echo "   Or use your Hermes management tool (hermes-ctl, /restart command, etc.)"

# ─── Done ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     RLM Plugin installed successfully!                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Verify: ask your Hermes agent 'Compare RAG and RLM in 3 bullet points'"
echo ""
echo "Uninstall:"
echo "  rm -rf ~/.hermes/plugins/rlm/ ~/.hermes/rlm/"
echo "  # Remove RLM_OPENAI_* lines from ~/.hermes/.env"
echo ""
