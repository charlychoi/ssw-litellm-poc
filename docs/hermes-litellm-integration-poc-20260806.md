# Hermes-LiteLLM 연동 1차 검증 PoC

## 배경

상상우리 AI 업무허브 제안의 핵심은 직원들이 개별 LLM API key를 갖지 않고, 모든 LLM 요청을 `Hermes → LiteLLM Gateway → LLM Provider` 경로로 통제하는 것이다.

검증해야 할 핵심 질문은 다음이다.

1. Hermes의 LLM endpoint를 LiteLLM으로 고정할 수 있는가?
2. Hermes 운영 환경에서 원본 OpenAI/Anthropic/Gemini API key를 제거할 수 있는가?
3. LiteLLM에서 직원별 사용량·예산·모델 권한을 구분할 수 있는가?

## 1차 검증 범위

이번 1차 PoC는 실제 provider 비용을 쓰지 않기 위해 OpenAI-compatible mock gateway로 진행했다. 목적은 Hermes가 LiteLLM과 같은 `/v1/chat/completions` endpoint로 요청을 보내는지 확인하는 것이다.

```text
Hermes
↓
OpenAI-compatible mock gateway
↓
mock response
```

## Hermes 테스트 설정

```yaml
model:
  default: test-model
  provider: custom
  base_url: http://127.0.0.1:40123/v1
  api_key: test-virtual-key
```

실제 LiteLLM 적용 시에는 `base_url`을 LiteLLM proxy 주소로 바꾸고 `api_key`를 LiteLLM virtual key로 바꾼다.

```yaml
model:
  provider: custom
  default: gpt-4o-mini
  base_url: https://litellm.example.com/v1
  api_key: sk-litellm-virtual-key
```

## 결과 요약

| 검증 항목 | 결과 | 비고 |
|---|---:|---|
| Hermes custom endpoint 사용 | 성공 | `/v1/chat/completions` 호출 확인 |
| Authorization bearer token 전달 | 성공 | LiteLLM virtual key 방식과 호환 가능 |
| streaming 호출 | 확인 | LiteLLM streaming 지원 필요 |
| 기본 호출의 user field | 없음 | 직원별 집계에는 추가 설계 필요 |
| 기본 호출의 metadata | 없음 | 업무유형/직원정보 자동 전달은 미확인 |

## 핵심 판단

Hermes 전체를 LiteLLM 뒤에 두는 1차 구조는 가능하다. 다만 직원별 통제를 위해 Hermes가 공용 key 하나로 모든 요청을 보내면 부족하다.

직원별 통제까지 검증하려면 다음 중 하나가 필요하다.

| 방식 | 설명 | PoC 적합성 |
|---|---|---:|
| 사용자별 Hermes profile | profile별 LiteLLM virtual key 설정 | 3~5명 파일럿에 적합 |
| 공용 Hermes + metadata 주입 | user_id, task_type을 요청에 포함 | 리포트용으로 적합 |
| 중간 업무허브/프록시 | 직원 인증 후 LiteLLM key 동적 선택 | 운영형 구조에 적합 |

## 제안서 반영 문구

> Hermes는 OpenAI-compatible custom endpoint를 통해 LiteLLM Gateway로 LLM 요청을 라우팅할 수 있다. 따라서 Hermes 운영 환경에서 원본 LLM provider API Key를 제거하고 LiteLLM virtual key만 사용하도록 구성하는 1차 통제 구조는 PoC에서 검증 가능하다. 다만 직원별 통제를 위해서는 Hermes가 모든 요청을 하나의 공용 key로 보내는 구조를 피해야 하며, 파일럿 사용자별 Hermes profile 또는 중간 업무허브/프록시를 통해 LiteLLM virtual key를 분리하는 방식을 함께 검증한다.
