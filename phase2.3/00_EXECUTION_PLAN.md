# 실행 계획서 — OpenRouter/Groq 실제 Provider 검증 PoC

## 0. 목적

기존 LiteLLM Governance PoC의 mock 기반 검증을 실제 외부 LLM 호출 기반 검증으로 확장한다.

핵심 질문:

> OpenRouter/Groq 무료 모델을 실제로 호출했을 때도 LiteLLM의 가상키, 모델 제한, 예산 차단, token/spend 리포트가 정상 작동하는가?

## 1. 사전 준비

### 필요한 값

- OpenRouter API Key
- Groq API Key
- 기존 LiteLLM Master Key
- 기존 PoC 프로젝트 경로

권장 프로젝트 경로:

```text
/opt/data/workspace/ssw-litellm-governance-poc/
```

## 2. 구현 단계

### Phase A — 환경 확인

1. 기존 LiteLLM Proxy 실행 여부 확인
2. PostgreSQL 연결 확인
3. 기존 Virtual Key 목록 확인
4. LiteLLM 버전 확인: `1.83.7` 또는 안전 버전

검증 명령:

```bash
curl -s http://localhost:4000/health/liveliness
curl -s http://localhost:4000/v1/models -H "Authorization: Bearer ${LITELLM_MASTER_KEY}"
```

### Phase B — Provider API Key 추가

`.env`에 추가:

```bash
OPENROUTER_API_KEY=...
GROQ_API_KEY=...
```

주의:

- 키 원문을 문서/로그에 저장하지 않는다.
- `.env`는 git에 포함하지 않는다.
- 리포트에는 redacted 형태만 기록한다.

### Phase C — LiteLLM config.yaml 업데이트

내부 alias 모델 추가:

```yaml
- model_name: ssw-free-openrouter
  litellm_params:
    model: openrouter/<현재 사용 가능한 free model>
    api_key: os.environ/OPENROUTER_API_KEY

- model_name: ssw-fast-groq
  litellm_params:
    model: groq/<현재 사용 가능한 groq model>
    api_key: os.environ/GROQ_API_KEY

- model_name: ssw-low-cost-real
  litellm_params:
    model: openrouter/<저가 모델 또는 free model>
    api_key: os.environ/OPENROUTER_API_KEY
```

변경 후 LiteLLM 재시작.

### Phase D — 가상키 allowed_models 업데이트

예시:

- `staff-lee-chat`: `ssw-free-openrouter`, `ssw-low-cost-real`
- `dev-kim-codex`: `gpt-4o-mini`, `ssw-free-openrouter`, `ssw-fast-groq`
- `admin-park-test`: 모든 테스트 모델

Admin API 또는 seed script 수정으로 적용한다.

### Phase E — 실제 호출 스크립트 작성

새 스크립트:

```text
scripts/70_real_provider_test.py
```

기능:

1. OpenRouter alias 호출
2. Groq alias 호출
3. 허용 모델 성공 확인
4. 비허용 모델 차단 확인
5. spend log 조회
6. 낮은 budget 테스트 키 생성 후 차단 확인
7. Markdown 리포트 생성

### Phase F — 리포트 생성

생성 파일:

```text
docs/REAL_PROVIDER_VERIFICATION_REPORT.md
```

포함 항목:

- 실행 시간
- provider/model alias 매핑
- API Key redaction 상태
- 성공 호출 결과
- token usage
- spend
- 차단 이벤트
- 예산 차단 결과
- 남은 리스크

## 3. 검증 명령 예시

```bash
uv run python scripts/70_real_provider_test.py --provider openrouter
uv run python scripts/70_real_provider_test.py --provider groq
uv run python scripts/70_real_provider_test.py --case denied-model
uv run python scripts/70_real_provider_test.py --case budget-exceeded
uv run python scripts/50_export_report.py
```

## 4. 완료 조건

- [ ] OpenRouter 실제 응답 성공
- [ ] Groq 실제 응답 성공 또는 API Key/모델 이슈 명확히 기록
- [ ] token usage 확인
- [ ] spend 기록 확인
- [ ] 가상키별 allowed model 적용
- [ ] 비허용 모델 차단
- [ ] 실제 호출 기반 예산 차단
- [ ] 리포트 생성

## 5. 최종 보고 형식

```md
# Real Provider Validation 결과

## 실행 환경
## Provider 설정
## 테스트 결과 요약
## 실제 호출 결과
## Token/Spend 기록
## 차단 이벤트
## 실패/미검증 항목
## 운영 전 권고
```
