import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
import typer
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
DOCS_DIR = Path(__file__).parent.parent / "docs"
KEYS_JSON = DOCS_DIR / "generated_keys.json"
REPORT_PATH = DOCS_DIR / "VERIFICATION_REPORT.md"

app = typer.Typer(add_completion=False)
console = Console()

# Map CLI --tool arg to metadata tool values used in generated_keys.json
TOOL_MAP = {
    "claude": "claude-code",
    "codex": "codex-cli",
    "gemini": "gemini-cli",
    "chat": "chat",
    "admin": "admin-api",
}


def load_keys() -> dict:
    if not KEYS_JSON.exists():
        console.print(f"[red]Key store not found at {KEYS_JSON}. Run 20_seed_keys.py first.[/red]")
        sys.exit(1)
    with open(KEYS_JSON) as f:
        return json.load(f)


def lookup_key(keys: dict, user: str, tool: str) -> dict | None:
    internal_tool = TOOL_MAP.get(tool, tool)
    return keys.get(f"{user}_{internal_tool}")


def chat_completion(api_key: str, model: str, prompt: str) -> tuple[bool, dict]:
    try:
        resp = httpx.post(
            f"{PROXY_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
            },
            timeout=30,
        )
        if resp.status_code in (200, 201):
            return True, resp.json()
        return False, {"status_code": resp.status_code, "body": resp.text}
    except Exception as e:
        return False, {"error": str(e)}


def append_report(section: str):
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "a") as f:
        f.write(section + "\n")


@app.command()
def main(
    user: str = typer.Option(..., help="User identifier: kim, lee, park"),
    tool: str = typer.Option(..., help="Tool: claude, codex, gemini, chat, admin"),
    case: str = typer.Option(
        "allowed",
        help="Test case: allowed | denied-model | denied-budget",
    ),
    model_override: str = typer.Option(
        None, "--model", help="Override model for allowed case (e.g. ssw-fake)"
    ),
):
    keys = load_keys()
    key_entry = lookup_key(keys, user, tool)

    if not key_entry:
        console.print(f"[red]No key found for user='{user}' tool='{tool}'. Available: {list(keys.keys())}[/red]")
        sys.exit(1)

    api_key = key_entry["key"]
    allowed_models = key_entry["models"]
    alias = key_entry["key_alias"]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"\n[bold]Demo call[/bold] — alias: [cyan]{alias}[/cyan], case: [yellow]{case}[/yellow]")

    if case == "allowed":
        model = model_override if model_override else allowed_models[0]
        prompt = "안녕하세요. 상상우리 AI 게이트웨이 테스트입니다."
        console.print(f"Model: [green]{model}[/green]")
        success, result = chat_completion(api_key, model, prompt)

    elif case == "denied-model":
        # ssw-expensive should not be in most keys' allowed list
        model = "ssw-expensive"
        prompt = "This should be blocked by model policy."
        console.print(f"Model: [red]{model}[/red] (expected: BLOCKED)")
        success, result = chat_completion(api_key, model, prompt)
        # For denied-model, a successful API call is actually a failure of policy
        if success:
            console.print("[yellow]WARNING: Expected block but call succeeded — check model allow-list.[/yellow]")
            success = False  # treat as unexpected
        else:
            success = True   # blocked as expected

    elif case == "denied-budget":
        # Use staff-lee-chat key regardless of passed user/tool to test budget
        lee_key = keys.get("lee_chat")
        if not lee_key:
            console.print("[red]staff-lee-chat key not found in key store.[/red]")
            sys.exit(1)
        api_key = lee_key["key"]
        model = "ssw-fake"
        prompt = "Budget exhaustion test."
        console.print(f"Key: [cyan]{lee_key['key_alias']}[/cyan], Model: [yellow]{model}[/yellow]")
        success, result = chat_completion(api_key, model, prompt)
        if not success:
            body = result.get("body", "")
            if "budget" in body.lower() or result.get("status_code") in (429, 400):
                console.print("[green]BLOCKED (budget exceeded — as expected)[/green]")
            else:
                console.print(f"[red]BLOCKED for unexpected reason:[/red] {body}")
        else:
            console.print("[yellow]WARNING: Expected budget block but call succeeded.[/yellow]")

    else:
        console.print(f"[red]Unknown case: '{case}'. Use: allowed | denied-model | denied-budget[/red]")
        sys.exit(1)

    # Print outcome
    cost = None
    if success and isinstance(result, dict):
        usage = result.get("usage", {})
        cost = result.get("_hidden_params", {}).get("response_cost") or result.get("x_litellm_response_cost")
        console.rule()
        console.print("[bold green]SUCCESS[/bold green]")
        choices = result.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            console.print(f"Response: {content[:300]}")
        if cost:
            console.print(f"Estimated cost: [cyan]${cost}[/cyan]")
        if usage:
            console.print(f"Tokens: {usage}")
    elif case != "denied-model":
        console.rule()
        console.print("[bold red]BLOCKED[/bold red]")
        console.print(f"Detail: {result}")

    # Append to VERIFICATION_REPORT.md
    status_label = "SUCCESS" if (success and case == "allowed") else "BLOCKED"
    report_section = f"""
## [{timestamp}] Case: `{case}` — User: `{user}`, Tool: `{tool}`

- **Key alias**: `{alias}`
- **Model attempted**: `{model}`
- **Result**: **{status_label}**
- **Cost**: {f'${cost}' if cost else 'N/A'}
- **Raw result**: `{str(result)[:500]}`
"""
    append_report(report_section)
    console.print(f"\n[dim]Appended result to {REPORT_PATH}[/dim]")


if __name__ == "__main__":
    app()
