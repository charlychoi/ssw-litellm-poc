# PRD — LiteLLM 실제 Provider 호출 검증 PoC

## 1. 제품/작업명

**상상우리 LiteLLM Real Provider Validation PoC**

## 2. 배경

기존 LiteLLM Governance PoC에서는 다음이 검증되었다.

- 직원/도구별 Virtual Key 발급
- 가상키별 모델 접근 제한
- 예산 초과 시 API 차단
- 사용량 리포트 생성
- Claude Code / Codex CLI / Gemini CLI의 LiteLLM 라우팅 가능성

그러나 상당수 허용 응답은 `mock_response` 기반이었다. 따라서 실제 운영 전에는 OpenRouter/Groq 같은 실제 외부 LLM provider를 연결하여 다음을 검증해야 한다.

- 실제 외부 모델 호출 성공 여부
- 실제 token usage 기록 여부
- LiteLLM spend/cost 집계 여부
- model alias → 실제 provider 모델 매핑 여부
- 실제 호출 기반 예산 차단 여부
- CLI 도구에서 실제 응답을 받으면서도 가상키 정책이 유지되는지

## 3. 목표

### Primary Goal

**mock이 아닌 실제 OpenRouter/Groq 무료 모델 호출에서도 LiteLLM의 가상키·모델 제한·예산 차단·사용량 리포트가 정상 동작함을 검증한다.**

### Secondary Goals

- 상상우리 기본 저가 모델 후보 검증
- OpenAI-compatible provider 기반 Codex/일반 API 경로 검증
- 향후 Google Chat/Hermes Agent 연결 시 사용할 실제 model alias 구조 확정
- 운영 전 비용 리스크와 API Key 관리 절차 확인

## 4. In Scope

- OpenRouter API Key 연결
- Groq API Key 연결
- LiteLLM config.yaml에 실제 provider 모델 추가
- 내부 alias 모델명 정의
  - `ssw-free-openrouter`
  - `ssw-fast-groq`
  - `ssw-low-cost-real`
- 실제 `/v1/chat/completions` 호출
- token usage/spend 로그 확인
- 가상키별 allowed_models 적용 확인
- 예산 초과 차단 재검증
- 리포트 export 갱신
- Streamlit 관리자 UI에 실제 provider 호출 결과 표시 가능하면 포함

## 5. Out of Scope

- Google Chat 연동
- SSO/OIDC
- 결제/회계 시스템 연동
- 전체 운영 배포
- 실제 직원 개인정보 연동
- 대규모 부하 테스트
- 개인 ChatGPT/Claude 구독 앱 통제

## 6. 사용자/키 정책

| Key Alias | 사용자 | 도구 | 허용 모델 | 예산 |
|---|---|---|---|---:|
| `staff-lee-chat` | lee | 일반 채팅 | `ssw-free-openrouter`, `ssw-low-cost-real` | $1 |
| `dev-kim-codex` | kim | Codex CLI/API | `gpt-4o-mini`, `ssw-free-openrouter`, `ssw-fast-groq` | $5 |
| `dev-kim-claude` | kim | Claude Code | 기존 Claude alias + 실제 저가 fallback | $5 |
| `admin-park-test` | park | 관리자 | 전체 테스트 모델 | $10 |

## 7. 실제 Provider 모델 후보

### OpenRouter 후보

| 내부 alias | 실제 모델 예시 | 목적 |
|---|---|---|
| `ssw-free-openrouter` | `openrouter/meta-llama/llama-3.1-8b-instruct:free` 또는 사용 가능 free 모델 | 무료 실제 호출 검증 |
| `ssw-low-cost-real` | OpenRouter 저가 모델 | 일반 직원 기본 모델 후보 |

### Groq 후보

| 내부 alias | 실제 모델 예시 | 목적 |
|---|---|---|
| `ssw-fast-groq` | `groq/llama-3.1-8b-instant` 또는 현재 사용 가능 모델 | 빠른 응답/데모 검증 |

실제 모델명은 테스트 시점의 provider catalog에 맞게 조정한다.

## 8. 핵심 기능 요구사항

### F1. Provider Key 설정

`.env`에 다음을 추가한다.

```bash
OPENROUTER_API_KEY=...
GROQ_API_KEY=...
```

`.env.example`에는 값 없이 설명만 둔다.

### F2. LiteLLM config 업데이트

`litellm/config.yaml`에 실제 provider 모델을 추가한다.

예시:

```yaml
- model_name: ssw-free-openrouter
  litellm_params:
    model: openrouter/<free-model-name>
    api_key: os.environ/OPENROUTER_API_KEY

- model_name: ssw-fast-groq
  litellm_params:
    model: groq/<groq-model-name>
    api_key: os.environ/GROQ_API_KEY
```

### F3. 실제 호출 스크립트

`scripts/70_real_provider_test.py`를 만든다.

필수 테스트:

1. OpenRouter 실제 호출
2. Groq 실제 호출
3. 가상키별 allowed model 호출 성공
4. 비허용 실제 모델 호출 차단
5. 낮은 예산 설정 후 실제 호출 기반 budget_exceeded 확인
6. 사용량 리포트 반영

### F4. 사용량/비용 로그 확인

다음 항목을 리포트에 기록한다.

- key_alias
- user_id
- tool
- requested_model
- resolved/provider model
- prompt_tokens
- completion_tokens
- total_tokens
- spend
- status: allowed/blocked
- error_type

### F5. 리포트 생성

`docs/REAL_PROVIDER_VERIFICATION_REPORT.md`를 생성한다.

## 9. 성공 기준

| 기준 | 성공 조건 |
|---|---|
| 실제 응답 | mock 문구 없이 외부 모델 응답 수신 |
| token 기록 | prompt/completion token 기록 확인 |
| spend 기록 | LiteLLM spend 또는 추정 비용 기록 |
| alias 매핑 | 내부 alias가 실제 provider 모델로 연결 |
| 가상키 제한 | 허용 모델만 성공, 비허용 모델 차단 |
| 예산 차단 | 실제 호출 비용 누적 후 budget_exceeded 확인 |
| 리포트 | 직원/도구/모델별 실제 사용량 리포트 생성 |

## 10. 최종 산출물

| 산출물 | 위치 |
|---|---|
| 업데이트된 LiteLLM config | `litellm/config.yaml` |
| 실제 provider 테스트 스크립트 | `scripts/70_real_provider_test.py` |
| 실제 provider 리포트 | `docs/REAL_PROVIDER_VERIFICATION_REPORT.md` |
| 업데이트된 README | `README.md` |
| 테스트 결과 로그 | `docs/logs/` 또는 리포트 내 포함 |
