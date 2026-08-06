#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export LITELLM_PROXY_URL="${LITELLM_PROXY_URL:-http://127.0.0.1:4100}"
echo "1) Start PostgreSQL and LiteLLM proxy separately"
echo "2) Seed keys: LITELLM_PROXY_URL=$LITELLM_PROXY_URL LITELLM_MASTER_KEY=... uv run python scripts/20_seed_keys.py"
echo "3) Run demo calls: uv run python scripts/30_demo_calls.py --user lee --tool chat --case allowed --model ssw-fake"
echo "4) Run budget test: uv run python scripts/40_budget_block_test.py"
echo "5) Run Hermes profile smoke tests with isolated HERMES_HOME and virtual keys"
