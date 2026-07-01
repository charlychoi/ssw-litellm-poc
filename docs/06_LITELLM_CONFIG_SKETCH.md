# LiteLLM Config Sketch — PoC 참고용

> 이 파일은 Claude Code 구현자가 시작점으로 참고할 설정 스케치다. 실제 provider key와 모델명은 환경에 맞게 조정한다.

## config.yaml 예시

```yaml
model_list:
  - model_name: ssw-low-cost
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY

  - model_name: ssw-dev-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-latest
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: ssw-dev-gpt
    model_info:
      mode: responses
    litellm_params:
      model: openai/gpt-4.1
      api_key: os.environ/OPENAI_API_KEY

  - model_name: ssw-free-test
    litellm_params:
      model: openrouter/google/gemini-2.0-flash-exp:free
      api_key: os.environ/OPENROUTER_API_KEY

litellm_settings:
  drop_params: true
  set_verbose: false

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
  store_model_in_db: true

router_settings:
  model_group_alias:
    claude-sonnet: ssw-dev-sonnet
    gpt-dev: ssw-dev-gpt
    low-cost: ssw-low-cost
```

## Virtual Key 발급 payload 예시

```json
{
  "key_alias": "dev-kim-claude",
  "team_id": "dev-team",
  "user_id": "kim",
  "models": ["claude-sonnet", "ssw-dev-sonnet"],
  "budget_duration": "30d",
  "max_budget": 5,
  "tpm_limit": 80000,
  "rpm_limit": 60,
  "metadata": {
    "tool": "claude-code",
    "role": "developer",
    "project": "ssw-ai-agent-poc"
  }
}
```

## 주의

- 실제 LiteLLM 버전에 따라 Admin API payload 필드명이 다를 수 있으므로 구현 시 공식 문서/현재 설치 버전을 확인한다.
- PoC에서는 모델명을 논리명으로 감싸고, 실제 provider 모델명은 config에서만 관리하는 방식을 권장한다.
