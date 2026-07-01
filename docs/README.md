# 상상우리 LiteLLM 비용 거버넌스 PoC 문서 세트

이 폴더는 Claude Code가 실제 PoC를 구현할 수 있도록 만든 실행 계획서/PRD 세트다.

## 파일 구성

| 파일 | 용도 |
|---|---|
| `00_CLAUDE_CODE_EXECUTION_PLAN.md` | Claude Code용 상세 실행 계획서 |
| `01_PRD.md` | 제품 요구사항 문서 |
| `02_ACCEPTANCE_CRITERIA.md` | 성공/검수 기준 |
| `03_DEMO_SCENARIO.md` | 의사결정자용 데모 흐름 |
| `04_SECURITY_AND_LIMITS.md` | 보안/한계/운영 리스크 |
| `05_CLAUDE_CODE_PROMPT.md` | Claude Code에 그대로 넣을 작업 프롬프트 |

## 핵심 목적

Google Chat 연동 전에, LiteLLM으로 다음이 가능한지 검증한다.

1. 직원/도구별 가상키 발급
2. 모델 접근 제한
3. 예산 초과 차단
4. 사용량 리포트
5. 관리자 관점의 비용 통제 가능성 데모

## 권장 사용법

Claude Code에게 `05_CLAUDE_CODE_PROMPT.md`를 먼저 전달하고, 나머지 문서 세트를 함께 참고하게 한다.

실제 구현 프로젝트 권장 위치:

```text
/opt/data/workspace/ssw-litellm-governance-poc/
```
