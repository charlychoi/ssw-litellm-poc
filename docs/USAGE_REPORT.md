# LiteLLM Usage Report

Generated: 2026-08-06 08:37:19

Proxy: http://127.0.0.1:4100

---

## Virtual Keys Summary

| key_alias       | user_id   | team_id    | tool        |   max_budget | spend     |
|:----------------|:----------|:-----------|:------------|-------------:|:----------|
| admin-park-test | park      | admin-team | admin-api   |           10 | $0.000356 |
| staff-lee-chat  | lee       | staff-team | chat        |            1 | $0.000370 |
| dev-kim-gemini  | kim       | dev-team   | gemini-cli  |            5 | $0.000000 |
| dev-kim-codex   | kim       | dev-team   | codex-cli   |            5 | $0.000357 |
| dev-kim-claude  | kim       | dev-team   | claude-code |            5 | $0.000000 |


## Overall Summary

- **Total calls**: 11

- **Total cost**: $0.001097


## Cost by User

| user_id          |   calls | total_cost   |
|:-----------------|--------:|:-------------|
| lee              |       4 | $0.000370    |
| kim              |       2 | $0.000357    |
| park             |       3 | $0.000356    |
| budget-test-user |       2 | $0.000013    |


## Cost by Key / Tool

| key_alias   |   calls | total_cost   |
|:------------|--------:|:-------------|
|             |      11 | $0.001097    |


## Cost by Model

| model              |   calls | total_cost   |   tokens |
|:-------------------|--------:|:-------------|---------:|
| openai/gpt-4o-mini |       8 | $0.001097    |     6490 |
| openai/gpt-4o      |       1 | $0.000000    |        0 |
| ssw-expensive      |       1 | $0.000000    |        0 |
| ssw-fake           |       1 | $0.000000    |        0 |


## Blocked Events

| request_id                           | user_id          | model         | status   | startTime                   |
|:-------------------------------------|:-----------------|:--------------|:---------|:----------------------------|
| 96199cc3-6dcd-477f-b022-42b280c8a357 | park             | openai/gpt-4o | failure  | 2026-08-06T06:18:11.623000Z |
| b1d76a2d-8bf2-44ac-bd65-a4a710f5296d | budget-test-user | ssw-fake      | failure  | 2026-08-06T06:17:48.490000Z |
| d5f2cc05-2ee1-4e11-8436-2bf5cf0475a0 | lee              | ssw-expensive | failure  | 2026-08-06T06:17:46.433000Z |

