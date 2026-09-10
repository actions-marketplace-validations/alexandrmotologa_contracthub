"""Integration tests for GraphQL workflows via CLI."""

from typer.testing import CliRunner

from contracthub.cli import app as cli_app

runner = CliRunner()


def test_cli_diff_graphql_breaking():
    result = runner.invoke(
        cli_app,
        [
            "diff",
            "examples/user_v1.graphql",
            "examples/user_v2_breaking.graphql",
            "--mode",
            "BACKWARD",
        ],
    )
    assert result.exit_code == 1
    assert "GRAPHQL_FIELD_REMOVED" in result.output
    assert "CreateUserInput.inviteCode" in result.output
    assert "GRAPHQL_INPUT_FIELD" in result.output


def test_cli_diff_graphql_compatible():
    result = runner.invoke(
        cli_app,
        [
            "diff",
            "examples/user_v1.graphql",
            "examples/user_v2_compatible.graphql",
            "--mode",
            "BACKWARD",
        ],
    )
    assert result.exit_code == 0
    assert "No breaking changes detected" in result.output or "PASSED" in result.output


def test_cli_semver_graphql():
    # Breaking -> MAJOR bump
    res_breaking = runner.invoke(
        cli_app,
        [
            "semver",
            "examples/user_v1.graphql",
            "examples/user_v2_breaking.graphql",
            "--current",
            "1.2.0",
        ],
    )
    assert res_breaking.exit_code == 1
    assert "MAJOR" in res_breaking.output
    assert "2.0.0" in res_breaking.output

    # Compatible additions -> MINOR bump
    res_compat = runner.invoke(
        cli_app,
        [
            "semver",
            "examples/user_v1.graphql",
            "examples/user_v2_compatible.graphql",
            "--current",
            "1.2.0",
        ],
    )
    assert res_compat.exit_code == 0
    assert "MINOR" in res_compat.output
    assert "1.3.0" in res_compat.output


def test_cli_codegen_graphql():
    result = runner.invoke(
        cli_app,
        ["codegen", "--file", "examples/user_v1.graphql", "--target", "typescript"],
    )
    assert result.exit_code == 0
    assert "export interface User" in result.output
    assert "export enum UserRole" in result.output


def test_cli_mock_graphql():
    result = runner.invoke(
        cli_app,
        ["mock", "--file", "examples/user_v1.graphql"],
    )
    assert result.exit_code == 0
    assert '"id":' in result.output
    assert '"name":' in result.output
