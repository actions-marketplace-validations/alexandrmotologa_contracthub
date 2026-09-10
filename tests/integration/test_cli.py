"""Integration tests for ContractHub CLI."""

from pathlib import Path

from typer.testing import CliRunner

from contracthub.cli import app

runner = CliRunner()
EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "ContractHub version" in result.output


def test_cli_diff_compatible():
    base = str(EXAMPLES_DIR / "order_v1.proto")
    cand = str(EXAMPLES_DIR / "order_v2_compatible.proto")
    result = runner.invoke(app, ["diff", base, cand, "--mode", "FULL"])
    assert result.exit_code == 0
    assert "COMPATIBILITY VERIFICATION: PASSED" in result.output


def test_cli_diff_breaking():
    base = str(EXAMPLES_DIR / "order_v1.proto")
    cand = str(EXAMPLES_DIR / "order_v2_breaking.proto")
    result = runner.invoke(app, ["diff", base, cand, "--mode", "FULL"])
    assert result.exit_code == 1
    assert "COMPATIBILITY VERIFICATION: FAILED" in result.output
    assert "PROTO_TAG_MUTATED" in result.output
    assert "PROTO_FIELD_REMOVED" in result.output


def test_cli_diff_json_format():
    base = str(EXAMPLES_DIR / "customer_v1.json")
    cand = str(EXAMPLES_DIR / "customer_v2_breaking.json")
    result = runner.invoke(app, ["diff", base, cand, "--format", "json"])
    assert result.exit_code == 1
    assert '"is_compatible": false' in result.output
    assert "JSON_SCHEMA_REQUIRED_ADDED" in result.output


def test_cli_diff_missing_file():
    result = runner.invoke(app, ["diff", "non_existent.proto", "also_missing.proto"])
    assert result.exit_code == 2
