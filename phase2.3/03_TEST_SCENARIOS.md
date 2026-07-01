# Test Scenarios — Charly 테스트 절차

## Scenario 1 — OpenRouter 실제 호출

### 목적

OpenRouter 무료 모델이 LiteLLM alias를 통해 실제 응답하는지 확인한다.

### 절차

```bash
uv run python scripts/70_real_provider_test.py --provider openrouter
```

또는 직접 호출:

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $STAFF_LEE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ssw-free-openrouter",
    "messages": [{"role": "user", "content": "상상우리 AI 게이트웨이 PoC를 한 문장으로 설명해줘."}]
  }'
```

### 기대 결과

- 실제 외부 LLM 응답
- token usage 기록
- spend log 기록
- `staff-lee-chat` 사용량 증가

---

## Scenario 2 — Groq 실제 호출

### 목적

Groq 무료/저가 모델이 빠른 응답 후보로 적합한지 확인한다.

### 절차

```bash
uv run python scripts/70_real_provider_test.py --provider groq
```

### 기대 결과

- 실제 Groq 모델 응답
- latency 기록
- token usage 기록
- spend log 기록

실패 시 기록할 것:

- API Key 문제
- 모델명 변경
- 무료 tier 제한
- provider rate limit

---

## Scenario 3 — 비허용 모델 차단

### 목적

실제 provider 모델이 연결되어 있어도 일반 직원 키는 고가/비허용 모델을 호출할 수 없는지 확인한다.

### 절차

```bash
uv run python scripts/70_real_provider_test.py --case denied-model
```

또는:

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $STAFF_LEE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ssw-expensive-real",
    "messages": [{"role": "user", "content": "고급 전략 보고서를 작성해줘."}]
  }'
```

### 기대 결과

- HTTP 401
- `key_model_access_denied`
- provider까지 요청 전달되지 않음
- 비용 발생 없음

---

## Scenario 4 — 실제 호출 기반 예산 차단

### 목적

실제 provider 호출 비용이 누적된 뒤 예산 차단이 작동하는지 확인한다.

### 절차

```bash
uv run python scripts/70_real_provider_test.py --case budget-exceeded
```

검증 흐름:

1. 낮은 예산 테스트 키 생성
2. 실제 provider 모델 1회 호출
3. spend 기록 확인
4. max_budget을 0 또는 매우 낮게 설정
5. 재호출

### 기대 결과

- 첫 호출 성공
- spend 누적
- 두 번째 호출 차단
- `budget_exceeded` 기록

---

## Scenario 5 — 관리자 리포트 확인

### 목적

실제 provider 호출이 기존 리포트 체계에 반영되는지 확인한다.

### 절차

```bash
uv run python scripts/50_export_report.py
```

확인 항목:

| 항목 | 기대 |
|---|---|
| 사용자별 | lee/kim/park 분리 |
| 도구별 | chat/codex/claude/gemini 분리 |
| 모델별 | ssw-free-openrouter/ssw-fast-groq 분리 |
| provider별 | openrouter/groq 분리 |
| token/spend | 표시 |
| 차단 이벤트 | 표시 |

---

## Scenario 6 — Claude/Codex 실제 provider 경유 선택 검증

### 목적

CLI에서 mock이 아닌 실제 alias 모델을 호출할 수 있는지 선택적으로 확인한다.

### 예시

Codex/OpenAI-compatible 경로:

```bash
OPENAI_BASE_URL=http://localhost:4000 \
OPENAI_API_KEY=$CODEX_KEY \
codex --model ssw-free-openrouter "한 문장으로 CODEX_REAL_PROVIDER_OK라고 답해줘"
```

성공 기준:

- CLI 응답 성공
- LiteLLM 로그에 `dev-kim-codex`
- 모델 alias 기록
- token/spend 기록
