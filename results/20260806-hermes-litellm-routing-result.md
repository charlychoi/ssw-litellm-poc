# Hermes-LiteLLM 라우팅 1차 PoC 결과 — 2026-08-06

## 목적

상상우리 AI 업무허브 제안에서 핵심 통제 경로인 `Hermes → LiteLLM Gateway → LLM Provider`가 기술적으로 가능한지 1차 확인한다.

## 테스트 환경

- Hermes Agent: v0.20.0
- 테스트 방식: LiteLLM과 동일한 OpenAI-compatible mock gateway 사용
- Gateway endpoint: `http://127.0.0.1:40123/v1/chat/completions`
- Hermes provider: `custom`
- API key: 테스트용 virtual key 문자열만 사용

## 실행 결과

Hermes 실행 결과:

```text
MOCK_LITELLM_ROUTE_OK

session_id: 20260806_053605_78a8f6
```

mock gateway에 기록된 핵심 요청 요약:

```json
{
  "path": "/v1/chat/completions",
  "authorization": "Bearer test-virtual-key...REDACTED",
  "model": "test-model",
  "stream": true,
  "user_field": null,
  "metadata": null,
  "extra_body_keys": [
    "max_tokens",
    "stream_options"
  ]
}
```

## 확인된 점

1. Hermes는 `custom` provider와 `base_url` 설정을 통해 OpenAI-compatible endpoint로 요청을 보낼 수 있다.
2. 따라서 LiteLLM proxy의 `/v1` endpoint를 Hermes의 LLM endpoint로 지정하는 1차 구조는 가능하다.
3. Hermes는 Authorization header에 bearer token을 전달한다. 이 값은 LiteLLM virtual key로 대체 가능하다.
4. Hermes는 streaming chat completion 방식으로 호출한다.

## 발견된 핵심 리스크

기본 호출에는 `user` 또는 `metadata` 필드가 포함되지 않았다. 따라서 Hermes가 하나의 공용 LiteLLM virtual key만 사용하면 LiteLLM은 사용량을 “Hermes 전체 합계”로만 집계할 가능성이 높다.

## 판단

- **1차 통제 구조:** 가능. Hermes 전체를 LiteLLM 뒤에 두고 원본 provider key를 Hermes 환경에서 제거하는 구성은 PoC 가능성이 높다.
- **직원별 통제:** 추가 설계 필요. 직원별 예산·모델 allow-list·차단을 하려면 사용자별 LiteLLM virtual key 분리, Hermes profile 분리, 또는 중간 업무허브/프록시가 필요하다.

## 다음 검증 단계

1. 실제 LiteLLM proxy를 띄운다.
2. 파일럿 사용자 3~5명용 virtual key를 생성한다.
3. key별 모델 allow-list와 budget을 설정한다.
4. Hermes profile별로 서로 다른 LiteLLM key를 연결한다.
5. 정상 호출, 금지 모델 호출, 예산 초과 호출을 테스트한다.
6. LiteLLM 로그에서 key별 사용량이 분리되는지 확인한다.
