# Hermes-LiteLLM 3차 PoC 보고서 — 2차 기술 리뷰 보완 검증 (2026-08-06)

## 1. 목적

2차 PoC 기술 리뷰에서 지적된 공백을 보완했다.

검증 항목:

1. Hermes 3개 profile 호출 후 key별 spend/token 집계가 분리되는지 확인
2. Hermes 경유로 비허용 모델을 호출했을 때 LiteLLM allow-list 차단이 실제 집행되는지 확인
3. LiteLLM fallback이 key allow-list 바깥 모델로 우회될 가능성이 있는지 확인
4. 무료/저가 라인 통제를 위해 RPM 제한이 실제 동작하는지 확인
5. README를 현재 repo 상태에 맞게 최신화

---

## 2. 실행 환경

| 항목 | 값 |
|---|---|
| Repo | `charlychoi/ssw-litellm-poc` |
| LiteLLM | `1.83.7` + proxy extras |
| LiteLLM endpoint | `http://127.0.0.1:4100/v1` |
| DB | 로컬 PostgreSQL 17.10, port `55434` |
| Hermes | `/opt/hermes/bin/hermes` |
| 격리 profile | `.hermes-phase2-homes/{employee_lee,developer_kim,admin_park}` |
| Provider 비용 | mock upstream 중심, 실제 provider 호출 없음 또는 인증 실패 경로 관찰 |

---

## 3. README 최신화

`README.md`를 최신 상태로 재작성했다.

반영 내용:

- Phase 1/2/2.3 + Hermes 1차/2차/3차 흐름 정리
- `profile-per-key` 구조와 운영 의미 설명
- 최신 판정표 추가
- 보안/운영 주의사항 추가
- 무료 모델 budget 한계와 RPM/TPM 필요성 명시
- fallback allow-list 리스크 명시
- 문서/결과 파일 경로 정리
- `litellm[proxy]`, `prisma`, `tabulate` 의존성 반영

또한 `scripts/50_export_report.py`가 `pandas.DataFrame.to_markdown()`을 사용하므로 `tabulate`가 필요하다는 점을 확인했고, `pyproject.toml`에 `tabulate>=0.10.0` 및 `litellm[proxy]==1.83.7`을 반영했다.

---

## 4. 검증 1 — Hermes 3 profile 호출 후 key별 spend 분리

### 실행

각 Hermes profile을 LiteLLM virtual key로 연결한 상태에서 `ssw-fake`를 호출했다.

```bash
HERMES_HOME=.hermes-phase2-homes/employee_lee /opt/hermes/bin/hermes chat   -q 'Respond with exactly PHASE3_SPEND_CHECK_OK'   --provider custom --model ssw-fake --toolsets safe --quiet
```

동일 방식으로 `developer_kim`, `admin_park` profile도 실행했다.

### 결과

| Hermes profile | 결과 | session_id |
|---|---|---|
| `employee_lee` | 성공 | `20260806_083700_9a5c54` |
| `developer_kim` | 성공 | `20260806_083705_8cc671` |
| `admin_park` | 성공 | `20260806_083710_21fa40` |

공통 응답:

```text
안녕하세요! 상상우리 AI 게이트웨이 Mock 응답입니다. 거버넌스 PoC 테스트 성공.
```

이후 `scripts/50_export_report.py`를 실행했다.

```bash
LITELLM_PROXY_URL=http://127.0.0.1:4100 LITELLM_MASTER_KEY=<master-key>   uv run python scripts/50_export_report.py
```

### key summary 결과

`docs/USAGE_REPORT.md`에서 key별 spend가 다음과 같이 분리되어 기록되었다.

| key_alias | user_id | team_id | tool | max_budget | spend |
|---|---|---|---|---:|---:|
| `admin-park-test` | park | admin-team | admin-api | 10 | $0.000356 |
| `staff-lee-chat` | lee | staff-team | chat | 1 | $0.000370 |
| `dev-kim-gemini` | kim | dev-team | gemini-cli | 5 | $0.000000 |
| `dev-kim-codex` | kim | dev-team | codex-cli | 5 | $0.000357 |
| `dev-kim-claude` | kim | dev-team | claude-code | 5 | $0.000000 |

Overall summary:

| 항목 | 값 |
|---|---:|
| Total calls | 11 |
| Total cost | $0.001097 |

사용자별 집계:

| user_id | calls | total_cost |
|---|---:|---:|
| lee | 4 | $0.000370 |
| kim | 2 | $0.000357 |
| park | 3 | $0.000356 |
| budget-test-user | 2 | $0.000013 |

### 판단

**보완 검증 성공.**

2차 보고서에서 증거가 부족했던 “key별 사용량 집계 기반 리포팅” 항목은 LiteLLM key summary 기준으로 확인되었다.

단, `/spend/logs` 기반 상세 로그의 `api_key_alias` 필드는 비어 있어 `Cost by Key / Tool` 표에는 alias가 나오지 않았다. 운영 리포트에서는 key list summary의 `spend` 또는 DB/API 조합을 기준으로 집계하는 방식이 필요하다.

---

## 5. 검증 2 — Hermes 경유 비허용 모델 차단

### 실행

`employee_lee` profile은 `staff-lee-chat` key를 사용하며 허용 모델은 다음이다.

```text
ssw-low-cost, ssw-fake, low-cost
```

해당 profile로 비허용 모델 `ssw-expensive`를 직접 지정했다.

```bash
HERMES_HOME=.hermes-phase2-homes/employee_lee /opt/hermes/bin/hermes chat   -q 'Respond with exactly SHOULD_NOT_SUCCEED'   --provider custom --model ssw-expensive --toolsets safe --quiet
```

### 결과

```text
HTTP 401: key not allowed to access model. This key can only access models=['ssw-low-cost', 'ssw-fake', 'low-cost']. Tried to access ssw-expensive

session_id: 20260806_083715_c2a377
```

### 판단

**보완 검증 성공.**

LiteLLM allow-list 차단이 Hermes 경유 경로에서도 실제로 집행되었다. 또한 이번 단발 CLI 실행에서는 장시간 재시도 루프 없이 사용자에게 401 메시지가 바로 표시되었다.

운영 UX 관점에서는 이 메시지를 “권한 없는 모델입니다. 관리자에게 승인 요청하세요.” 같은 친화적 안내로 감싸는 개선이 필요하다.

---

## 6. 검증 3 — fallback allow-list 우회 가능성

### 목적

기술 리뷰에서 제기된 질문:

> fallback 대상 모델이 해당 key의 allow-list에 없어도 실행 또는 시도되는가?

### 실행

`phase3-fallback-primary-only` key를 생성했다.

| 항목 | 값 |
|---|---|
| key_alias | `phase3-fallback-primary-only` |
| user_id | `fallback-test-user` |
| 허용 모델 | `ssw-free-openrouter` only |
| fallback 설정 | `ssw-free-openrouter` → `ssw-low-cost-real` |

`ssw-low-cost-real`은 이 key의 allow-list에 넣지 않았다.

### 결과

호출 결과는 HTTP 401이었으나, 오류 메시지에 fallback 대상 `ssw-low-cost-real`이 실제로 시도되었음이 나타났다.

```text
Received Model Group=ssw-free-openrouter
Available Model Group Fallbacks=['ssw-low-cost-real']
Error doing the fallback: ... Received Model Group=ssw-low-cost-real ...
```

핵심은 `key_model_access_denied`가 아니라 provider 인증 실패가 반환되었다는 점이다. 즉 fallback 대상이 key allow-list에 없더라도 LiteLLM router가 fallback 경로를 시도한 것으로 관찰된다.

### 판단

**리스크 확인.**

이번 환경에서는 provider 인증 실패 때문에 실제 성공 응답까지 이어지지는 않았지만, fallback 대상 모델이 allow-list 밖이어도 fallback 시도가 발생했다. 운영에서는 fallback 대상을 각 key의 allow-list에 포함된 모델로만 제한하거나, 역할별 fallback config를 분리해야 한다.

권고:

1. 일반 직원 key에는 fallback 대상까지 모두 명시적으로 저가/허용 모델만 배치
2. 고급 모델 fallback은 관리자/개발자 key에만 허용
3. 가능하면 모델 그룹별 fallback을 역할별로 분리
4. 실제 provider 연결 전 fallback 우회 테스트를 CI/운영 체크리스트에 포함

---

## 7. 검증 4 — RPM 제한

### 목적

무료/저가 모델은 spend가 0으로 기록될 수 있으므로 비용 기반 `max_budget`만으로는 통제 공백이 생긴다. 따라서 RPM/TPM 제한이 실제 차단 수단으로 쓸 수 있는지 확인했다.

### 실행

`phase3-rpm-limit-1` key를 생성했다.

| 항목 | 값 |
|---|---|
| key_alias | `phase3-rpm-limit-1` |
| user_id | `rpm-test-user` |
| 허용 모델 | `ssw-fake` |
| rpm_limit | 1 |

같은 key로 연속 3회 호출했다.

### 결과

| 호출 | HTTP | 결과 |
|---:|---:|---|
| 1 | 200 | 성공 |
| 2 | 429 | Rate limit exceeded |
| 3 | 429 | Rate limit exceeded |

차단 메시지:

```text
Rate limit exceeded for api_key: <hash>. Limit type: requests. Current limit: 1, Remaining: 0.
```

### 판단

**단일 LiteLLM proxy 기준 RPM 제한은 성공.**

무료/저가 모델의 비용 기반 budget 공백은 RPM/TPM 제한으로 보완할 수 있다. 다만 다중 proxy/운영 환경에서는 rate limit 상태 공유를 위해 Redis 연결을 필수 구성으로 보는 것이 안전하다.

---

## 8. 수정된 판정표

| # | 항목 | 결과 |
|---:|---|:---:|
| 1 | 실제 LiteLLM proxy 기동 | 통과 |
| 2 | PostgreSQL DB 연결 | 통과 |
| 3 | LiteLLM migration/view 생성 | 통과 |
| 4 | 직원/역할별 virtual key 발급 | 통과 |
| 5 | virtual key별 모델 allow-list | 통과 |
| 6 | 비허용 모델 차단 — 직접 호출 | 통과 |
| 7 | 예산 초과 차단 — 비용 기록 모델 기준 | 통과 |
| 8 | Hermes profile별 LiteLLM key 연결 | 통과 |
| 9 | Hermes → LiteLLM → mock model 응답 | 통과 |
| 10 | Hermes profile 내 원본 provider key 미사용 | 통과 |
| 11 | Hermes 경유 호출의 key별 사용량 분리 집계 | 통과 |
| 12 | Hermes 경유 비허용 모델 차단 | 통과 |
| 13 | 무료/저가 모델 RPM 제한 | 통과 — 단일 proxy 기준 |
| 14 | fallback allow-list 우회 방지 | 리스크 확인, 운영 전 하드닝 필요 |
| 15 | 무료 티어 비용 기반 budget 차단 | 한계 존재, RPM/TPM 병행 필요 |

---

## 9. 최종 결론

3차 보완 검증 결과, 2차 기술 리뷰에서 지적한 핵심 공백 두 가지는 해소되었다.

1. **Hermes 경유 호출도 key별 spend summary로 분리 집계됨을 확인했다.**
2. **Hermes 경유 비허용 모델 호출도 LiteLLM allow-list로 401 차단됨을 확인했다.**

동시에 운영 전 반드시 반영해야 할 리스크도 명확해졌다.

1. **fallback은 allow-list 밖 모델까지 시도될 수 있다.** 따라서 fallback 정책은 역할별로 보수적으로 분리해야 한다.
2. **무료/저가 모델은 비용 기반 budget 통제만으로 부족하다.** RPM/TPM 제한을 함께 적용해야 한다.
3. **운영 환경에서는 PostgreSQL + Redis 조합이 권장된다.** PostgreSQL은 virtual key/사용량/예산 저장소, Redis는 rate limit 상태 공유 저장소로 본다.

상상우리 파일럿 제안서에는 다음 문장을 사용할 수 있다.

> Hermes profile별 LiteLLM virtual key 방식은 직원별 사용량 귀속과 모델 권한 통제를 실제로 구현할 수 있다. 3차 보완 검증에서 Hermes 경유 비허용 모델 차단과 key별 spend 분리 집계가 확인되었다. 단, fallback 정책과 무료/저가 모델의 RPM/TPM 제한은 운영 전 필수 하드닝 항목이다.

---

## 10. 다음 단계

| 우선순위 | 항목 | 설명 |
|---:|---|---|
| 1 | fallback 정책 하드닝 | 역할별 fallback 모델을 allow-list 내부로 제한 |
| 2 | Redis 연결 검증 | 다중 LiteLLM proxy에서도 RPM/TPM 제한 공유 확인 |
| 3 | 실제 저가 유료 provider 연결 | 비용 기반 budget이 실제 가격 모델에서 동작하는지 확인 |
| 4 | n8n 승인 workflow | 고급 모델 요청/예산 초과/월간 리포트 자동화 |
| 5 | 파일럿 3~5명 운영 | 실제 업무 패턴, 비용, 문의 유형 수집 |
