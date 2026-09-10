"""Integration tests for all expanded ContractHub capabilities."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient
from typer.testing import CliRunner

from contracthub.api.server import create_app
from contracthub.cli import app
from contracthub.storage.database import Base, get_engine

runner = CliRunner()
EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


@pytest.fixture(autouse=True)
def clean_db():
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app_instance = create_app()
    with TestClient(app_instance) as c:
        yield c


def test_cli_mock_command():
    proto_file = str(EXAMPLES_DIR / "order_v1.proto")
    # Default (first message OrderItem)
    result = runner.invoke(app, ["mock", "--file", proto_file])
    assert result.exit_code == 0
    assert "item_id" in result.output

    # Specific message OrderEvent
    result_event = runner.invoke(app, ["mock", "--file", proto_file, "--message", "OrderEvent"])
    assert result_event.exit_code == 0
    assert "order_id" in result_event.output
    assert "customer_id" in result_event.output


def test_cli_fix_command_dry_run():
    base = str(EXAMPLES_DIR / "order_v1.proto")
    cand = str(EXAMPLES_DIR / "order_v2_breaking.proto")
    result = runner.invoke(app, ["fix", cand, "--base", base, "--dry-run"])
    assert result.exit_code == 0
    assert "auto-remediation" in result.output.lower()
    assert "reserved 2;" in result.output


def test_cli_scan_command_json():
    result = runner.invoke(app, ["scan", "--against", "HEAD", "--format", "json"])
    assert result.exit_code == 0
    assert '"total_scanned":' in result.output


def test_api_mock_endpoint(client: TestClient):
    proto_content = (EXAMPLES_DIR / "order_v1.proto").read_text(encoding="utf-8")
    resp = client.post(
        "/v1/mock",
        json={"schema": proto_content, "schemaType": "PROTOBUF", "targetEntity": "OrderEvent"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "order_id" in data
    assert "items" in data


def test_api_webhooks_crud(client: TestClient):
    # 1. Create webhook
    resp = client.post(
        "/v1/webhooks",
        json={
            "url": "https://example.com/webhook",
            "secret": "s3cr3t",
            "events": "VERSION_REGISTERED",
        },
    )
    assert resp.status_code == 200
    wh = resp.json()
    assert wh["url"] == "https://example.com/webhook"
    wh_id = wh["id"]

    # 2. List webhooks
    resp_list = client.get("/v1/webhooks")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 1

    # 3. Delete webhook
    resp_del = client.delete(f"/v1/webhooks/{wh_id}")
    assert resp_del.status_code == 200

    # 4. Verify empty
    resp_list_after = client.get("/v1/webhooks")
    assert resp_list_after.status_code == 200
    assert len(resp_list_after.json()) == 0
