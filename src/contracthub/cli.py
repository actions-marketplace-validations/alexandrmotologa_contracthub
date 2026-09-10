"""ContractHub Command Line Interface."""

import json
from pathlib import Path

import httpx
import typer
import uvicorn
from rich.console import Console

from contracthub import __version__
from contracthub.config import settings
from contracthub.core.comparator import SchemaComparator
from contracthub.core.mock_generator import MockGenerator
from contracthub.core.models import CompatibilityMode
from contracthub.core.remediation import AutoRemediator
from contracthub.core.scanner import GitScanner
from contracthub.core.semver import SemVerEngine
from contracthub.core.validator import PayloadValidator
from contracthub.tui.diff_viewer import (
    render_diff_table,
    render_github_summary,
    render_json_result,
    render_scan_table,
    render_semver_report,
    render_validation_report,
)

app = typer.Typer(
    name="contracthub",
    help="Universal Schema Registry and Breaking Change Linter.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(
            f"[bold cyan]ContractHub[/bold cyan] version [bold white]{__version__}[/bold white]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    pass


@app.command()
def diff(
    base_file: Path = typer.Argument(..., help="Path to base (old) schema file."),
    candidate_file: Path = typer.Argument(..., help="Path to candidate (new) schema file."),
    mode: CompatibilityMode = typer.Option(
        CompatibilityMode.FULL,
        "--mode",
        "-m",
        help="Compatibility evaluation mode.",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: 'table' or 'json'.",
    ),
):
    """Compare two local schema files and report breaking change violations."""
    if not base_file.exists():
        console.print(f"[bold red]Error:[/bold red] Base file '{base_file}' does not exist.")
        raise typer.Exit(code=2)

    if not candidate_file.exists():
        console.print(
            f"[bold red]Error:[/bold red] Candidate file '{candidate_file}' does not exist."
        )
        raise typer.Exit(code=2)

    try:
        base_content = base_file.read_text(encoding="utf-8")
        candidate_content = candidate_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        console.print(f"[bold red]Error reading files:[/bold red] {e}")
        raise typer.Exit(code=2) from e

    schema_type = SchemaComparator.detect_schema_type(base_content, base_file.name)

    result = SchemaComparator.compare_strings(
        base_content=base_content,
        candidate_content=candidate_content,
        schema_type=schema_type,
        mode=mode,
    )

    if format.lower() == "json":
        render_json_result(result)
    else:
        render_diff_table(result, base_name=base_file.name, candidate_name=candidate_file.name)

    if not result.is_compatible:
        raise typer.Exit(code=1)


@app.command()
def scan(
    against: str = typer.Option(
        "origin/main",
        "--against",
        "-a",
        help="Git branch or reference to compare working tree against.",
    ),
    mode: CompatibilityMode = typer.Option(
        CompatibilityMode.FULL,
        "--mode",
        "-m",
        help="Compatibility evaluation mode.",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: 'table', 'json', or 'github'.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional file path to write summary report to.",
    ),
):
    """Scan all modified schema files in the Git repository against a base branch."""
    summary = GitScanner.scan(target_ref=against, mode=mode)

    if format.lower() == "json":
        data = summary.model_dump(mode="json")
        json_str = json.dumps(data, indent=2)
        if output:
            output.write_text(json_str, encoding="utf-8")
        else:
            console.print(json_str)
    elif format.lower() == "github":
        md = render_github_summary(summary)
        if output:
            output.write_text(md, encoding="utf-8")
        else:
            console.print(md)
    else:
        render_scan_table(summary)
        if output:
            md = render_github_summary(summary)
            output.write_text(md, encoding="utf-8")

    if not summary.is_compatible:
        raise typer.Exit(code=1)


@app.command()
def fix(
    candidate_file: Path = typer.Argument(..., help="Path to candidate schema file to fix."),
    base_file: Path = typer.Option(..., "--base", "-b", help="Path to base (old) schema file."),
    in_place: bool = typer.Option(
        False,
        "--in-place",
        "-i",
        help="Overwrite candidate file with fixed content.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview synthesized fixes without writing changes.",
    ),
):
    """Automatically patch breaking changes (e.g. inject reserved tags) into candidate schemas."""
    if not base_file.exists():
        console.print(f"[bold red]Error:[/bold red] Base file '{base_file}' does not exist.")
        raise typer.Exit(code=2)
    if not candidate_file.exists():
        console.print(
            f"[bold red]Error:[/bold red] Candidate file '{candidate_file}' does not exist."
        )
        raise typer.Exit(code=2)

    base_content = base_file.read_text(encoding="utf-8")
    candidate_content = candidate_file.read_text(encoding="utf-8")

    result = AutoRemediator.fix_proto(
        base_content=base_content,
        candidate_content=candidate_content,
    )

    if not result.was_modified:
        console.print(
            "[green]No auto-remediable breaking changes found (schema is either compatible or contains non-trivial mutations).[/green]"
        )
        raise typer.Exit(code=0)

    console.print(
        f"[bold cyan]Identified {len(result.actions)} auto-remediation fix(es):[/bold cyan]"
    )
    for act in result.actions:
        console.print(f"  - [yellow]{act.target}[/yellow]: {act.description}")
        console.print(f"    [dim]{act.patch_snippet}[/dim]")

    if dry_run or not in_place:
        console.print(
            "\n[yellow]Run with '--in-place' (-i) to apply these fixes directly to the candidate file.[/yellow]"
        )
    else:
        candidate_file.write_text(result.fixed_content, encoding="utf-8")
        console.print(f"\n[bold green]Successfully applied fixes to {candidate_file}![/bold green]")


@app.command()
def mock(
    file: Path = typer.Option(..., "--file", "-f", help="Schema file to generate mock data from."),
    message: str | None = typer.Option(
        None,
        "--message",
        "-m",
        help="Target message or entity name for Proto/OpenAPI.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional output JSON file path.",
    ),
):
    """Generate synthetic JSON mock data payloads conforming to a schema definition."""
    if not file.exists():
        console.print(f"[bold red]Error:[/bold red] File '{file}' does not exist.")
        raise typer.Exit(code=2)

    content = file.read_text(encoding="utf-8")
    schema_type = SchemaComparator.detect_schema_type(content, file.name)

    mock_data = MockGenerator.generate(
        schema_content=content,
        schema_type=schema_type,
        target_entity=message,
    )

    json_str = json.dumps(mock_data, indent=2)
    if output:
        output.write_text(json_str, encoding="utf-8")
        console.print(f"[bold green]Saved mock data to {output}[/bold green]")
    else:
        console.print(json_str)


@app.command()
def semver(
    base_file: Path = typer.Argument(..., help="Path to base (previous) schema file."),
    candidate_file: Path = typer.Argument(..., help="Path to candidate (updated) schema file."),
    current: str = typer.Option(
        "1.0.0", "--current", "-c", help="Current semantic version (e.g. 1.2.0)."
    ),
    mode: CompatibilityMode = typer.Option(
        CompatibilityMode.FULL, "--mode", "-m", help="Compatibility mode."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON recommendation."),
):
    """Compute and recommend the next Semantic Version (MAJOR, MINOR, PATCH)."""
    if not base_file.exists():
        console.print(f"[bold red]Error:[/bold red] Base file '{base_file}' does not exist.")
        raise typer.Exit(code=2)
    if not candidate_file.exists():
        console.print(
            f"[bold red]Error:[/bold red] Candidate file '{candidate_file}' does not exist."
        )
        raise typer.Exit(code=2)

    base_content = base_file.read_text(encoding="utf-8")
    candidate_content = candidate_file.read_text(encoding="utf-8")
    schema_type = SchemaComparator.detect_schema_type(candidate_content, candidate_file.name)

    rec = SemVerEngine.recommend_bump(
        base_content=base_content,
        candidate_content=candidate_content,
        schema_type=schema_type,
        current_version=current,
        mode=mode,
    )

    if json_output:
        console.print(json.dumps(rec.model_dump(), indent=2))
    else:
        render_semver_report(rec, base_file.name, candidate_file.name)

    if rec.is_breaking:
        raise typer.Exit(code=1)


@app.command()
def validate(
    file: Path = typer.Option(..., "--file", "-f", help="Schema file to validate against."),
    payload: Path = typer.Option(
        ..., "--payload", "-p", help="Path to JSON payload file or '-' for stdin."
    ),
    message: str | None = typer.Option(
        None, "--message", "-m", help="Target message or component entity name."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON validation result."),
):
    """Validate a JSON payload against a contract schema definition."""
    import sys

    if not file.exists():
        console.print(f"[bold red]Error:[/bold red] Schema file '{file}' does not exist.")
        raise typer.Exit(code=2)

    if str(payload) == "-":
        payload_data = sys.stdin.read()
    else:
        if not payload.exists():
            console.print(f"[bold red]Error:[/bold red] Payload file '{payload}' does not exist.")
            raise typer.Exit(code=2)
        payload_data = payload.read_text(encoding="utf-8")

    schema_content = file.read_text(encoding="utf-8")
    schema_type = SchemaComparator.detect_schema_type(schema_content, file.name)

    result = PayloadValidator.validate(
        schema_content=schema_content,
        payload=payload_data,
        schema_type=schema_type,
        target_entity=message,
    )

    if json_output:
        console.print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        render_validation_report(result, file.name)

    if not result.is_valid:
        raise typer.Exit(code=1)


@app.command()
def check(
    subject: str = typer.Option(
        ..., "--subject", "-s", help="Schema subject name in the registry."
    ),
    file: Path = typer.Option(..., "--file", "-f", help="Local candidate schema file to verify."),
    url: str = typer.Option(
        settings.registry_url,
        "--url",
        "-u",
        help="Registry base URL.",
    ),
    mode: CompatibilityMode | None = typer.Option(
        None,
        "--mode",
        "-m",
        help="Compatibility mode override.",
    ),
):
    """Verify candidate schema against the latest version stored in a remote registry."""
    if not file.exists():
        console.print(f"[bold red]Error:[/bold red] File '{file}' does not exist.")
        raise typer.Exit(code=2)

    content = file.read_text(encoding="utf-8")
    schema_type = SchemaComparator.detect_schema_type(content, file.name)

    base_url = url.rstrip("/")
    latest_url = f"{base_url}/v1/subjects/{subject}/versions/latest"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(latest_url)
            if resp.status_code == 404:
                console.print(
                    f"[yellow]Subject '{subject}' has no existing versions. Candidate will be V1 (compatible).[/yellow]"
                )
                raise typer.Exit(code=0)
            elif resp.status_code != 200:
                console.print(
                    f"[bold red]Registry returned error {resp.status_code}:[/bold red] {resp.text}"
                )
                raise typer.Exit(code=2)

            data = resp.json()
            base_content = data["schema"]
    except httpx.RequestError as exc:
        console.print(f"[bold red]Failed to connect to registry at {base_url}:[/bold red] {exc}")
        raise typer.Exit(code=2)

    eval_mode = mode or CompatibilityMode.FULL
    result = SchemaComparator.compare_strings(
        base_content=base_content,
        candidate_content=content,
        schema_type=schema_type,
        mode=eval_mode,
    )

    render_diff_table(
        result,
        base_name=f"{subject} (V{data.get('version', 'latest')})",
        candidate_name=file.name,
    )

    if not result.is_compatible:
        raise typer.Exit(code=1)


@app.command()
def register(
    subject: str = typer.Option(..., "--subject", "-s", help="Schema subject name."),
    file: Path = typer.Option(..., "--file", "-f", help="Schema file to register."),
    url: str = typer.Option(
        settings.registry_url,
        "--url",
        "-u",
        help="Registry base URL.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Bypass compatibility checking.",
    ),
):
    """Register a new schema version into the remote registry."""
    if not file.exists():
        console.print(f"[bold red]Error:[/bold red] File '{file}' does not exist.")
        raise typer.Exit(code=2)

    content = file.read_text(encoding="utf-8")
    schema_type = SchemaComparator.detect_schema_type(content, file.name)
    base_url = url.rstrip("/")
    register_url = f"{base_url}/v1/subjects/{subject}/versions"

    payload = {
        "schema": content,
        "schemaType": schema_type.value,
        "force": force,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(register_url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                console.print(
                    f"[bold green]Registered version {data['version']} for subject '{subject}'[/bold green] "
                    f"(ID: {data['id']}, Type: {data['schema_type']})"
                )
            elif resp.status_code == 422:
                console.print(
                    "[bold red]Schema registration rejected due to compatibility violations:[/bold red]"
                )
                detail = resp.json().get("detail", {})
                console.print(detail)
                raise typer.Exit(code=1)
            else:
                console.print(f"[bold red]Error {resp.status_code}:[/bold red] {resp.text}")
                raise typer.Exit(code=1)
    except httpx.RequestError as exc:
        console.print(f"[bold red]Connection error to {base_url}:[/bold red] {exc}")
        raise typer.Exit(code=2)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host address."),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port number."),
    reload: bool = typer.Option(False, "--reload", help="Enable hot reloading."),
    db: str | None = typer.Option(None, "--db", help="Database connection URL."),
):
    """Start the ContractHub registry server, Confluent wire API, and Web Diff Studio."""
    import os

    if db:
        os.environ["CONTRACTHUB_DB"] = db

    console.print(
        f"[bold cyan]Starting ContractHub Registry on[/bold cyan] [bold white]http://{host}:{port}[/bold white]"
    )
    console.print(f"  Web Diff Studio: [green]http://{host}:{port}/studio[/green]")
    console.print(f"  Swagger Docs:    [green]http://{host}:{port}/docs[/green]")
    console.print(f"  Confluent API:   [green]http://{host}:{port}/subjects[/green]")
    console.print()

    uvicorn.run(
        "contracthub.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    app()
