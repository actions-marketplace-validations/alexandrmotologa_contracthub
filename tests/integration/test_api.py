"""Integration tests for ContractHub Native and Confluent APIs."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from contracthub.api.server import create_app
from contracthub.storage.database import Base, get_engine

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
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health_check(client: TestClient):
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_studio_page(client: TestClient):
    resp = client.get("/studio")
    assert resp.status_code == 200
    assert "<!DOCTYPE html>" in resp.text
    assert "ContractHub Studio" in resp.text
    assert "Payload Validator" in resp.text
    assert "Client Codegen" in resp.text
    assert "Auto-Fix Candidate" in resp.text
    assert "GRAPHQL" in resp.text


def test_direct_fix_endpoint(client: TestClient):
    base_proto = 'syntax = "proto3"; message User { string id = 1; string email = 2; }'
    cand_proto = 'syntax = "proto3"; message User { string id = 1; }'

    resp = client.post(
        "/v1/fix",
        json={
            "baseSchema": base_proto,
            "candidateSchema": cand_proto,
            "schemaType": "PROTOBUF",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "reserved 2" in data["fixed_content"]
    assert len(data["actions"]) > 0
    assert data["actions"][0]["rule_code"] == "PROTO_FIELD_REMOVED"


def test_direct_diff_endpoint(client: TestClient):
    v1 = (EXAMPLES_DIR / "order_v1.proto").read_text(encoding="utf-8")
    v2_break = (EXAMPLES_DIR / "order_v2_breaking.proto").read_text(encoding="utf-8")

    resp = client.post(
        "/v1/diff",
        json={
            "baseSchema": v1,
            "candidateSchema": v2_break,
            "schemaType": "PROTOBUF",
            "mode": "FULL",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_compatible"] is False
    assert len(data["violations"]) > 0


def test_subject_registration_and_enforcement(client: TestClient):
    v1 = (EXAMPLES_DIR / "order_v1.proto").read_text(encoding="utf-8")
    v2_comp = (EXAMPLES_DIR / "order_v2_compatible.proto").read_text(encoding="utf-8")
    v2_break = (EXAMPLES_DIR / "order_v2_breaking.proto").read_text(encoding="utf-8")

    # 1. Register V1
    resp1 = client.post(
        "/v1/subjects/orders-value/versions",
        json={"schema": v1, "schemaType": "PROTOBUF"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["version"] == 1
    assert data1["id"] == 1

    # 2. Try registering breaking V2 (should be rejected with 422)
    resp_break = client.post(
        "/v1/subjects/orders-value/versions",
        json={"schema": v2_break, "schemaType": "PROTOBUF"},
    )
    assert resp_break.status_code == 422
    assert (
        "Candidate schema violates compatibility invariants."
        in resp_break.json()["detail"]["message"]
    )

    # 3. Register compatible V2 (should succeed with version 2)
    resp_comp = client.post(
        "/v1/subjects/orders-value/versions",
        json={"schema": v2_comp, "schemaType": "PROTOBUF"},
    )
    assert resp_comp.status_code == 200
    data_comp = resp_comp.json()
    assert data_comp["version"] == 2

    # 4. Fetch latest version
    resp_latest = client.get("/v1/subjects/orders-value/versions/latest")
    assert resp_latest.status_code == 200
    assert resp_latest.json()["version"] == 2


def test_confluent_wire_compatibility(client: TestClient):
    v1 = (EXAMPLES_DIR / "order_v1.proto").read_text(encoding="utf-8")
    v2_comp = (EXAMPLES_DIR / "order_v2_compatible.proto").read_text(encoding="utf-8")
    v2_break = (EXAMPLES_DIR / "order_v2_breaking.proto").read_text(encoding="utf-8")

    # 1. Confluent register schema
    resp = client.post(
        "/subjects/kafka-order-value/versions",
        json={"schema": v1, "schemaType": "PROTOBUF"},
    )
    assert resp.status_code == 200
    schema_id = resp.json()["id"]

    # 2. Get by Schema ID
    resp_id = client.get(f"/schemas/ids/{schema_id}")
    assert resp_id.status_code == 200
    assert resp_id.json()["schema"] == v1

    # 3. Test compatibility dry-run endpoint (Confluent wire format)
    resp_check_comp = client.post(
        "/compatibility/subjects/kafka-order-value/versions/latest",
        json={"schema": v2_comp, "schemaType": "PROTOBUF"},
    )
    assert resp_check_comp.status_code == 200
    assert resp_check_comp.json()["is_compatible"] is True

    resp_check_break = client.post(
        "/compatibility/subjects/kafka-order-value/versions/latest",
        json={"schema": v2_break, "schemaType": "PROTOBUF"},
    )
    assert resp_check_break.status_code == 200
    assert resp_check_break.json()["is_compatible"] is False
