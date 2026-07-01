#!/usr/bin/env bash
# Environment preflight check for LiteLLM Governance PoC

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$ROOT_DIR/.env"

PASS="✅"
WARN="⚠️ "
FAIL="❌"

echo ""
echo "========================================"
echo "  LiteLLM Governance PoC — Env Check"
echo "========================================"
echo ""

issues=0

# 1. Check .env file
if [ -f "$ENV_FILE" ]; then
    echo "$PASS  .env file found at $ENV_FILE"
    # Source it so subsequent checks pick up values
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
else
    echo "$WARN .env file NOT found at $ENV_FILE"
    echo "       Create it from .env.example if available."
    issues=$((issues + 1))
fi

echo ""

# 2. Check LITELLM_MASTER_KEY
if [ -n "$LITELLM_MASTER_KEY" ]; then
    redacted="${LITELLM_MASTER_KEY:0:8}..."
    echo "$PASS  LITELLM_MASTER_KEY is set ($redacted)"
else
    echo "$FAIL  LITELLM_MASTER_KEY is NOT set"
    echo "       Set it in .env: LITELLM_MASTER_KEY=sk-..."
    issues=$((issues + 1))
fi

echo ""

# 3. Check LiteLLM proxy reachability
PROXY_URL="${LITELLM_PROXY_URL:-http://localhost:4000}"
echo "Checking proxy at $PROXY_URL ..."

health_response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$PROXY_URL/health/liveliness" 2>/dev/null)

if [ "$health_response" = "200" ]; then
    echo "$PASS  LiteLLM proxy is reachable ($PROXY_URL) — HTTP $health_response"
else
    # Try /health as fallback
    health_response2=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$PROXY_URL/health" 2>/dev/null)
    if [ "$health_response2" = "200" ]; then
        echo "$PASS  LiteLLM proxy is reachable ($PROXY_URL/health) — HTTP $health_response2"
    else
        echo "$FAIL  LiteLLM proxy NOT reachable at $PROXY_URL"
        echo "       Start it with: uv run litellm --config litellm/config.yaml --port 4000"
        issues=$((issues + 1))
    fi
fi

echo ""

# 4. Check litellm version
if command -v uv &>/dev/null; then
    echo "LiteLLM version (via uv):"
    uv run --project "$ROOT_DIR" litellm --version 2>/dev/null || \
        uv run litellm --version 2>/dev/null || \
        echo "  (could not determine version — is litellm in pyproject.toml?)"
elif command -v litellm &>/dev/null; then
    echo "LiteLLM version:"
    litellm --version
else
    echo "$WARN  litellm CLI not found. Install via: uv add litellm"
    issues=$((issues + 1))
fi

echo ""

# 5. Check docs/ and generated keys
if [ -f "$ROOT_DIR/docs/generated_keys.json" ]; then
    key_count=$(python3 -c "import json; d=json.load(open('$ROOT_DIR/docs/generated_keys.json')); print(len(d))" 2>/dev/null)
    echo "$PASS  generated_keys.json exists ($key_count key(s))"
else
    echo "$WARN  docs/generated_keys.json not found — run 20_seed_keys.py first"
fi

echo ""
echo "========================================"
if [ "$issues" -eq 0 ]; then
    echo "  $PASS All checks passed — ready to run PoC scripts"
else
    echo "  $FAIL $issues issue(s) found — resolve above before proceeding"
fi
echo "========================================"
echo ""

exit $issues
