#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${ROOT}/sample_request_log.redacted.jsonl"
HOME_DIR="${ROOT}/.hermes-test-home"
mkdir -p "$HOME_DIR"
cp "$ROOT/hermes_test_config.example.yaml" "$HOME_DIR/config.yaml"
rm -f "$LOG" /opt/data/workspace/hermes_litellm_poc_mock_requests.jsonl
python3 "$ROOT/mock_openai_gateway.py" &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT
sleep 1
HERMES_HOME="$HOME_DIR" OPENAI_BASE_URL="http://127.0.0.1:40123/v1" OPENAI_API_KEY="test-virtual-key" /opt/hermes/bin/hermes chat -q 'Respond with exactly POC_OK' --provider custom --model test-model --toolsets safe --quiet
cp /opt/data/workspace/hermes_litellm_poc_mock_requests.jsonl "$LOG"
python3 - <<'PY'
import json
from pathlib import Path
p=Path('/opt/data/workspace/hermes_litellm_poc_mock_requests.jsonl')
for line in p.read_text().splitlines():
    if not line.strip(): continue
    r=json.loads(line)
    if r['path'].endswith('/chat/completions'):
        h=r.get('headers',{})
        if 'Authorization' in h: h['Authorization']='Bearer test-virtual-key...REDACTED'
        j=r.get('json',{})
        print(json.dumps({'path':r['path'],'headers':h,'model':j.get('model'),'stream':j.get('stream'),'user':j.get('user'),'metadata':j.get('metadata'),'extra_body_keys':[k for k in j if k not in {'messages','model','stream','tools','tool_choice'}]}, ensure_ascii=False, indent=2))
PY
