# Claude Code 작업 프롬프트

아래 내용을 Claude Code에 그대로 전달한다.

---

당신은 상상우리 AI 에이전트 프로젝트의 기술 PoC 구현 담당자입니다.

목표는 Google Chat 연동 전 단계에서 **LiteLLM으로 직원별·도구별·모델별 유료 LLM 사용을 기업 예산 범위 안에서 통제할 수 있는지** 검증하는 것입니다.

## 작업 위치

`/opt/data/workspace/ssw-litellm-governance-poc/`

## 반드시 읽을 문서

현재 전달받은 문서 세트:

- `00_CLAUDE_CODE_EXECUTION_PLAN.md`
- `01_PRD.md`
- `02_ACCEPTANCE_CRITERIA.md`
- `03_DEMO_SCENARIO.md`
- `04_SECURITY_AND_LIMITS.md`

## 구현 목표

1. LiteLLM Proxy + PostgreSQL + Redis 기반 PoC 구성
2. 직원/도구별 Virtual Key 발급 자동화
3. 키별 allowed models, max_budget, budget_duration, rpm/tpm 제한 설정
4. 정상 호출, 비허용 모델 차단, 예산 초과 차단을 스크립트로 검증
5. 사용자별·도구별·모델별 사용량 리포트 생성
6. `docs/VERIFICATION_REPORT.md`에 실제 실행 명령과 결과 기록

## 중요한 제약

- Google Chat 연동은 이번 범위에서 제외합니다.
- 실제 유료 API Key가 없으면 mock provider 또는 테스트 가능한 provider 구조로 우선 구현하되, 어떤 부분이 mock인지 명확히 표시하세요.
- 마스터키는 절대 클라이언트 설정에 넣지 않습니다.
- 실제 가상키 원문은 문서에 저장하지 말고 redaction하세요.
- LiteLLM v1.82.7/v1.82.8은 사용하지 말고, `litellm[proxy]>=1.83.10,<2.0.0`을 사용하세요.
- PoC는 설명이 아니라 실제 명령으로 검증되어야 합니다.

## 완료 조건

아래 7개가 확인되어야 완료입니다.

- [ ] LiteLLM Proxy 실행 확인
- [ ] Master Key / Virtual Key 분리 확인
- [ ] 직원/도구별 가상키 생성 확인
- [ ] 허용 모델 호출 성공
- [ ] 비허용 모델 호출 실패
- [ ] 예산 초과 후 호출 차단
- [ ] 사용자·도구·모델별 사용량 리포트 생성

## 최종 보고 형식

```md
# LiteLLM Governance PoC 결과

## 1. 실행 환경

## 2. 생성 파일

## 3. 실행 명령과 결과

## 4. 성공한 검증

## 5. 실패/미검증 항목

## 6. 다음 단계
```

중요: 작업이 막히면 추측하지 말고, 정확한 에러와 대안을 기록하세요.
