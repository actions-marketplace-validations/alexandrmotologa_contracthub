"""Integration tests for codegen CLI command and REST API endpoints."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient
from typer.testing import CliRunner

from contracthub.api.server import create_app
from contracthub.cli import app as cli_app
from contracthub.storage.database import Base, get_engine

runner = CliRunner()


@pytest.fixture(autouse=True)
def clean_db():
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_cli_codegen_stdout():
    result = runner.invoke(
        cli_app,
        ["codegen", "--file", "examples/order_v1.proto", "--target", "typescript"],
    )
    assert result.exit_code == 0
    assert "export interface OrderEvent" in result.output
    assert "export enum OrderStatus" in result.output


def test_cli_codegen_output_file(tmp_path: Path):
    out_file = tmp_path / "models.py"
    result = runner.invoke(
        cli_app,
        [
            "codegen",
            "--file",
            "examples/order_v1.avsc",
            "--target",
            "pydantic",
            "--output",
            str(out_file),
        ],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "class OrderEvent(BaseModel):" in content
    assert "total_amount: float" in content


def test_api_direct_codegen(client: TestClient):
    schema = Path("examples/customer_v1.json").read_text(encoding="utf-8")
    resp = client.post(
        "/v1/codegen",
        json={
            "schema": schema,
            "target": "typescript",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["target"] == "typescript"
    assert data["schema_type"] == "JSON_SCHEMA"
    assert "export interface Customer {" in data["code"]


def test_api_subject_version_codegen(client: TestClient):
    subject = "orders-codegen-test"
    schema = Path("examples/order_v1.proto").read_text(encoding="utf-8")

    # Register subject version first
    reg_resp = client.post(
        f"/v1/subjects/{subject}/versions",
        json={
            "schema": schema,
            "schemaType": "PROTOBUF",
        },
    )
    assert reg_resp.status_code == 200

    # Request codegen from registered version
    cg_resp = client.get(f"/v1/subjects/{subject}/versions/latest/codegen?target=pydantic")
    assert cg_resp.status_code == 200
    cg_data = cg_resp.json()
    assert cg_data["target"] == "pydantic"
    assert cg_data["schema_type"] == "PROTOBUF"
    assert "class OrderEvent(BaseModel):" in cg_data["code"]
    assert "class OrderStatus(IntEnum):" in cg_data["code"]
