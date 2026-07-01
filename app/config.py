import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
LITELLM_MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./litellm_poc.db")
TEST_BUDGET_LIMIT = float(os.getenv("TEST_BUDGET_LIMIT", "0.0001"))

VIRTUAL_KEY_SPECS = [
    {
        "key_alias": "dev-kim-claude",
        "user_id": "kim",
        "team_id": "dev-team",
        "models": ["ssw-dev-sonnet", "ssw-free-test", "ssw-fake", "claude-sonnet"],
        "max_budget": 5.0,
        "budget_duration": "30d",
        "tpm_limit": 80000,
        "rpm_limit": 60,
        "metadata": {"tool": "claude-code", "role": "developer"},
    },
    {
        "key_alias": "dev-kim-codex",
        "user_id": "kim",
        "team_id": "dev-team",
        "models": ["ssw-dev-gpt", "ssw-fake", "gpt-dev"],
        "max_budget": 5.0,
        "budget_duration": "30d",
        "tpm_limit": 80000,
        "rpm_limit": 60,
        "metadata": {"tool": "codex-cli", "role": "developer"},
    },
    {
        "key_alias": "dev-kim-gemini",
        "user_id": "kim",
        "team_id": "dev-team",
        "models": ["ssw-free-test", "ssw-fake", "free-test"],
        "max_budget": 5.0,
        "budget_duration": "30d",
        "tpm_limit": 80000,
        "rpm_limit": 60,
        "metadata": {"tool": "gemini-cli", "role": "developer"},
    },
    {
        "key_alias": "staff-lee-chat",
        "user_id": "lee",
        "team_id": "staff-team",
        "models": ["ssw-low-cost", "ssw-fake", "low-cost"],
        "max_budget": 1.0,
        "budget_duration": "30d",
        "tpm_limit": 20000,
        "rpm_limit": 10,
        "metadata": {"tool": "chat", "role": "staff"},
    },
    {
        "key_alias": "admin-park-test",
        "user_id": "park",
        "team_id": "admin-team",
        "models": [
            "ssw-dev-sonnet", "ssw-dev-gpt", "ssw-free-test",
            "ssw-expensive", "ssw-fake", "ssw-low-cost",
        ],
        "max_budget": 10.0,
        "budget_duration": "30d",
        "metadata": {"tool": "admin-api", "role": "admin"},
    },
]

# UI에서 사용하는 사용자→도구→키 매핑
KEY_UI_MAP = {
    ("kim", "claude-code"): {
        "alias": "dev-kim-claude",
        "models": ["ssw-dev-sonnet", "ssw-fake", "ssw-free-test"],
    },
    ("kim", "codex-cli"): {
        "alias": "dev-kim-codex",
        "models": ["ssw-dev-gpt", "ssw-fake"],
    },
    ("kim", "gemini-cli"): {
        "alias": "dev-kim-gemini",
        "models": ["ssw-free-test", "ssw-fake"],
    },
    ("lee", "chat"): {
        "alias": "staff-lee-chat",
        "models": ["ssw-low-cost", "ssw-fake"],
    },
    ("park", "admin-api"): {
        "alias": "admin-park-test",
        "models": ["ssw-dev-sonnet", "ssw-dev-gpt", "ssw-free-test", "ssw-expensive", "ssw-fake"],
    },
}

USER_TOOL_MAP = {
    "kim": ["claude-code", "codex-cli", "gemini-cli"],
    "lee": ["chat"],
    "park": ["admin-api"],
}
