# 상상우리 Hermes + LiteLLM AI 업무허브 PoC

> **상태**: Phase 1/2/2.3 + Hermes 1차/2차 검증 완료, Hermes 3차 보완 검증 진행  
> **핵심 구조**: Hermes 업무허브 → LiteLLM Gateway → 모델별 provider/mock upstream  
> **LiteLLM 권장 버전**: `1.83.7` 이상 고정 권장 (`1.82.7`/`1.82.8` 공급망 이슈로 사용 금지)  
> **보안 원칙**: 직원 개인 provider API key 미지급, Hermes에는 LiteLLM virtual key만 주입

이 repo는 상상우리 AI 업무허브에서 **직원별 모델 권한, 예산, 사용량 집계, 우회 차단**이 가능한지 검증하기 위한 PoC입니다. 초기 LiteLLM 거버넌스 검증에서 출발해, 현재는 Hermes profile별 LiteLLM virtual key 연결까지 검증했습니다.

---

## 1. 현재까지의 결론

| 구분 | 결론 |
|---|---|
| Hermes → LiteLLM endpoint 고정 | 가능. Hermes `custom` provider + `base_url`로 LiteLLM `/v1` 경유 확인 |
| 원본 provider key 미잔존 | 가능. Hermes profile에는 LiteLLM virtual key만 저장 |
| 직원 식별 방식 | 파일럿은 `profile-per-key` 방식이 가장 현실적. key 자체가 사용자/역할 식별자 |
| 모델 권한 | LiteLLM virtual key `models` allow-list로 직접 호출 및 Hermes 경유 차단 확인 |
| 예산 차단 | 비용이 기록되는 모델 기준으로 `max_budget` 차단 확인 |
| 사용량 집계 | LiteLLM DB key summary에서 직원/역할별 spend 분리 확인 |
| 운영 한계 | 무료 티어/가격 DB 미포함 모델은 비용 기반 예산 차단이 약함. RPM/TPM 제한 필요 |
| 신규 리스크 | LiteLLM fallback이 allow-list 바깥 모델까지 시도될 수 있어 별도 정책 검증 필요 |

---

## 2. PoC 단계별 요약

| 단계 | 목적 | 결과 | 주요 문서 |
|---|---|:---:|---|
| Phase 1 | LiteLLM virtual key, 모델 allow-list, budget 기본 검증 | ✅ | `docs/VERIFICATION_REPORT.md` |
| Phase 2 | Claude/Codex/Gemini CLI를 LiteLLM으로 라우팅 | ✅ | `docs/VERIFICATION_REPORT.md` |
| Phase 2.3 | 실제 provider/무료 모델/fallback 정책 확장 검토 | 부분 ✅ | `phase2.3/`, `docs/` |
| Hermes 1차 | Hermes가 LiteLLM 호환 endpoint로 라우팅 가능한지 mock gateway로 검증 | ✅ | `docs/hermes-litellm-integration-poc-20260806.md` |
| Hermes 2차 | 실제 LiteLLM proxy + PostgreSQL + Hermes profile별 virtual key 검증 | ✅ | `docs/hermes-litellm-virtual-key-poc-20260806.md` |
| Hermes 3차 | 리뷰 지적 보완: key별 spend, Hermes 경유 차단, fallback, RPM 제한 검증 | ✅/리스크 확인 | `docs/hermes-litellm-phase3-review-fix-poc-20260806.md` |

---

## 3. 최신 검증 판정표

| # | 항목 | 결과 | 비고 |
|---:|---|:---:|---|
| 1 | LiteLLM proxy 실제 기동 | ✅ | DB 연결 상태에서 startup complete |
| 2 | PostgreSQL DB 연결 | ✅ | LiteLLM migration/view 생성 확인 |
| 3 | 직원/역할별 virtual key 발급 | ✅ | lee/kim/park 등 key 생성 |
| 4 | 직접 호출 기준 모델 allow-list | ✅ | 비허용 모델 401 차단 |
| 5 | 직접 호출 기준 예산 초과 차단 | ✅ | `budget_exceeded` 확인 |
| 6 | Hermes profile별 LiteLLM key 연결 | ✅ | 3개 profile 성공 |
| 7 | Hermes profile 내 원본 provider key 미사용 | ✅ | config example 기준 LiteLLM key만 사용 |
| 8 | Hermes 경유 호출의 key별 spend 분리 | ✅ | `docs/USAGE_REPORT.md` key summary에서 spend 분리 확인 |
| 9 | Hermes 경유 비허용 모델 차단 | ✅ | `employee_lee` → `ssw-expensive` 401 확인 |
| 10 | fallback allow-list 우회 여부 | ⚠️ | fallback 대상 모델이 key allow-list 밖이어도 fallback 시도 로그 확인 |
| 11 | 무료/저가 라인 비용 기반 budget 통제 | ⚠️ | 무료 모델은 spend 0 가능. RPM/TPM 필요 |
| 12 | RPM 제한 | ✅ | 단일 proxy 기준 `rpm_limit=1` key 두 번째 호출 429 차단 |

---

## 4. Repo 구조

```text
ssw-litellm-poc/
├── litellm/
│   └── config.yaml                         # LiteLLM 모델/라우터/DB 설정
├── scripts/
│   ├── 20_seed_keys.py                     # virtual key 발급
│   ├── 30_demo_calls.py                    # 허용/차단 데모 호출
│   ├── 40_budget_block_test.py             # 예산 초과 차단 검증
│   ├── 50_export_report.py                 # 사용량 리포트 생성
│   └── 60_cli_integration_test.py          # CLI 연동 검증
├── poc/
│   ├── hermes-litellm-mock-gateway/        # Hermes 1차 mock gateway PoC
│   └── hermes-litellm-virtual-key-policy/  # Hermes 2차 profile/key 예시
├── docs/
│   ├── hermes-litellm-integration-poc-20260806.md
│   ├── hermes-litellm-virtual-key-poc-20260806.md
│   ├── hermes-litellm-phase3-review-fix-poc-20260806.md
│   ├── USAGE_REPORT.md
│   └── VERIFICATION_REPORT.md
├── results/
│   ├── 20260806-hermes-litellm-routing-result.md
│   ├── 20260806-hermes-litellm-virtual-key-result.md
│   └── 20260806-hermes-litellm-phase3-review-fix-result.md
└── tests/
```

---

## 5. 빠른 시작

### 5.1 환경 준비

```bash
cp .env.example .env
# .env 편집: LITELLM_MASTER_KEY, DATABASE_URL, 필요한 provider key
```

Python 의존성:

```bash
uv sync
uv pip install 'litellm[proxy]==1.83.7' prisma tabulate
```

Prisma client 생성:

```bash
DATABASE_URL='postgresql://USER@localhost:5432/litellm_poc'   uv run prisma generate --schema .venv/lib/python3.12/site-packages/litellm/proxy/schema.prisma
```

> Python 버전에 따라 `.venv/lib/python3.11` 또는 `.venv/lib/python3.12` 경로가 달라질 수 있습니다.

### 5.2 LiteLLM proxy 시작

```bash
DATABASE_URL='postgresql://USER@localhost:5432/litellm_poc' LITELLM_MASTER_KEY='sk-...'   uv run litellm --config litellm/config.yaml --port 4100
```

### 5.3 virtual key 발급

```bash
LITELLM_PROXY_URL=http://127.0.0.1:4100 LITELLM_MASTER_KEY='sk-...'   uv run python scripts/20_seed_keys.py
```

생성되는 실제 key 파일은 커밋 금지입니다.

```text
docs/generated_keys.json         # 실제 key 포함, gitignore 대상
docs/generated_keys.redacted.md  # redacted 요약만 커밋 가능
```

### 5.4 정책 검증

```bash
# 허용 모델 성공
LITELLM_PROXY_URL=http://127.0.0.1:4100   uv run python scripts/30_demo_calls.py --user lee --tool chat --case allowed --model ssw-fake

# 비허용 모델 차단
LITELLM_PROXY_URL=http://127.0.0.1:4100   uv run python scripts/30_demo_calls.py --user lee --tool chat --case denied-model

# 예산 초과 차단
LITELLM_PROXY_URL=http://127.0.0.1:4100 LITELLM_MASTER_KEY='sk-...'   uv run python scripts/40_budget_block_test.py

# 사용량 리포트
LITELLM_PROXY_URL=http://127.0.0.1:4100 LITELLM_MASTER_KEY='sk-...'   uv run python scripts/50_export_report.py
```

### 5.5 Hermes profile 연동 예시

```yaml
model:
  provider: custom
  default: ssw-fake
  base_url: http://127.0.0.1:4100/v1
  api_key: <LiteLLM virtual key>
```

격리 profile 예시는 다음 폴더에 있습니다.

```text
poc/hermes-litellm-virtual-key-policy/
```

실행 예:

```bash
HERMES_HOME=$PWD/.hermes-phase2-homes/employee_lee   /opt/hermes/bin/hermes chat   -q 'Respond with exactly OK'   --provider custom   --model ssw-fake   --toolsets safe   --quiet
```

---

## 6. 보안/운영 주의사항

1. **원본 provider API key를 Hermes profile에 넣지 않는다.**  
   Hermes에는 LiteLLM virtual key만 넣는다.

2. **LiteLLM virtual key에는 DB가 필수다.**  
   DB 없이 `/key/generate`는 `DB not connected`로 실패한다.

3. **무료 모델은 budget 통제만으로 부족하다.**  
   무료 티어 또는 가격 DB 미포함 모델은 spend가 0으로 기록될 수 있다. RPM/TPM 제한을 함께 설정해야 한다.

4. **fallback은 별도 allow-list 검증이 필요하다.**  
   Phase 3에서 fallback 대상 모델이 key allow-list 밖이어도 fallback 시도가 발생함을 확인했다. 운영 전 fallback 정책을 보수적으로 설계해야 한다.

5. **Redis는 운영 필수에 가깝다.**  
   단일 proxy에서는 RPM 제한이 동작했지만, 다중 인스턴스 운영에서는 Redis 기반 rate limit 저장소가 필요하다.

6. **시크릿 파일은 커밋 금지다.**

```text
.env
*.env
docs/generated_keys.json
.hermes-phase2-homes/
.pglite-phase2-db/
.postgres-phase2-db/
.s.PGSQL.*
```

---

## 7. 상상우리 파일럿 권장 구조

```text
직원/부서/역할별 Hermes profile
  → 각 profile에 LiteLLM virtual key 1개 연결
  → LiteLLM에서 key별 모델 allow-list / max_budget / rpm_limit / tpm_limit 관리
  → PostgreSQL에 사용량 저장
  → Redis로 RPM/TPM 제한 공유
  → n8n으로 승인/알림/리포트 자동화
```

파일럿 단계 권장:

| 역할 | Hermes profile | LiteLLM key 정책 |
|---|---|---|
| 일반 직원 | `employee_*` | 저가 모델 + 낮은 RPM/TPM + 낮은 월예산 |
| 개발/자동화 담당 | `developer_*` | 코딩 모델 + 중간 예산 + 작업용 rate limit |
| 관리자 | `admin_*` | 고급 모델 접근 + 높은 예산 + 사용량 리포트 권한 |

---

## 8. 다음 단계

| 우선순위 | 항목 | 목적 |
|---:|---|---|
| 1 | Redis 연결 운영 검증 | 다중 인스턴스 RPM/TPM 제한 신뢰성 확보 |
| 2 | fallback 정책 하드닝 | allow-list 우회 가능성 제거 |
| 3 | 실제 provider 저가 유료 모델 연결 | 비용 기반 budget 통제 검증 |
| 4 | n8n 리포트/승인 workflow | 예산 초과, 고급 모델 요청, 월간 사용량 알림 자동화 |
| 5 | 3~5명 파일럿 | 실제 직원 사용 패턴과 비용 추정 |
