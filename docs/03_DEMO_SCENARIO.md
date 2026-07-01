# Demo Scenario — 상상우리 LiteLLM 비용 통제 PoC

## 데모 목적

비전문가/의사결정자에게 다음 한 문장을 증명한다.

> 회사가 직원에게 직접 OpenAI/Anthropic/Gemini 키를 주지 않고, LiteLLM 가상키만 지급하면 직원별·도구별·모델별 비용을 추적하고 예산 초과 시 차단할 수 있다.

---

## 데모 흐름 1 — 관리자 키 발급

### 설명

관리자가 직원과 도구별로 서로 다른 가상키를 발급한다.

### 실행 예

```bash
uv run python scripts/20_seed_keys.py
```

### 보여줄 것

- `dev-kim-claude`
- `dev-kim-codex`
- `dev-kim-gemini`
- `staff-lee-chat`
- `admin-park-test`

### 메시지

“김 개발자 한 명에게도 Claude Code용, Codex용, Gemini용 키를 따로 줍니다. 그래야 어떤 도구가 비용을 많이 쓰는지 알 수 있습니다.”

---

## 데모 흐름 2 — 허용 모델 정상 호출

### 실행 예

```bash
uv run python scripts/30_demo_calls.py --user kim --tool claude --case allowed
```

### 기대 결과

- 호출 성공
- 응답 수신
- 로그에 `dev-kim-claude` 기록
- 사용 모델 기록
- 비용/토큰 기록

### 메시지

“허용된 모델은 정상 사용됩니다. 직원 업무를 막는 것이 아니라, 회사 정책 안에서 쓰게 하는 구조입니다.”

---

## 데모 흐름 3 — 비허용 고가 모델 차단

### 실행 예

```bash
uv run python scripts/30_demo_calls.py --user lee --tool chat --case denied-model
```

### 기대 결과

- 호출 실패
- 사유: model not allowed 또는 equivalent error
- 차단 이벤트 기록

### 메시지

“일반 직원 키로 최고가 모델을 호출하면 여기서 차단됩니다. 실수로 비싼 모델을 계속 쓰는 사고를 막을 수 있습니다.”

---

## 데모 흐름 4 — 예산 초과 차단

### 실행 예

```bash
uv run python scripts/40_budget_block_test.py
```

### 기대 결과

- 예산 한도까지는 호출 성공
- 한도 초과 후 호출 실패
- 차단 이벤트 기록

### 메시지

“예산은 단순 표시가 아니라 실제 차단 조건입니다. 기업 예산을 넘는 순간 자동으로 멈춥니다.”

---

## 데모 흐름 5 — 관리자 리포트

### 실행 예

```bash
uv run python scripts/50_export_report.py
```

### 기대 결과

`docs/VERIFICATION_REPORT.md` 또는 `docs/USAGE_REPORT.md` 생성

포함 항목:

| 항목 | 설명 |
|---|---|
| 사용자별 비용 | kim, lee, park |
| 도구별 비용 | claude, codex, gemini, chat |
| 모델별 비용 | model group |
| 차단 이벤트 | 예산 초과, 모델 제한 |
| 남은 예산 | key별 remaining |

### 메시지

“관리자는 누가 어떤 도구로 어떤 모델을 얼마나 썼는지 확인할 수 있습니다. 이 데이터가 있어야 ROI 계산과 예산 증액 판단이 가능합니다.”

---

## 최종 데모 결론 문구

> 이 PoC는 Google Chat 연동 전 단계입니다. 하지만 핵심 관건인 ‘유료 LLM 사용을 회사 예산 안에서 직원별·도구별로 통제할 수 있는가’는 LiteLLM 가상키, 모델 제한, 예산 차단, 사용량 리포트로 검증할 수 있습니다.

---

## 데모에서 숨기면 안 되는 한계

1. 개인 ChatGPT/Claude 구독 앱은 기술적으로 통제 대상이 아니다.
2. Claude Code/Codex/Gemini CLI는 각 도구의 base URL 설정이 실제 버전에서 검증되어야 한다.
3. 실제 운영에서는 키 로테이션, 로그 보존, 관리자 승인 플로우가 추가되어야 한다.
4. LiteLLM 서버는 핵심 인프라가 되므로 백업/모니터링/장애 대응이 필요하다.
