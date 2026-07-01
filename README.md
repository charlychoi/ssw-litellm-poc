# 상상우리 LiteLLM AI 비용 거버넌스 PoC

> **상태**: Phase 1 + Phase 2 완료 ✅  
> **LiteLLM**: v1.83.7 (v1.82.7/v1.82.8 공급망 공격으로 사용 금지)  
> **검증 결과**: 12/12 항목 완료

LiteLLM Proxy를 AI 게이트웨이로 활용하여 직원별·도구별·모델별 LLM 비용을 기업 예산 안에서 실제로 통제하고, Claude Code / Codex CLI / Gemini CLI 같은 AI 코딩 에이전트도 동일 정책으로 제어할 수 있음을 검증한 PoC.

---

## 검증 결과 요약

### Phase 1 — 정책 검증 (7/7)

| # | 항목 | 결과 |
|:---:|---|:---:|
| 1 | LiteLLM Proxy 실행 | ✅ |
| 2 | 마스터키 / 가상키 분리 | ✅ |
| 3 | 직원/도구별 가상키 발급 (5개) | ✅ |
| 4 | 허용 모델 호출 성공 | ✅ |
| 5 | 비허용 모델 차단 (401 key_model_access_denied) | ✅ |
| 6 | 예산 초과 차단 (400 budget_exceeded) | ✅ |
| 7 | 사용량 리포트 생성 (직원/도구/모델 분리) | ✅ |

### Phase 2 — CLI 연동 검증 (5/5)

| CLI 도구 | 환경변수 | 라우팅 | 허용 모델 | 비허용 차단 |
|---|---|:---:|:---:|:---:|
| Claude Code CLI | `ANTHROPIC_BASE_URL` | ✅ | ✅ | ✅ |
| Codex CLI | `OPENAI_BASE_URL` | ✅ | ✅ | ✅ |
| Gemini CLI | `GOOGLE_GEMINI_BASE_URL` | ✅ | ⚠️¹ | ✅ |

> ¹ Gemini 허용 모델 응답은 실제 Google API Key 연동 시 가능

---

## 프로젝트 구조

```
ssw-litellm-governance-poc/
├── litellm/
│   └── config.yaml              # 모델 목록 + 마스터키 + DB 설정
├── app/
│   └── config.py                # 가상키 스펙 정의
├── scripts/
│   ├── 20_seed_keys.py          # 가상키 발급 (Admin API)
│   ├── 30_demo_calls.py         # 허용/차단 데모 호출
│   ├── 40_budget_block_test.py  # 예산 초과 차단 검증
│   ├── 50_export_report.py      # 사용량 리포트 생성
│   ├── 60_cli_integration_test.py  # Phase 2 CLI 자동 검증
│   ├── generate_report_docx.py     # Phase 1 Word 보고서
│   └── generate_final_report_docx.py  # Phase 1+2 최종 보고서
├── tests/
│   ├── test_budget_policy.py    # 예산 정책 단위 테스트
│   ├── test_key_policy.py       # 모델 접근 정책 단위 테스트
│   ├── test_report_parser.py    # 리포트 집계 단위 테스트
│   └── test_demo_client.py      # API 요청 구성 단위 테스트
├── ui/
│   └── streamlit_app.py         # 관리자/사용자 대시보드
└── docs/
    ├── PROJECT_LOG.md            # 전체 작업 로그 (이 PoC의 일지)
    ├── VERIFICATION_REPORT.md   # Phase 1+2 실제 명령어 및 응답 기록
    ├── USAGE_REPORT.md           # 사용량 집계 리포트 (자동 생성)
    ├── generated_keys.redacted.md  # 발급된 키 목록 (redacted)
    ├── SSW_LiteLLM_Governance_PoC_Report.docx       # Phase 1 보고서
    └── SSW_LiteLLM_Governance_PoC_Final_Report.docx # Phase 1+2 최종 보고서
```

---

## 빠른 시작

### 사전 요구사항

```bash
# Python 3.11+, uv, PostgreSQL 16, Node.js 18+
brew install postgresql@16
brew services start postgresql@16
createdb litellm_poc
```

### 1. 환경 설정

```bash
cp .env.example .env
# .env 편집: LITELLM_MASTER_KEY, DATABASE_URL
```

### 2. 의존성 설치

```bash
uv sync
uv pip install "litellm[proxy]==1.83.7" prisma tabulate

# Prisma 클라이언트 생성
DATABASE_URL="postgresql://$(whoami)@localhost:5432/litellm_poc" \
  uv run prisma generate --schema .venv/lib/python3.11/site-packages/litellm/proxy/schema.prisma
```

### 3. LiteLLM Proxy 시작

```bash
DATABASE_URL="postgresql://$(whoami)@localhost:5432/litellm_poc" \
LITELLM_MASTER_KEY="sk-master-ssw-poc-2024" \
  uv run litellm --config litellm/config.yaml --port 4000
```

### 4. Phase 1 — 정책 검증

```bash
# 가상키 발급
uv run python scripts/20_seed_keys.py

# 허용 모델 호출
uv run python scripts/30_demo_calls.py --user kim --tool claude --case allowed --model ssw-fake

# 비허용 모델 차단 확인
uv run python scripts/30_demo_calls.py --user lee --tool chat --case denied-model

# 예산 초과 차단 확인
uv run python scripts/40_budget_block_test.py

# 사용량 리포트 생성
uv run python scripts/50_export_report.py

# 단위 테스트 (48개)
uv run pytest tests/ -v
```

### 5. Phase 2 — CLI 연동 검증

```bash
# 자동화 검증 스크립트 (5/5 통과)
uv run python scripts/60_cli_integration_test.py
```

```bash
# Claude Code CLI 수동 테스트
ANTHROPIC_BASE_URL=http://localhost:4000 \
ANTHROPIC_API_KEY=<dev-kim-claude 가상키> \
  claude -p "Hello" --model claude-haiku-4-5

# Codex CLI 수동 테스트 (git repo 내에서)
OPENAI_BASE_URL=http://localhost:4000 \
OPENAI_API_KEY=<dev-kim-codex 가상키> \
  npx @openai/codex exec -m "gpt-4o-mini" "Just say OK"

# Gemini CLI 수동 테스트
GOOGLE_GEMINI_BASE_URL=http://localhost:4000 \
GEMINI_API_KEY=<dev-kim-gemini 가상키> \
GEMINI_CLI_TRUST_WORKSPACE=true \
  npx @google/gemini-cli -p "Just say OK"
```

### 6. 보고서 생성

```bash
# Phase 1+2 최종 Word 보고서
uv run python scripts/generate_final_report_docx.py
# → docs/SSW_LiteLLM_Governance_PoC_Final_Report.docx
# → ~/Desktop/SSW_LiteLLM_Governance_PoC_Final_Report.docx
```

### 7. Streamlit 대시보드

```bash
uv run streamlit run ui/streamlit_app.py --server.port 8501
# → http://localhost:8501
```

---

## CLI 도구 라우팅 원리

### Claude Code CLI
```bash
export ANTHROPIC_BASE_URL=http://<LiteLLM-서버>:4000
export ANTHROPIC_API_KEY=<dev-kim-claude 가상키>
claude  # 이후 Claude Code 실행 → LiteLLM 경유
```
LiteLLM이 `/v1/messages?beta=true` (Anthropic 네이티브 포맷) 처리

### Codex CLI
```bash
export OPENAI_BASE_URL=http://<LiteLLM-서버>:4000
export OPENAI_API_KEY=<dev-kim-codex 가상키>
npx @openai/codex  # LiteLLM 경유 → /v1/chat/completions
```

### Gemini CLI
```bash
# ~/.gemini/settings.json
{"security": {"auth": {"selectedType": "gemini-api-key"}}}

export GOOGLE_GEMINI_BASE_URL=http://<LiteLLM-서버>:4000
export GEMINI_API_KEY=<dev-kim-gemini 가상키>
npx @google/gemini-cli  # LiteLLM 경유 → /v1beta/models/...
```

---

## 핵심 검증 결과 — 실제 API 응답

### 비허용 모델 차단 (HTTP 401)
```json
{
  "error": {
    "message": "key not allowed to access model. This key can only access models=['ssw-low-cost', 'ssw-fake']. Tried to access ssw-expensive",
    "type": "key_model_access_denied",
    "code": "401"
  }
}
```

### 예산 초과 차단 (HTTP 400)
```json
{
  "error": {
    "message": "Budget has been exceeded! Current cost: 1.35e-05, Max budget: 0.0",
    "type": "budget_exceeded",
    "code": "400"
  }
}
```

### Claude Code 포맷 허용 응답 (HTTP 200)
```json
{
  "content": [{"text": "Claude Code → LiteLLM 게이트웨이 경유 성공! 가상키(dev-kim-claude) 모델 제어 검증 완료. [mock]", "type": "text"}],
  "model": "claude-haiku-4-5",
  "stop_reason": "end_turn"
}
```

---

## 한계 사항

| 항목 | 현황 | 운영 대응 |
|---|---|---|
| RPM/TPM 속도 제한 | Redis 미설정으로 비활성 | `brew install redis` 후 즉시 활성화 |
| 실제 LLM 호출 | mock_response 사용 | OpenRouter/Anthropic/OpenAI API Key 등록 |
| Codex CLI 클라이언트 검증 | 표준 모델명 필요 | LiteLLM에서 OpenAI 모델명 alias 설정 |
| Gemini CLI 전체 성공 | Google Key 필요 | config.yaml에 gemini 모델 + GOOGLE_API_KEY |
| 개인 ChatGPT/Claude 앱 | 기술적 통제 불가 | 정책 규정 + 의무 사용 지침 |

---

## 관련 문서

- [PROJECT_LOG.md](docs/PROJECT_LOG.md) — 전체 작업 과정 상세 기록
- [VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md) — 실제 명령어 및 API 응답
- [01_PRD.md](docs/01_PRD.md) — 제품 요구사항
- [00_CLAUDE_CODE_EXECUTION_PLAN.md](docs/00_CLAUDE_CODE_EXECUTION_PLAN.md) — 초기 실행 계획
- [최종 보고서 (docx)](docs/SSW_LiteLLM_Governance_PoC_Final_Report.docx)
