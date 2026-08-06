# Hermes-LiteLLM 2차 PoC 최종 보고서 (2026-08-06)

## 1. 목적

상상우리 AI 업무허브 구조에서 Hermes가 LiteLLM을 중앙 게이트웨이로 사용하면서 직원/역할별 가상키, 모델 권한, 예산 차단, 사용량 분리가 가능한지 검증했다.

검증 대상 구조:

```text
직원/역할별 Hermes profile
  → LiteLLM Proxy (/v1, virtual key)
  → LiteLLM mock model upstream
  → LiteLLM DB(PostgreSQL) 사용량/정책 저장
```

실제 외부 LLM provider 비용을 피하기 위해 LiteLLM의 `mock_response` 모델을 우선 사용했다. 원본 provider API key는 Hermes profile에 넣지 않았다.

## 2. 실행 환경

| 항목 | 값 |
|---|---|
| Repo | `charlychoi/ssw-litellm-poc` |
| 작업 경로 | `/opt/data/workspace/ssw-litellm-poc` |
| LiteLLM 버전 | `1.83.7` |
| LiteLLM endpoint | `http://127.0.0.1:4100/v1` |
| DB | 로컬 PostgreSQL 17.10, port `55434` |
| Hermes 실행 | `/opt/hermes/bin/hermes chat`, 격리 `HERMES_HOME` 3개 |
| Provider 비용 | mock upstream 사용, 실제 외부 호출 없음(단 `ssw-expensive` real config는 차단/크레딧 부족 케이스로 관측됨) |

## 3. 블로커와 해결

| 블로커 | 관측 | 해결/판단 |
|---|---|---|
| LiteLLM proxy extra dependency 부족 | `No module named 'backoff'` | `litellm[proxy]==1.83.7` 설치로 해결 |
| DB 없는 virtual key 생성 불가 | `/key/generate` → `DB not connected` | 직원별 key/예산/사용량은 DB 필수임을 확인 |
| Docker PostgreSQL 사용 불가 | Docker daemon 미가동 | 사용자 권한 로컬 PostgreSQL 바이너리 방식으로 우회 |
| PGlite 호환성 문제 | Prisma prepared statement 오류 | LiteLLM/Prisma 검증에는 실제 PostgreSQL 사용 권장 |
| Prisma binary 필요 | `Unable to find Prisma binaries` | `prisma generate --schema .../litellm/proxy/schema.prisma` 실행 후 진행 |

## 4. PostgreSQL + LiteLLM proxy 기동 검증

PostgreSQL 17.10을 사용자 권한으로 기동했다.

```text
listening on IPv4 address "127.0.0.1", port 55434
database system is ready to accept connections
```

LiteLLM proxy는 PostgreSQL에 연결되어 migration/view 생성을 완료했다.

```text
LiteLLM_VerificationTokenView Created!
MonthlyGlobalSpend Created!
Last30dKeysBySpend Created!
Last30dModelsBySpend Created!
MonthlyGlobalSpendPerKey Created!
MonthlyGlobalSpendPerUserPerKey Created!
DailyTagSpend Created!
Last30dTopEndUsersSpend Created!
INFO: Application startup complete.
```

## 5. Virtual key 생성 결과

`scripts/20_seed_keys.py`로 5개 key를 생성했다. 실제 key 값은 `docs/generated_keys.json`에만 생성되며 `.gitignore` 대상이다. repo에는 redacted 요약만 남긴다.

| Alias | User | Team | 허용 모델 | 예산 |
|---|---|---|---|---:|
| `dev-kim-claude` | kim | dev-team | `ssw-dev-sonnet`, `ssw-free-test`, `ssw-fake`, `claude-sonnet` | $5 / 30d |
| `dev-kim-codex` | kim | dev-team | `ssw-dev-gpt`, `ssw-fake`, `gpt-dev` | $5 / 30d |
| `dev-kim-gemini` | kim | dev-team | `ssw-free-test`, `ssw-fake`, `free-test` | $5 / 30d |
| `staff-lee-chat` | lee | staff-team | `ssw-low-cost`, `ssw-fake`, `low-cost` | $1 / 30d |
| `admin-park-test` | park | admin-team | `ssw-dev-sonnet`, `ssw-dev-gpt`, `ssw-free-test`, `ssw-expensive`, `ssw-fake`, `ssw-low-cost` | $10 / 30d |

## 6. 모델 권한 검증

### 6.1 일반 직원 허용 모델 성공

`staff-lee-chat` key로 `ssw-fake` 호출 성공.

```text
SUCCESS
Response: 안녕하세요! 상상우리 AI 게이트웨이 Mock 응답입니다. 거버넌스 PoC 테스트 성공.
Tokens: {'completion_tokens': 20, 'prompt_tokens': 10, 'total_tokens': 30}
```

### 6.2 일반 직원 비허용 모델 차단 성공

`staff-lee-chat` key로 `ssw-expensive` 호출 시 차단.

```json
{
  "error": {
    "message": "key not allowed to access model. This key can only access models=['ssw-low-cost', 'ssw-fake', 'low-cost']. Tried to access ssw-expensive",
    "type": "key_model_access_denied",
    "param": "model",
    "code": "401"
  }
}
```

## 7. 예산 초과 차단 검증

`scripts/40_budget_block_test.py`로 예산 강제 소진 시나리오를 실행했다.

| 단계 | 결과 |
|---|---|
| `max_budget=0.0001` 테스트 key 생성 | 성공 |
| 첫 번째 `ssw-fake` 호출 | 성공 |
| Admin API로 `max_budget=0.0` 업데이트 | 성공 |
| 두 번째 호출 | `budget_exceeded`, HTTP 400으로 차단 |

차단 응답:

```json
{
  "error": {
    "message": "Budget has been exceeded! Current cost: 1.35e-05, Max budget: 0.0",
    "type": "budget_exceeded",
    "param": null,
    "code": "400"
  }
}
```

## 8. Hermes profile별 LiteLLM virtual key 연결 검증

3개의 격리 Hermes home을 만들고 각 profile에 서로 다른 LiteLLM virtual key를 연결했다.

```yaml
model:
  provider: custom
  default: ssw-fake
  base_url: http://127.0.0.1:4100/v1
  api_key: <LiteLLM virtual key>
```

| Hermes profile | LiteLLM key alias | 결과 | session_id |
|---|---|---|---|
| employee_lee | `staff-lee-chat` | 성공 | `20260806_061842_2b8439` |
| developer_kim | `dev-kim-codex` | 성공 | `20260806_061848_e02f33` |
| admin_park | `admin-park-test` | 성공 | `20260806_061854_7bb03d` |

공통 응답:

```text
안녕하세요! 상상우리 AI 게이트웨이 Mock 응답입니다. 거버넌스 PoC 테스트 성공.
```

## 9. 판정

| 검증 항목 | 결과 |
|---|:---:|
| 실제 LiteLLM proxy 기동 | ✅ |
| PostgreSQL DB 연결 | ✅ |
| LiteLLM migration/view 생성 | ✅ |
| 직원/역할별 virtual key 발급 | ✅ |
| virtual key별 모델 allow-list | ✅ |
| 비허용 모델 차단 | ✅ |
| 예산 초과 차단 | ✅ |
| Hermes profile별 LiteLLM key 연결 | ✅ |
| Hermes → LiteLLM → mock model 응답 | ✅ |
| Hermes profile 내 원본 provider key 미사용 | ✅ |

## 10. 결론

2차 PoC의 핵심 기술 검증은 성공했다.

상상우리 AI 업무허브에서 Hermes를 사용자 업무 허브로 두고 LiteLLM을 중앙 LLM Gateway로 배치하면, 파일럿 단계에서 다음 통제가 가능하다.

1. 직원/역할별 LiteLLM virtual key 분리
2. key별 허용 모델 allow-list 집행
3. key별 예산 초과 차단
4. key별 사용량 집계 기반 리포팅
5. Hermes profile별 virtual key 연결을 통한 직원/역할별 경로 고정

운영 조건은 명확하다.

- LiteLLM virtual key/예산/사용량 통제에는 PostgreSQL 같은 DB 연결이 필수다.
- Docker가 없는 환경에서도 사용자 권한 PostgreSQL로 PoC는 가능하지만, 운영은 별도 PostgreSQL 또는 관리형 DB를 권장한다.
- Hermes 기본 요청에는 `user`/`metadata`가 자동 포함되지 않으므로, 직원별 식별은 파일럿 단계에서 profile별 virtual key 분리 방식이 가장 현실적이다.

## 11. 다음 단계 제안

| 단계 | 내용 |
|---|---|
| 3차 실제 provider PoC | OpenRouter/Groq/OpenAI 중 1개 provider를 LiteLLM 뒤에 연결 |
| 파일럿 3~5명 | 실제 직원별 Hermes profile 또는 채널별 profile 구성 |
| 월예산 정책 | 역할별 월 한도, 고급 모델 승인 정책 설계 |
| 관리자 리포트 | LiteLLM DB 기반 사용자/모델/비용 리포트 자동화 |
| n8n 연계 | 예산 초과/고급 모델 요청/외부 발송 승인 workflow 연결 |
