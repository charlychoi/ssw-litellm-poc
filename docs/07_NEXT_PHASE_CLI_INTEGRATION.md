# Next Phase — Claude Code / Codex / Gemini CLI 실제 연동 검증

이 문서는 이번 PoC 이후 단계에서 검증할 항목이다. 이번 1차 PoC 범위는 LiteLLM 비용 통제 자체이며, CLI별 실제 연동은 다음 단계로 둔다.

## 1. Claude Code 연동 검증

### 가설

Claude Code가 Anthropic-compatible base URL과 auth token을 지원하면 LiteLLM Gateway를 경유할 수 있다.

### 검증 항목

- `ANTHROPIC_BASE_URL` 적용 여부
- `ANTHROPIC_AUTH_TOKEN` 또는 해당 버전의 인증 환경변수 적용 여부
- Claude Code 로그/요청이 LiteLLM에 기록되는지
- 허용 모델/비허용 모델 정책이 적용되는지

### 성공 기준

- Claude Code에서 실행한 요청이 LiteLLM usage log에 `dev-kim-claude`로 기록된다.

---

## 2. Codex CLI 연동 검증

### 가설

Codex CLI는 OpenAI-compatible custom provider + Responses API 설정으로 LiteLLM Gateway를 경유할 수 있다.

### 검증 항목

- custom provider base_url 적용 여부
- 내장 openai provider 우회 버그 회피
- ChatGPT OAuth 세션 logout 필요 여부
- Responses API endpoint 호환성
- LiteLLM config의 `mode: responses` 필요 여부

### 성공 기준

- Codex CLI 요청이 LiteLLM usage log에 `dev-kim-codex`로 기록된다.

---

## 3. Gemini CLI 연동 검증

### 가설

Gemini CLI의 base URL 환경변수를 통해 LiteLLM Gateway 경유가 가능할 수 있다.

### 검증 항목

- base URL 환경변수 실제 지원 여부
- Google 로그인 캐시가 있으면 우회하는지
- sandbox 모드에서 env가 전달되는지
- Gemini 모델명이 LiteLLM alias로 매핑되는지

### 성공 기준

- Gemini CLI 요청이 LiteLLM usage log에 `dev-kim-gemini`로 기록된다.

---

## 공통 검증 절차

각 CLI별로 다음을 수행한다.

1. 회사 가상키 설정
2. 간단한 프롬프트 실행
3. LiteLLM 로그 확인
4. 모델 제한 테스트
5. 예산 초과 테스트
6. 우회 가능성 기록

## 최종 판단 기준

CLI 연동은 “응답이 나온다”가 성공이 아니다. 반드시 다음이 확인되어야 한다.

> 해당 요청이 LiteLLM 로그에 의도한 가상키 alias로 기록되어야 성공이다.
