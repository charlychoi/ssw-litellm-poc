# 상상우리 LiteLLM 비용 거버넌스 PoC — Claude Code 실행 계획서

## 0. 목적

이 PoC의 목적은 Google Chat 연동 전에, **LiteLLM으로 직원별·도구별·모델별 유료 LLM 사용을 기업 예산 범위 안에서 실제로 통제할 수 있는지**를 검증하는 것이다.

검증 대상은 UI 완성도가 아니라 다음 핵심 기술 이슈다.

1. 직원/도구별 가상키 발급 및 식별
2. 가상키별 모델 접근 제한
3. 가상키별 예산 한도 설정 및 초과 차단
4. Claude Code / OpenAI-compatible 클라이언트에서 LiteLLM 경유 호출
5. 호출 로그에서 사용자·도구·모델·비용 추적
6. 관리자 관점의 최소 대시보드/리포트
7. 우회 호출과 개인 구독 사용은 기술 통제 밖이라는 경계 명확화

---

## 1. Claude Code에게 주는 작업 지시

Claude Code는 이 문서를 기준으로 `/opt/data/workspace/ssw-litellm-governance-poc/` 프로젝트를 생성한다.

### 핵심 원칙

- **실제 동작하는 PoC**를 만든다.
- Google Chat 연동은 제외한다.
- 우선 LiteLLM Proxy + PostgreSQL + Redis 기반으로 로컬/VPS에서 검증한다.
- 실제 유료 API Key가 없더라도, 최소한 mock provider 또는 free/openrouter/groq 등 선택 가능한 provider 구조를 둔다.
- 예산 초과, 모델 제한, 로그 추적은 테스트로 검증한다.
- 모든 결과는 `docs/VERIFICATION_REPORT.md`에 명령어와 출력 근거를 남긴다.

---

## 2. 권장 기술 스택

| 영역 | 선택 |
|---|---|
| Gateway | LiteLLM Proxy |
| DB | PostgreSQL |
| Realtime / counter | Redis |
| Admin API wrapper | FastAPI |
| PoC dashboard | Streamlit 또는 FastAPI HTML 단일 페이지 |
| Test | pytest |
| Script | Python 3.11+ 권장, 현재 VPS는 Python 3.13 가능 |
| Env/package | `uv` 사용 권장 |
| Container | Docker Compose 가능하면 우선, 불가하면 local process fallback |

---

## 3. 프로젝트 구조

```text
ssw-litellm-governance-poc/
├── README.md
├── .env.example
├── docker-compose.yml
├── litellm/
│   ├── config.yaml
│   └── seed_virtual_keys.md
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── services/
│   │   ├── litellm_admin.py
│   │   ├── budget_policy.py
│   │   ├── usage_report.py
│   │   └── demo_client.py
│   └── routers/
│       ├── health.py
│       ├── admin_keys.py
│       ├── demo_chat.py
│       └── reports.py
├── scripts/
│   ├── 00_check_env.sh
│   ├── 10_start_stack.sh
│   ├── 20_seed_keys.py
│   ├── 30_demo_calls.py
│   ├── 40_budget_block_test.py
│   └── 50_export_report.py
├── tests/
│   ├── test_budget_policy.py
│   ├── test_key_policy.py
│   ├── test_demo_client.py
│   └── test_report_parser.py
└── docs/
    ├── PRD.md
    ├── ACCEPTANCE_CRITERIA.md
    ├── SECURITY_AND_LIMITS.md
    ├── DEMO_SCENARIO.md
    └── VERIFICATION_REPORT.md
```

---

## 4. PoC 범위

### In Scope

- LiteLLM Proxy 실행
- PostgreSQL/Redis 연결
- 마스터키와 가상키 분리
- 직원 3명 × 도구 3종 예시 키 발급
- 도구별 모델 권한 제한
- 월 예산/일 예산/분당 요청 제한 검증
- 정상 호출/차단 호출 데모
- 사용량 리포트 생성
- 관리자용 최소 페이지 또는 CLI 리포트

### Out of Scope

- Google Chat App 연동
- 사내 SSO 연동
- 실제 인사 DB 연동
- 완성형 관리자 대시보드
- 결제/회계 시스템 연동
- 개인 ChatGPT/Claude 구독 통제
- 운영 배포 자동화

---

## 5. 데모 사용자/도구 정책

PoC에는 아래 더미 계정을 만든다.

| 사용자 | 역할 | 도구 | 키 alias | 허용 모델 | 예산 |
|---|---|---|---|---|---:|
| kim | 개발자 | Claude Code | `dev-kim-claude` | `claude-sonnet` 계열 | $5 |
| kim | 개발자 | Codex CLI | `dev-kim-codex` | `gpt` 계열 | $5 |
| kim | 개발자 | Gemini CLI | `dev-kim-gemini` | `gemini` 또는 alias | $5 |
| lee | 일반 직원 | Chat/API | `staff-lee-chat` | 저가 모델만 | $1 |
| park | 관리자 | Admin/API | `admin-park-test` | 전체 테스트 모델 | $10 |

실제 모델명은 LiteLLM config에서 현재 연결 가능한 provider 기준으로 치환한다. 단, 문서에는 논리 모델명과 실제 provider 모델명을 분리해 기록한다.

---

## 6. 구현 단계

### Phase 1 — Skeleton

1. 프로젝트 폴더 생성
2. `README.md`, `.env.example`, `docker-compose.yml` 생성
3. FastAPI skeleton 생성
4. `uv` 환경 구성
5. 기본 테스트 1개 통과

검증:

```bash
uv run pytest
uv run python -m app.main --help || true
```

### Phase 2 — LiteLLM Proxy 실행

1. `litellm/config.yaml` 작성
2. PostgreSQL, Redis 포함 compose 구성
3. LiteLLM Proxy 기동
4. `/health` 또는 `/models` 호출 확인

검증:

```bash
curl -s http://localhost:4000/health
curl -s http://localhost:4000/v1/models -H "Authorization: Bearer ${MASTER_KEY}"
```

### Phase 3 — 가상키 발급 자동화

1. `scripts/20_seed_keys.py` 구현
2. LiteLLM Admin API로 키 생성
3. alias, team_id, models, budget, rpm/tpm 설정
4. 생성 결과를 `docs/generated_keys.redacted.md`에 redacted 저장

검증:

```bash
uv run python scripts/20_seed_keys.py
```

성공 기준:

- 실제 key 값은 전체 저장하지 않는다.
- alias, team_id, budget, allowed models는 저장한다.

### Phase 4 — 정상 호출/모델 제한 검증

1. `scripts/30_demo_calls.py` 구현
2. 각 키로 허용 모델 호출
3. 허용되지 않은 모델 호출 시 실패 확인
4. 응답/오류를 `docs/VERIFICATION_REPORT.md`에 기록

검증:

```bash
uv run python scripts/30_demo_calls.py --case allowed
uv run python scripts/30_demo_calls.py --case denied-model
```

### Phase 5 — 예산 초과 차단 검증

1. 테스트용 키에 아주 낮은 예산 설정
2. 반복 호출로 예산 초과 유도
3. LiteLLM이 차단하는지 확인
4. 차단 상태/응답코드/로그 기록

검증:

```bash
uv run python scripts/40_budget_block_test.py
```

성공 기준:

- 예산 초과 후 추가 호출이 실패해야 한다.
- 실패 사유가 로그 또는 API 응답에서 확인 가능해야 한다.

### Phase 6 — 리포트/대시보드

1. 사용량 조회 API 또는 DB 조회 구현
2. 사용자별/도구별/모델별 비용 요약
3. Markdown 리포트 export
4. 가능하면 Streamlit/FastAPI HTML 대시보드 추가

검증:

```bash
uv run python scripts/50_export_report.py
```

---

## 7. 필수 산출물

Claude Code는 완료 시 아래 산출물을 반드시 남긴다.

| 산출물 | 위치 |
|---|---|
| 실행 가능한 PoC 코드 | `/opt/data/workspace/ssw-litellm-governance-poc/` |
| 환경변수 샘플 | `.env.example` |
| LiteLLM 설정 | `litellm/config.yaml` |
| 가상키 발급 스크립트 | `scripts/20_seed_keys.py` |
| 정상/실패 호출 스크립트 | `scripts/30_demo_calls.py` |
| 예산 차단 테스트 | `scripts/40_budget_block_test.py` |
| 사용량 리포트 | `docs/VERIFICATION_REPORT.md` |
| PRD | `docs/PRD.md` |
| 데모 시나리오 | `docs/DEMO_SCENARIO.md` |

---

## 8. 검증 기준 요약

PoC는 아래 7개가 확인되면 성공이다.

- [ ] LiteLLM Proxy가 실행된다.
- [ ] 마스터키와 가상키가 분리된다.
- [ ] 직원/도구별 가상키가 생성된다.
- [ ] 허용 모델 호출은 성공한다.
- [ ] 비허용 모델 호출은 실패한다.
- [ ] 예산 초과 후 호출이 차단된다.
- [ ] 사용량 리포트에서 직원·도구·모델·비용이 구분된다.

---

## 9. 중요 리스크

1. LiteLLM 버전 고정 필요 — v1.82.7/v1.82.8 사용 금지.
2. 실제 provider API key 없이는 LLM end-to-end 호출이 제한될 수 있다.
3. Claude Code/Codex/Gemini CLI의 base URL 우회 여부는 별도 실기 검증 필요.
4. 개인 구독 앱 사용은 LiteLLM으로 통제 불가.
5. 운영 도입 전에는 인증/권한/로그 보존/키 로테이션 정책이 필요하다.

---

## 10. Claude Code 최종 보고 형식

Claude Code는 작업 완료 후 다음 형식으로 보고한다.

```md
# LiteLLM Governance PoC 작업 결과

## 실행한 명령
- ...

## 생성/수정 파일
- ...

## 검증 결과
| 항목 | 결과 | 근거 |
|---|---|---|

## 실패/미검증 항목
- ...

## 다음 단계
- ...
```
