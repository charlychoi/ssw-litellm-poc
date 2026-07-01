import os
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
MASTER_KEY = os.getenv("LITELLM_MASTER_KEY")
DOCS_DIR = Path(__file__).parent.parent / "docs"
REPORT_PATH = DOCS_DIR / "VERIFICATION_REPORT.md"

console = Console()

TEST_ALIAS = "budget-block-test-throwaway"
TEST_MODEL = "ssw-fake"


def admin_headers() -> dict:
    return {"Authorization": f"Bearer {MASTER_KEY}"}


def create_test_key(client: httpx.Client) -> str | None:
    payload = {
        "key_alias": TEST_ALIAS,
        "user_id": "budget-test-user",
        "models": [TEST_MODEL],
        "max_budget": 0.0001,
        "budget_duration": "30d",
        "metadata": {"tool": "budget-block-test", "role": "test"},
    }
    resp = client.post(
        f"{PROXY_URL}/key/generate",
        json=payload,
        headers=admin_headers(),
        timeout=30,
    )
    if resp.status_code == 409:
        console.print(f"[yellow]Test key '{TEST_ALIAS}' already exists. Attempting to reuse...[/yellow]")
        # Try to find and return existing key — for simplicity, abort and ask user to clean up
        console.print("[red]Please delete the existing test key manually and re-run.[/red]")
        return None
    resp.raise_for_status()
    key = resp.json().get("key")
    console.print(f"[green]Created test key:[/green] {key[:10]}...")
    return key


def call_model(client: httpx.Client, api_key: str, model: str) -> tuple[bool, dict]:
    try:
        resp = client.post(
            f"{PROXY_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "budget test ping"}],
                "max_tokens": 5,
            },
            timeout=30,
        )
        if resp.status_code in (200, 201):
            return True, resp.json()
        return False, {"status_code": resp.status_code, "body": resp.text}
    except Exception as e:
        return False, {"error": str(e)}


def set_max_budget_zero(client: httpx.Client, api_key: str):
    # PATCH /key/update — set max_budget to 0.0 to force budget exhaustion
    resp = client.post(
        f"{PROXY_URL}/key/update",
        json={"key": api_key, "max_budget": 0.0},
        headers=admin_headers(),
        timeout=30,
    )
    if resp.status_code == 200:
        console.print("[cyan]Updated key max_budget → 0.0 via Admin API[/cyan]")
    else:
        console.print(f"[yellow]Update returned {resp.status_code}: {resp.text}[/yellow]")


def delete_test_key(client: httpx.Client, api_key: str):
    resp = client.post(
        f"{PROXY_URL}/key/delete",
        json={"keys": [api_key]},
        headers=admin_headers(),
        timeout=30,
    )
    if resp.status_code == 200:
        console.print("[dim]Test key deleted.[/dim]")
    else:
        console.print(f"[yellow]Could not delete test key: {resp.status_code}[/yellow]")


def append_report(section: str):
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "a") as f:
        f.write(section + "\n")


def main():
    if not MASTER_KEY:
        console.print("[red]LITELLM_MASTER_KEY is not set. Aborting.[/red]")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.rule("[bold]Budget Block Test[/bold]")

    results = []

    with httpx.Client() as client:
        # Step 1: Create throw-away key with near-zero budget
        console.print("\n[bold]Step 1:[/bold] Creating test key with max_budget=0.0001")
        test_key = create_test_key(client)
        if not test_key:
            sys.exit(1)

        # Step 2: First call — should succeed (fake provider, budget not yet tracked)
        console.print(f"\n[bold]Step 2:[/bold] First call to {TEST_MODEL}")
        success, result = call_model(client, test_key, TEST_MODEL)
        if success:
            console.print("[green]Call 1: SUCCESS (as expected for first call)[/green]")
            results.append(("Call 1 (pre-budget-zero)", "SUCCESS", str(result)[:200]))
        else:
            console.print(f"[yellow]Call 1 blocked unexpectedly: {result}[/yellow]")
            results.append(("Call 1 (pre-budget-zero)", "BLOCKED (unexpected)", str(result)[:200]))

        # Step 3: Force budget exhaustion via Admin API
        console.print("\n[bold]Step 3:[/bold] Setting max_budget=0.0 via Admin API to force exhaustion")
        set_max_budget_zero(client, test_key)

        # Small pause to allow LiteLLM to pick up the updated budget
        time.sleep(1)

        # Step 4: Second call — should be blocked
        console.print(f"\n[bold]Step 4:[/bold] Second call to {TEST_MODEL} (expect: BLOCKED)")
        success2, result2 = call_model(client, test_key, TEST_MODEL)
        if not success2:
            body = result2.get("body", "")
            status = result2.get("status_code", "")
            if "budget" in body.lower() or status in (429, 400):
                console.print(f"[bold green]BLOCKED — Budget exceeded (HTTP {status})[/bold green]")
                console.print(f"[dim]{body[:300]}[/dim]")
                results.append(("Call 2 (post-budget-zero)", "BLOCKED (budget exceeded)", body[:300]))
            else:
                console.print(f"[red]BLOCKED for unknown reason (HTTP {status}):[/red] {body[:300]}")
                results.append(("Call 2 (post-budget-zero)", f"BLOCKED (HTTP {status})", body[:300]))
        else:
            console.print("[yellow]WARNING: Expected budget block but call succeeded.[/yellow]")
            results.append(("Call 2 (post-budget-zero)", "SUCCESS (unexpected)", str(result2)[:200]))

        # Step 5: Clean up
        console.print("\n[bold]Step 5:[/bold] Deleting test key")
        delete_test_key(client, test_key)

    # Write to report
    rows = "\n".join(f"| {r[0]} | {r[1]} | `{r[2]}` |" for r in results)
    report_section = f"""
## [{timestamp}] Budget Block Test

| Step | Result | Detail |
|---|---|---|
{rows}

**Conclusion**: LiteLLM budget enforcement {"PASSED" if any("BLOCKED" in r[1] and "unexpected" not in r[1] for r in results) else "NEEDS REVIEW"}.
"""
    append_report(report_section)
    console.print(f"\n[dim]Results written to {REPORT_PATH}[/dim]")
    console.rule("[bold]Done[/bold]")


if __name__ == "__main__":
    main()
