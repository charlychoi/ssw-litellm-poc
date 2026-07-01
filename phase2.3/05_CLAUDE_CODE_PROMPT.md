# Claude Code 작업 프롬프트 — 실제 Provider 검증 PoC

아래 내용을 Claude Code에 그대로 전달하세요.

---

당신은 상상우리 LiteLLM 비용 거버넌스 PoC의 후속 검증 담당자입니다.

기존 PoC는 LiteLLM의 가상키, 모델 제한, 예산 차단, CLI 라우팅 가능성을 mock 기반으로 상당 부분 검증했습니다. 이번 작업의 목적은 **OpenRouter/Groq 무료 모델을 실제로 호출하여 mock이 아닌 외부 LLM 호출에서도 token/spend/예산차단/리포트가 정상 작동하는지 검증**하는 것입니다.

## 작업 위치

기존 프로젝트:

```text
/opt/data/workspace/ssw-litellm-governance-poc/
```

## 참고 문서

- `00_EXECUTION_PLAN.md`
- `01_PRD_REAL_PROVIDER_VALIDATION.md`
- `02_ACCEPTANCE_CRITERIA.md`
- `03_TEST_SCENARIOS.md`
- `04_SECURITY_AND_COST_GUARDRAILS.md`

## 구현 목표

1. `.env.example`에 OpenRouter/Groq 키 항목 추가
2. `litellm/config.yaml`에 실제 provider alias 추가
   - `ssw-free-openrouter`
   - `ssw-fast-groq`
   - `ssw-low-cost-real`
3. 기존 가상키 allowed_models 업데이트
4. `scripts/70_real_provider_test.py` 작성
5. OpenRouter 실제 호출 검증
6. Groq 실제 호출 검증
7. token usage와 spend log 확인
8. 비허용 모델 차단 확인
9. 실제 호출 기반 budget_exceeded 확인
10. `docs/REAL_PROVIDER_VERIFICATION_REPORT.md` 생성

## 중요한 제약

- API Key 원문을 절대 문서/로그에 저장하지 마세요.
- 무료 모델이라도 max_tokens와 호출 수를 제한하세요.
- 모델명이 바뀌었으면 현재 사용 가능한 무료/저가 모델로 대체하고 리포트에 기록하세요.
- 실패를 숨기지 말고 정확한 HTTP status/error를 기록하세요.
- mock 응답과 실제 provider 응답을 명확히 구분하세요.

## 완료 기준

- [ ] OpenRouter 실제 응답 성공
- [ ] Groq 실제 응답 성공 또는 실패 사유 명확히 기록
- [ ] token usage 기록
- [ ] spend 기록
- [ ] 가상키 모델 제한 유지
- [ ] 실제 호출 기반 예산 차단 확인
- [ ] Markdown 리포트 생성

## 최종 보고 형식

```md
# Real Provider Validation 결과

## 실행 환경
## Provider 설정
## 실제 호출 결과
## Token/Spend 검증
## 모델 제한 검증
## 예산 차단 검증
## 실패/미검증 항목
## 운영 전 권고
```
