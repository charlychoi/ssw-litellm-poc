# LiteLLM Usage Report

Generated: 2026-07-01 21:42:18

Proxy: http://localhost:4000

---

## Virtual Keys Summary

| key_alias       | user_id   | team_id    | tool        |   max_budget | spend     |
|:----------------|:----------|:-----------|:------------|-------------:|:----------|
| admin-park-test | park      | admin-team | admin-api   |           10 | $0.000000 |
| staff-lee-chat  | lee       | staff-team | chat        |            1 | $0.000000 |
| dev-kim-gemini  | kim       | dev-team   | gemini-cli  |            5 | $0.000000 |
| dev-kim-codex   | kim       | dev-team   | codex-cli   |            5 | $0.000000 |
| dev-kim-claude  | kim       | dev-team   | claude-code |            5 | $0.000013 |


## Overall Summary

- **Total calls**: 6

- **Total cost**: $0.000027


## Cost by User

| user_id          |   calls | total_cost   |
|:-----------------|--------:|:-------------|
| budget-test-user |       2 | $0.000013    |
| kim              |       3 | $0.000013    |
| lee              |       1 | $0.000000    |


## Cost by Key / Tool

| key_alias   |   calls | total_cost   |
|:------------|--------:|:-------------|
|             |       6 | $0.000027    |


## Cost by Model

| model                              |   calls | total_cost   |   tokens |
|:-----------------------------------|--------:|:-------------|---------:|
| openai/gpt-4o-mini                 |       2 | $0.000027    |       60 |
| anthropic/claude-3-5-sonnet-latest |       1 | $0.000000    |        0 |
| openai/fake                        |       1 | $0.000000    |        0 |
| ssw-expensive                      |       1 | $0.000000    |        0 |
| ssw-fake                           |       1 | $0.000000    |        0 |


## Blocked Events

| request_id                           | user_id          | model                              | status   | startTime                   |
|:-------------------------------------|:-----------------|:-----------------------------------|:---------|:----------------------------|
| 135f9cc9-fda1-4aec-9242-c0d4b8c62737 | budget-test-user | ssw-fake                           | failure  | 2026-07-01T12:37:40.151000Z |
| a3990d56-c147-4954-8612-41fb47e11016 | lee              | ssw-expensive                      | failure  | 2026-07-01T12:36:56.069000Z |
| af9a8203-4006-4b8f-8323-2e8c01344dad | kim              | openai/fake                        | failure  | 2026-07-01T12:35:42.636000Z |
| 0e87b323-3bfc-4143-9251-d1a707797178 | kim              | anthropic/claude-3-5-sonnet-latest | failure  | 2026-07-01T12:34:50.816000Z |

