# 상상우리 LiteLLM 실제 Provider 검증 PoC 문서 세트

이 문서 세트는 기존 LiteLLM Governance PoC의 후속 작업으로, mock 응답이 아닌 **OpenRouter/Groq 무료 모델 실제 API 호출**을 통해 비용 집계·토큰 기록·예산 차단·CLI 연동 신뢰도를 검증하기 위한 PRD/실행계획서입니다.

## 파일 구성

| 파일 | 용도 |
|---|---|
| `00_EXECUTION_PLAN.md` | Claude Code/Codex 작업용 상세 실행 계획서 |
| `01_PRD_REAL_PROVIDER_VALIDATION.md` | 실제 Provider 검증 PRD |
| `02_ACCEPTANCE_CRITERIA.md` | 검수/성공 기준 |
| `03_TEST_SCENARIOS.md` | Charly 테스트 시나리오 |
| `04_SECURITY_AND_COST_GUARDRAILS.md` | API Key/비용/보안 가드레일 |
| `05_CLAUDE_CODE_PROMPT.md` | Claude Code에 그대로 전달할 작업 프롬프트 |

## 핵심 목적

기존 PoC에서 검증한 가상키·모델 제한·예산 차단 기능을 실제 외부 LLM 호출에도 적용해 검증합니다.

- OpenRouter 무료 모델 실제 호출
- Groq 무료/저가 모델 실제 호출
- LiteLLM token/spend 로그 확인
- 직원/도구/모델별 리포트 반영
- 낮은 예산 설정 후 실제 호출 기반 차단 확인
