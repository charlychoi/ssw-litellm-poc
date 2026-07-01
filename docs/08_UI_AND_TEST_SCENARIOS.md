# UI and Test Scenarios — LiteLLM 비용 거버넌스 PoC

## 1. 결론

기존 PRD에는 관리자 리포트/최소 대시보드 요구가 들어 있었지만, **관리자와 사용자용 PoC UI 화면 정의는 충분히 상세하지 않았다.**

따라서 PoC 구현 범위에 아래 2개 UI를 명시적으로 추가한다.

1. **사용자 테스트 UI** — 직원/도구/모델/프롬프트를 선택해 호출하는 화면
2. **관리자 통제 UI** — 가상키, 모델권한, 예산, 사용량, 차단 이벤트를 보는 화면

---

## 2. PoC UI 범위

### 2.1 사용자 테스트 UI

목적: 직원 입장에서 회사 AI Gateway를 통해 LLM을 사용하는 흐름을 데모한다.

URL 예시:

```text
http://localhost:8000/user
```

필수 구성:

| 영역 | 필드 | 설명 |
|---|---|---|
| 사용자 선택 | user | kim / lee / park |
| 도구 선택 | tool | claude-code / codex-cli / gemini-cli / chat |
| 모델 선택 | model | 허용/비허용 모델 선택 가능 |
| 업무유형 | task_type | coding / document / summary / general |
| 프롬프트 입력 | prompt | 테스트 문장 입력 |
| 실행 버튼 | Send | LiteLLM 경유 호출 |
| 결과 영역 | response | LLM 응답 또는 차단 사유 표시 |
| 비용 영역 | cost/tokens | 추정 또는 실제 비용 표시 |
| 상태 영역 | allowed/blocked | 성공/차단 여부 표시 |

사용자 UI 핵심 메시지:

> 직원은 평소처럼 AI를 쓰지만, 뒤에서는 회사 Gateway가 모델 권한과 예산을 확인한다.

---

### 2.2 관리자 통제 UI

목적: 관리자 입장에서 직원별·도구별 비용 통제 가능성을 확인한다.

URL 예시:

```text
http://localhost:8000/admin
```

필수 구성:

#### A. 가상키 현황

| key_alias | user | tool | allowed_models | budget | used | remaining | status |
|---|---|---|---|---:|---:|---:|---|
| dev-kim-claude | kim | claude-code | claude-sonnet | 5.00 | 1.20 | 3.80 | active |

#### B. 사용량 요약

- 총 호출 수
- 총 비용
- 사용자별 비용
- 도구별 비용
- 모델별 비용

#### C. 차단 이벤트

| time | user | tool | model | reason |
|---|---|---|---|---|
| 10:32 | lee | chat | expensive-model | model_not_allowed |
| 10:35 | kim | claude-code | claude-sonnet | budget_exceeded |

#### D. 데모 버튼

- 정상 호출 실행
- 비허용 모델 호출 실행
- 예산 초과 테스트 실행
- 리포트 새로고침

관리자 UI 핵심 메시지:

> 관리자는 누가, 어떤 도구로, 어떤 모델을, 얼마나 썼고, 무엇이 차단됐는지 확인할 수 있다.

---

## 3. 권장 구현 방식

PoC에서는 복잡한 프론트엔드보다 빠른 검증이 중요하다.

### 옵션 A — Streamlit 권장

장점:

- 구현 빠름
- 폼/표/차트가 쉬움
- 데모에 적합

파일 예시:

```text
ui/streamlit_app.py
```

실행:

```bash
uv run streamlit run ui/streamlit_app.py --server.port 8501
```

### 옵션 B — FastAPI HTML

장점:

- 백엔드와 일체형
- 외부 의존성 적음

파일 예시:

```text
app/routers/ui.py
app/templates/user.html
app/templates/admin.html
```

실행:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### PoC 권장

**Streamlit 우선.** 빠른 시연과 표/차트 표시가 쉽다.

---

## 4. Charly 테스트 시나리오

## Scenario 1 — 정상 사용

### 목적

허용된 직원/도구/모델 조합은 정상 응답하는지 확인한다.

### 절차

1. 사용자 UI 접속
2. 사용자 `kim` 선택
3. 도구 `claude-code` 선택
4. 모델 `claude-sonnet` 또는 PoC의 허용 모델 선택
5. 프롬프트 입력:

```text
상상우리 AI 게이트웨이 PoC의 목적을 한 문단으로 요약해줘.
```

6. Send 클릭

### 기대 결과

- 응답 성공
- 상태: `allowed`
- 사용량/비용 증가
- 관리자 UI에서 `dev-kim-claude` 사용량 증가 확인

---

## Scenario 2 — 비허용 모델 차단

### 목적

일반 직원이 고가 모델을 호출할 때 차단되는지 확인한다.

### 절차

1. 사용자 UI 접속
2. 사용자 `lee` 선택
3. 도구 `chat` 선택
4. 모델 `expensive-model` 또는 일반 직원에게 허용되지 않은 모델 선택
5. 프롬프트 입력:

```text
이 문서를 고급 전략 보고서로 작성해줘.
```

6. Send 클릭

### 기대 결과

- 응답 실패
- 상태: `blocked`
- 차단 사유: `model_not_allowed`
- 관리자 UI 차단 이벤트에 기록

---

## Scenario 3 — 예산 초과 차단

### 목적

예산이 표시만 되는 것이 아니라 실제 차단 조건으로 작동하는지 확인한다.

### 절차

1. 관리자 UI에서 테스트 키 `staff-lee-chat`의 예산을 낮게 설정하거나 이미 낮게 설정된 테스트 키 사용
2. 사용자 UI에서 `lee` / `chat` / 허용 모델 선택
3. 같은 프롬프트를 여러 번 호출하거나 `Run budget exceed test` 버튼 클릭
4. 예산 초과 후 다시 호출

### 기대 결과

- 예산 내 호출은 성공
- 예산 초과 후 호출은 실패
- 차단 사유: `budget_exceeded`
- 관리자 UI의 남은 예산이 0 또는 초과 상태로 표시

---

## Scenario 4 — 도구별 비용 구분

### 목적

같은 사용자라도 도구별 비용을 분리 추적할 수 있는지 확인한다.

### 절차

1. 사용자 `kim` 선택
2. 도구 `claude-code`로 1회 호출
3. 도구 `codex-cli`로 1회 호출
4. 도구 `gemini-cli`로 1회 호출
5. 관리자 UI 사용량 요약 확인

### 기대 결과

관리자 UI에 다음이 분리 표시된다.

| user | tool | key_alias | calls |
|---|---|---|---:|
| kim | claude-code | dev-kim-claude | 1 |
| kim | codex-cli | dev-kim-codex | 1 |
| kim | gemini-cli | dev-kim-gemini | 1 |

---

## Scenario 5 — 관리자 리포트 export

### 목적

PoC 결과를 Markdown으로 남길 수 있는지 확인한다.

### 절차

1. 관리자 UI에서 `Export report` 클릭 또는 CLI 실행

```bash
uv run python scripts/50_export_report.py
```

2. `docs/VERIFICATION_REPORT.md` 확인

### 기대 결과

리포트에 다음이 포함된다.

- 정상 호출 결과
- 비허용 모델 차단 결과
- 예산 초과 차단 결과
- 사용자/도구/모델별 사용량
- 미검증 항목

---

## 5. 데모 판정표

| 항목 | Charly가 볼 화면 | 성공 기준 |
|---|---|---|
| 정상 호출 | 사용자 UI | 응답 성공 + allowed 표시 |
| 모델 제한 | 사용자 UI + 관리자 UI | blocked + model_not_allowed |
| 예산 제한 | 사용자 UI + 관리자 UI | blocked + budget_exceeded |
| 도구별 추적 | 관리자 UI | kim의 3개 도구 비용 분리 |
| 리포트 | Markdown | 실행 결과 기록 |

---

## 6. PoC에서 보여줄 최종 메시지

> 이 PoC는 사내 AI 사용을 막는 시스템이 아니라, 회사 예산과 권한 안에서 안전하게 쓰게 하는 게이트웨이다. 직원은 AI를 계속 사용하고, 관리자는 비용·모델·도구별 사용량을 확인하며, 예산 초과와 고가 모델 오남용은 자동 차단된다.
