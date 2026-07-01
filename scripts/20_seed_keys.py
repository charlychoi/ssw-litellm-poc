import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
MASTER_KEY = os.getenv("LITELLM_MASTER_KEY")
DOCS_DIR = Path(__file__).parent.parent / "docs"

console = Console()

VIRTUAL_KEYS = [
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
            "ssw-dev-sonnet",
            "ssw-dev-gpt",
            "ssw-free-test",
            "ssw-expensive",
            "ssw-fake",
            "ssw-low-cost",
        ],
        "max_budget": 10.0,
        "budget_duration": "30d",
        "metadata": {"tool": "admin-api", "role": "admin"},
    },
]


def generate_key(client: httpx.Client, spec: dict) -> dict | None:
    alias = spec["key_alias"]
    try:
        resp = client.post(
            f"{PROXY_URL}/key/generate",
            json=spec,
            headers={"Authorization": f"Bearer {MASTER_KEY}"},
            timeout=30,
        )
        if resp.status_code == 409:
            console.print(f"[yellow]WARNING: key '{alias}' already exists (409), skipping.[/yellow]")
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        console.print(f"[red]ERROR creating '{alias}': HTTP {e.response.status_code} — {e.response.text}[/red]")
        return None
    except Exception as e:
        console.print(f"[red]ERROR creating '{alias}': {e}[/red]")
        return None


def redact(key: str) -> str:
    return key[:8] + "..." if len(key) > 8 else key + "..."


def main():
    if not MASTER_KEY:
        console.print("[red]LITELLM_MASTER_KEY is not set. Aborting.[/red]")
        sys.exit(1)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    created = []
    key_store = {}

    with httpx.Client() as client:
        for spec in VIRTUAL_KEYS:
            result = generate_key(client, spec)
            if result:
                entry = {
                    "key_alias": spec["key_alias"],
                    "user_id": spec["user_id"],
                    "team_id": spec["team_id"],
                    "models": spec["models"],
                    "max_budget": spec["max_budget"],
                    "budget_duration": spec["budget_duration"],
                    "metadata": spec.get("metadata", {}),
                    "key": result.get("key", ""),
                    "key_name": result.get("key_name", ""),
                }
                created.append(entry)
                # Index by user+tool for demo_calls.py lookup
                tool = spec["metadata"].get("tool", "")
                user = spec["user_id"]
                key_store[f"{user}_{tool}"] = entry
                console.print(f"[green]Created:[/green] {spec['key_alias']}")

    # Save full key store (unredacted) for scripts to use
    keys_json_path = DOCS_DIR / "generated_keys.json"
    with open(keys_json_path, "w") as f:
        json.dump(key_store, f, indent=2)
    console.print(f"\n[dim]Saved key store to {keys_json_path}[/dim]")

    # Save redacted summary for docs
    redacted_path = DOCS_DIR / "generated_keys.redacted.md"
    with open(redacted_path, "w") as f:
        f.write("# Generated Virtual Keys (Redacted)\n\n")
        f.write("| alias | user | team | models | max_budget | key (redacted) |\n")
        f.write("|---|---|---|---|---|---|\n")
        for e in created:
            models_str = ", ".join(e["models"])
            f.write(
                f"| {e['key_alias']} | {e['user_id']} | {e['team_id']} "
                f"| {models_str} | ${e['max_budget']} | {redact(e['key'])} |\n"
            )
    console.print(f"[dim]Saved redacted summary to {redacted_path}[/dim]")

    # Rich table
    table = Table(title="Virtual Keys Created", show_lines=True)
    table.add_column("Alias", style="cyan")
    table.add_column("User")
    table.add_column("Team")
    table.add_column("Models", overflow="fold")
    table.add_column("Budget")
    table.add_column("Key (redacted)", style="dim")

    for e in created:
        table.add_row(
            e["key_alias"],
            e["user_id"],
            e["team_id"],
            ", ".join(e["models"]),
            f"${e['max_budget']} / {e['budget_duration']}",
            redact(e["key"]),
        )

    console.print()
    console.print(table)
    console.print(f"\n[bold green]Done.[/bold green] {len(created)} key(s) created.")


if __name__ == "__main__":
    main()
