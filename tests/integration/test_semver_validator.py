"""Integration tests for SemVer and Payload Validator CLI & REST API."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from contracthub.api.server import app as fastapi_app
from contracthub.cli import app as cli_app

runner = CliRunner()
client = TestClient(fastapi_app)
EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


def test_cli_semver_breaking_major():
    base = str(EXAMPLES_DIR / "order_v1.proto")
    cand = str(EXAMPLES_DIR / "order_v2_breaking.proto")
    result = runner.invoke(cli_app, ["semver", base, cand, "--current", "1.2.0"])
    assert result.exit_code == 1  # exits 1 on breaking
    assert "SEMVER RECOMMENDATION: MAJOR BUMP" in result.output
    assert "2.0.0" in result.output


def test_cli_semver_compatible_minor():
    base = str(EXAMPLES_DIR / "order_v1.proto")
    cand = str(EXAMPLES_DIR / "order_v2_compatible.proto")
    result = runner.invoke(cli_app, ["semver", base, cand, "--current", "1.2.0", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["bump_type"] == "MINOR"
    assert data["recommended_version"] == "1.3.0"
    assert data["is_breaking"] is False


def test_cli_validate_success(tmp_path):
    schema_file = EXAMPLES_DIR / "customer_v1.json"
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(
        json.dumps({"id": "usr_1", "email": "test@example.com"}), encoding="utf-8"
    )

    result = runner.invoke(
        cli_app, ["validate", "--file", str(schema_file), "--payload", str(payload_file)]
    )
    assert result.exit_code == 0
    assert "PAYLOAD VALIDATION: PASSED" in result.output


def test_cli_validate_failure(tmp_path):
    schema_file = EXAMPLES_DIR / "customer_v1.json"
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(
        json.dumps({"id": 12345}), encoding="utf-8"
    )  # bad type and missing email

    result = runner.invoke(
        cli_app, ["validate", "--file", str(schema_file), "--payload", str(payload_file)]
    )
    assert result.exit_code == 1
    assert "PAYLOAD VALIDATION: FAILED" in result.output


def test_api_direct_semver():
    base_content = (EXAMPLES_DIR / "order_v1.proto").read_text(encoding="utf-8")
    cand_content = (EXAMPLES_DIR / "order_v2_breaking.proto").read_text(encoding="utf-8")

    resp = client.post(
        "/v1/semver",
        json={
            "baseSchema": base_content,
            "candidateSchema": cand_content,
            "current_version": "1.4.0",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["bump_type"] == "MAJOR"
    assert data["recommended_version"] == "2.0.0"


def test_api_direct_validate():
    schema_content = (EXAMPLES_DIR / "customer_v1.json").read_text(encoding="utf-8")
    resp = client.post(
        "/v1/validate",
        json={
            "schema": schema_content,
            "payload": {"id": "usr_10", "email": "alice@test.org"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
