# Acceptance Criteria — 실제 Provider 검증 PoC

## 1. Gateway/환경

- [ ] LiteLLM Proxy가 정상 실행된다.
- [ ] LiteLLM 버전이 안전 버전이다. v1.82.7/v1.82.8 사용 금지.
- [ ] OpenRouter API Key가 `.env`에서 로드된다.
- [ ] Groq API Key가 `.env`에서 로드된다.
- [ ] API Key 원문이 로그/문서에 노출되지 않는다.

## 2. Model Alias

- [ ] `ssw-free-openrouter` alias가 실제 OpenRouter 모델로 연결된다.
- [ ] `ssw-fast-groq` alias가 실제 Groq 모델로 연결된다.
- [ ] `/v1/models` 또는 호출 결과에서 alias 확인이 가능하다.
- [ ] 사용 불가 모델은 명확히 실패 사유가 기록된다.

## 3. 실제 호출

- [ ] OpenRouter 모델이 mock 없이 실제 응답한다.
- [ ] Groq 모델이 mock 없이 실제 응답한다. 불가 시 API Key/모델/쿼터 사유를 기록한다.
- [ ] 응답에 token usage가 기록된다.
- [ ] LiteLLM spend log에 비용 또는 추정 비용이 기록된다.

## 4. 가상키 정책

- [ ] `staff-lee-chat`은 허용된 저가/무료 모델만 호출 가능하다.
- [ ] `staff-lee-chat`으로 고가/비허용 모델 호출 시 `key_model_access_denied`가 발생한다.
- [ ] `dev-kim-codex`는 지정된 모델 alias만 호출 가능하다.
- [ ] `admin-park-test`는 테스트 모델 전체 호출 가능하다.

## 5. 예산 차단

- [ ] 낮은 예산 테스트 키를 생성한다.
- [ ] 실제 provider 호출 후 spend가 누적된다.
- [ ] max_budget 초과 또는 0 설정 후 추가 호출이 `budget_exceeded`로 차단된다.

## 6. 리포트

- [ ] `docs/REAL_PROVIDER_VERIFICATION_REPORT.md`가 생성된다.
- [ ] 사용자/도구/모델별 사용량이 표시된다.
- [ ] provider별 사용량이 표시된다.
- [ ] token/spend가 표시된다.
- [ ] 실패/미검증 항목이 숨김 없이 표시된다.

## 최종 성공 판정

아래 4개가 되면 성공이다.

1. 실제 외부 LLM 응답 수신
2. token/spend 기록
3. 가상키별 모델 제한 유지
4. 실제 호출 기반 예산 차단 확인
