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
