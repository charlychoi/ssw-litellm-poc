import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
MASTER_KEY = os.getenv("LITELLM_MASTER_KEY")
DOCS_DIR = Path(__file__).parent.parent / "docs"
REPORT_PATH = DOCS_DIR / "USAGE_REPORT.md"

console = Console()


def admin_headers() -> dict:
    return {"Authorization": f"Bearer {MASTER_KEY}"}


def fetch_keys(client: httpx.Client) -> list[dict]:
    resp = client.get(
        f"{PROXY_URL}/key/list",
        params={"include_team_keys": "true"},
        headers=admin_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    raw_keys = data.get("keys", data) if isinstance(data, dict) else data

    # /key/list may return just key strings — fetch detailed info for each
    result = []
    for k in raw_keys:
        if isinstance(k, str):
            try:
                info_resp = client.get(
                    f"{PROXY_URL}/key/info",
                    params={"key": k},
                    headers=admin_headers(),
                    timeout=10,
                )
                if info_resp.status_code == 200:
                    info = info_resp.json()
                    # /key/info returns {"key": "...", "info": {...}}
                    entry = info.get("info", info) if isinstance(info, dict) else {}
                    result.append(entry)
            except Exception:
                pass
        elif isinstance(k, dict):
            result.append(k)
    return result


def fetch_spend_logs(client: httpx.Client) -> list[dict]:
    # Try /spend/logs first, fall back to /global/spend/keys
    try:
        resp = client.get(
            f"{PROXY_URL}/spend/logs",
            headers=admin_headers(),
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("logs", data.get("data", []))
    except Exception as e:
        console.print(f"[yellow]/spend/logs failed: {e}[/yellow]")

    # Fallback: global spend by key
    try:
        resp = client.get(
            f"{PROXY_URL}/global/spend/keys",
            headers=admin_headers(),
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("data", [])
    except Exception as e:
        console.print(f"[yellow]/global/spend/keys failed: {e}[/yellow]")

    return []


def df_to_markdown(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def print_rich_table(title: str, df: pd.DataFrame):
    table = Table(title=title, show_lines=True)
    for col in df.columns:
        table.add_column(str(col))
    for _, row in df.iterrows():
        table.add_row(*[str(v) for v in row])
    console.print(table)


def main():
    if not MASTER_KEY:
        console.print("[red]LITELLM_MASTER_KEY is not set. Aborting.[/red]")
        sys.exit(1)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.rule("[bold]LiteLLM Usage Report[/bold]")

    with httpx.Client() as client:
        # --- Key list with spend ---
        console.print("[bold]Fetching key list...[/bold]")
        keys = fetch_keys(client)
        console.print(f"  Found {len(keys)} key(s)")

        # --- Spend logs ---
        console.print("[bold]Fetching spend logs...[/bold]")
        logs = fetch_spend_logs(client)
        console.print(f"  Found {len(logs)} log record(s)")

    # Build keys DataFrame
    keys_rows = []
    for k in keys:
        raw_meta = k.get("metadata", {}) or {}
        meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
        keys_rows.append(
            {
                "key_alias": k.get("key_alias") or k.get("aliases", {}).get("key_alias", ""),
                "user_id": k.get("user_id", ""),
                "team_id": k.get("team_id", ""),
                "tool": meta.get("tool", ""),
                "role": meta.get("role", ""),
                "max_budget": k.get("max_budget"),
                "spend": k.get("spend", 0.0),
                "budget_reset_at": k.get("budget_reset_at", ""),
                "models": ", ".join(k.get("models") or []),
            }
        )
    keys_df = pd.DataFrame(keys_rows) if keys_rows else pd.DataFrame()

    # Build logs DataFrame
    logs_rows = []
    for log in logs:
        logs_rows.append(
            {
                "request_id": log.get("request_id", log.get("id", "")),
                "user_id": log.get("user", log.get("user_id", "")),
                "key_alias": log.get("api_key_alias", log.get("key_alias", "")),
                "model": log.get("model", ""),
                "spend": log.get("spend", 0.0),
                "total_tokens": log.get("total_tokens", 0),
                "startTime": log.get("startTime", log.get("start_time", "")),
                "status": log.get("status", "success"),
            }
        )
    logs_df = pd.DataFrame(logs_rows) if logs_rows else pd.DataFrame()

    # --- Aggregations ---
    report_lines = [
        f"# LiteLLM Usage Report\n",
        f"Generated: {timestamp}\n",
        f"Proxy: {PROXY_URL}\n",
        "---\n",
    ]

    # Per-key summary
    if not keys_df.empty:
        summary_cols = ["key_alias", "user_id", "team_id", "tool", "max_budget", "spend"]
        display_df = keys_df[summary_cols].copy()
        display_df["spend"] = display_df["spend"].map(lambda x: f"${x:.6f}" if x is not None else "$0.000000")
        print_rich_table("Virtual Keys Summary", display_df)
        report_lines.append("## Virtual Keys Summary\n")
        report_lines.append(df_to_markdown(display_df) + "\n\n")
    else:
        report_lines.append("## Virtual Keys Summary\n\n_No keys found._\n\n")

    if not logs_df.empty:
        logs_df["spend"] = pd.to_numeric(logs_df["spend"], errors="coerce").fillna(0.0)
        logs_df["total_tokens"] = pd.to_numeric(logs_df["total_tokens"], errors="coerce").fillna(0)

        # Total summary
        total_calls = len(logs_df)
        total_cost = logs_df["spend"].sum()
        console.print(f"\nTotal calls: [cyan]{total_calls}[/cyan], Total cost: [cyan]${total_cost:.6f}[/cyan]")

        report_lines.append("## Overall Summary\n")
        report_lines.append(f"- **Total calls**: {total_calls}\n")
        report_lines.append(f"- **Total cost**: ${total_cost:.6f}\n\n")

        # Per-user cost
        per_user = (
            logs_df.groupby("user_id")
            .agg(calls=("request_id", "count"), total_cost=("spend", "sum"))
            .reset_index()
            .sort_values("total_cost", ascending=False)
        )
        per_user["total_cost"] = per_user["total_cost"].map(lambda x: f"${x:.6f}")
        print_rich_table("Cost by User", per_user)
        report_lines.append("## Cost by User\n")
        report_lines.append(df_to_markdown(per_user) + "\n\n")

        # Per-tool cost (from key_alias pattern)
        if "key_alias" in logs_df.columns:
            per_tool = (
                logs_df.groupby("key_alias")
                .agg(calls=("request_id", "count"), total_cost=("spend", "sum"))
                .reset_index()
                .sort_values("total_cost", ascending=False)
            )
            per_tool["total_cost"] = per_tool["total_cost"].map(lambda x: f"${x:.6f}")
            print_rich_table("Cost by Key/Tool", per_tool)
            report_lines.append("## Cost by Key / Tool\n")
            report_lines.append(df_to_markdown(per_tool) + "\n\n")

        # Per-model cost
        per_model = (
            logs_df.groupby("model")
            .agg(calls=("request_id", "count"), total_cost=("spend", "sum"), tokens=("total_tokens", "sum"))
            .reset_index()
            .sort_values("total_cost", ascending=False)
        )
        per_model["total_cost"] = per_model["total_cost"].map(lambda x: f"${x:.6f}")
        print_rich_table("Cost by Model", per_model)
        report_lines.append("## Cost by Model\n")
        report_lines.append(df_to_markdown(per_model) + "\n\n")

        # Blocked events (non-success status)
        if "status" in logs_df.columns:
            blocked = logs_df[logs_df["status"] != "success"]
            report_lines.append("## Blocked Events\n")
            if not blocked.empty:
                blocked_display = blocked[["request_id", "user_id", "model", "status", "startTime"]].copy()
                print_rich_table("Blocked Events", blocked_display)
                report_lines.append(df_to_markdown(blocked_display) + "\n\n")
            else:
                report_lines.append("_No blocked events found in logs._\n\n")
    else:
        report_lines.append("## Spend Logs\n\n_No spend log records found._\n\n")

    report_text = "\n".join(report_lines)
    with open(REPORT_PATH, "w") as f:
        f.write(report_text)

    console.print(f"\n[bold green]Report written to:[/bold green] {REPORT_PATH}")


if __name__ == "__main__":
    main()
