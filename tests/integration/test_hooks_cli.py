"""Integration tests for init-hooks and extended fix CLI commands."""

import json
from pathlib import Path

from typer.testing import CliRunner

from contracthub.cli import app as cli_app

runner = CliRunner()


def test_cli_init_hooks(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    result = runner.invoke(cli_app, ["init-hooks", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Installed executable Git hook" in result.output
    assert (git_dir / "hooks" / "pre-commit").exists()
    assert (tmp_path / ".pre-commit-config.yaml").exists()


def test_cli_fix_avro(tmp_path: Path):
    base_file = tmp_path / "base.avsc"
    cand_file = tmp_path / "cand.avsc"

    base_file.write_text(
        json.dumps(
            {
                "type": "record",
                "name": "Payment",
                "fields": [{"name": "id", "type": "string"}],
            }
        ),
        encoding="utf-8",
    )
    cand_file.write_text(
        json.dumps(
            {
                "type": "record",
                "name": "Payment",
                "fields": [
                    {"name": "id", "type": "string"},
                    {"name": "currency", "type": "string"},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli_app,
        ["fix", "--base", str(base_file), "--candidate", str(cand_file), "--in-place"],
    )
    assert result.exit_code == 0
    assert "Successfully applied fixes" in result.output

    remediated = json.loads(cand_file.read_text(encoding="utf-8"))
    curr_field = next(f for f in remediated["fields"] if f["name"] == "currency")
    assert "default" in curr_field
    assert curr_field["default"] == ""
