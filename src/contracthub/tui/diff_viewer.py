"""Rich Diff Viewer and Terminal Output Visualizer."""

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from contracthub.core.models import CompatibilityResult, Severity

console = Console()


def render_diff_table(result: CompatibilityResult, base_name: str, candidate_name: str) -> None:
    """Renders a rich formatted terminal report for schema compatibility checks."""
    if result.is_compatible:
        title = Text(" COMPATIBILITY VERIFICATION: PASSED ", style="bold white on green")
        summary_text = (
            f"[bold green]No breaking changes detected.[/bold green]\n"
            f"Base: [cyan]{base_name}[/cyan] | Candidate: [cyan]{candidate_name}[/cyan]\n"
            f"Mode: [yellow]{result.mode.value}[/yellow] | Checks performed: {result.total_checks}"
        )
        console.print()
        console.print(Panel(summary_text, title=title, border_style="green", expand=False))
        console.print()
        return

    # Incompatible changes detected
    title = Text(" COMPATIBILITY VERIFICATION: FAILED ", style="bold white on red")
    summary_text = (
        f"[bold red]{result.breaking_count} breaking change(s) detected![/bold red]\n"
        f"Base: [cyan]{base_name}[/cyan] | Candidate: [cyan]{candidate_name}[/cyan]\n"
        f"Mode: [yellow]{result.mode.value}[/yellow] | Total violations: {len(result.violations)}"
    )
    console.print()
    console.print(Panel(summary_text, title=title, border_style="red", expand=False))
    console.print()

    table = Table(
        title="Schema Evolution Violations",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
    )
    table.add_column("Severity", justify="center", style="bold", width=12)
    table.add_column("Code", style="cyan", width=26)
    table.add_column("Path", style="yellow", width=28)
    table.add_column("Violation Details", style="white")
    table.add_column("Suggestion", style="green")

    for v in result.violations:
        if v.severity == Severity.BREAKING:
            sev_text = Text("BREAKING", style="bold red")
        elif v.severity == Severity.WARNING:
            sev_text = Text("WARNING", style="bold yellow")
        else:
            sev_text = Text("INFO", style="bold blue")

        table.add_row(
            sev_text,
            v.code,
            v.path,
            v.message,
            v.suggestion or "-",
        )

    console.print(table)
    console.print()


def render_json_result(result: CompatibilityResult) -> None:
    """Prints raw JSON representation for CI/CD log parsers."""
    data = result.model_dump(mode="json")
    console.print(json.dumps(data, indent=2))


def render_scan_table(summary) -> None:
    """Renders a formatted multi-file scan table for Git repositories."""
    if summary.total_scanned == 0:
        console.print("[yellow]No modified schema files found to scan.[/yellow]")
        return

    if summary.is_compatible:
        title = Text(" MONOREPO SCHEMA SCAN: PASSED ", style="bold white on green")
        summary_text = (
            f"[bold green]All {summary.total_scanned} schema file(s) are compatible.[/bold green]\n"
            f"Target Git Ref: [cyan]{summary.target_ref}[/cyan] | Mode: [yellow]{summary.mode.value}[/yellow]"
        )
        console.print()
        console.print(Panel(summary_text, title=title, border_style="green", expand=False))
        console.print()
    else:
        title = Text(" MONOREPO SCHEMA SCAN: FAILED ", style="bold white on red")
        summary_text = (
            f"[bold red]{summary.failed_count} of {summary.total_scanned} file(s) contain breaking changes![/bold red]\n"
            f"Target Git Ref: [cyan]{summary.target_ref}[/cyan] | Mode: [yellow]{summary.mode.value}[/yellow]"
        )
        console.print()
        console.print(Panel(summary_text, title=title, border_style="red", expand=False))
        console.print()

    table = Table(title="Scanned Schema Files", header_style="bold magenta", border_style="dim")
    table.add_column("Status", justify="center", width=12)
    table.add_column("Schema File", style="cyan", width=36)
    table.add_column("Breaking", justify="center", width=10)
    table.add_column("Notes", style="white")

    for item in summary.results:
        if item.is_new_file:
            table.add_row(
                Text("NEW", style="bold blue"),
                item.path,
                "0",
                "Newly added schema (compatible)",
            )
        elif item.is_compatible:
            table.add_row(
                Text("PASSED", style="bold green"),
                item.path,
                "0",
                f"{item.total_checks} checks passed",
            )
        else:
            first_v = item.violations[0].message if item.violations else "Breaking mutation"
            table.add_row(
                Text("FAILED", style="bold red"),
                item.path,
                str(item.breaking_count),
                first_v,
            )

    console.print(table)
    console.print()


def render_github_summary(summary) -> str:
    """Produces GitHub Flavored Markdown for $GITHUB_STEP_SUMMARY or PR comments."""
    lines = []
    lines.append("# ContractHub Schema Scan Report\n")

    if summary.is_compatible:
        lines.append("**Status:** Passed\n")
        lines.append(
            f"All **{summary.total_scanned}** modified schema files satisfy `{summary.mode.value}` compatibility invariants against `{summary.target_ref}`.\n"
        )
    else:
        lines.append("**Status:** Failed\n")
        lines.append(
            f"Found breaking changes in **{summary.failed_count}** of **{summary.total_scanned}** schema file(s) evaluated against `{summary.target_ref}`.\n"
        )

    lines.append("| Status | Schema File | Breaking Issues | Details |")
    lines.append("| :---: | :--- | :---: | :--- |")

    for item in summary.results:
        if item.is_new_file:
            lines.append(f"| NEW | `{item.path}` | 0 | Newly introduced schema |")
        elif item.is_compatible:
            lines.append(f"| PASSED | `{item.path}` | 0 | Compatible evolution |")
        else:
            lines.append(f"| FAILED | `{item.path}` | {item.breaking_count} | Breaking changes detected |")

    lines.append("\n")

    # Detailed collapsible tables for failed files
    for item in summary.results:
        if not item.is_compatible:
            lines.append(f"<details><summary><strong>Violations in {item.path} ({item.breaking_count} issues)</strong></summary>\n")
            lines.append("| Severity | Code | Path | Message | Suggestion |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for v in item.violations:
                sug = v.suggestion or "-"
                lines.append(f"| `{v.severity.value}` | `{v.code}` | `{v.path}` | {v.message} | {sug} |")
            lines.append("\n</details>\n")

    return "\n".join(lines)
