# Security and Cost Guardrails — 실제 Provider 검증

## 1. API Key 보안

- OpenRouter/Groq API Key는 `.env`에만 저장한다.
- `.env.example`에는 키 값을 넣지 않는다.
- 리포트에는 `sk-or-v1-abc...xyz`처럼 redacted 형태만 기록한다.
- Telegram, GitHub, 문서에 원문 키를 붙이지 않는다.

## 2. 비용 가드레일

무료 모델 테스트라도 아래를 지킨다.

| 항목 | 권장값 |
|---|---:|
| max_tokens | 100~300 |
| 테스트 호출 수 | 10회 이하 |
| 테스트 키 예산 | $0.01~$0.10 |
| 일반 직원 키 예산 | $1 이하 |
| timeout | 30초 이하 |

## 3. 무료 모델 주의사항

- 무료 모델은 provider 정책에 따라 rate limit이 낮을 수 있다.
- 모델명이 자주 바뀔 수 있다.
- 무료 모델도 일부 환경에서는 상업 이용/데이터 사용 조건 확인이 필요하다.
- Gemini 무료 tier는 상업 업무 검증에는 부적합할 수 있으므로 이번 테스트 우선순위에서 제외한다.

## 4. 로그 정책

리포트에 남겨도 되는 것:

- 모델명
- alias
- token 수
- spend
- HTTP status
- error type

남기면 안 되는 것:

- API Key 원문
- 고객/직원 개인정보
- 민감한 프롬프트 전문
- provider account 정보

## 5. 실패 시 대응

| 실패 | 대응 |
|---|---|
| OpenRouter free model 404 | 현재 사용 가능한 free model로 교체 |
| Groq model not found | Groq 모델 목록 확인 후 교체 |
| rate limit | 호출 간격 증가, max_tokens 축소 |
| spend 미기록 | LiteLLM pricing/model map 확인 |
| token usage 없음 | provider response format 확인 |
| budget 차단 안 됨 | key spend/current spend와 max_budget 재확인 |

## 6. 운영 전 필수 보완

- Redis RPM/TPM 활성화
- 실제 provider별 월 예산 설정
- key rotation 절차
- 개인 구독 AI 사용 정책
- SSO/OIDC 또는 직원 계정 매핑
