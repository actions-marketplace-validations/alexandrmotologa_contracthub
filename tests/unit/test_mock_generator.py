"""Unit tests for MockGenerator."""

from pathlib import Path

from contracthub.core.mock_generator import MockGenerator
from contracthub.core.models import SchemaType

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


def test_mock_proto():
    content = (EXAMPLES_DIR / "order_v1.proto").read_text(encoding="utf-8")
    mock_data = MockGenerator.generate(
        schema_content=content,
        schema_type=SchemaType.PROTOBUF,
        target_entity="OrderEvent",
    )
    assert isinstance(mock_data, dict)
    assert "order_id" in mock_data
    assert "customer_id" in mock_data
    assert "status" in mock_data
    assert "items" in mock_data
    assert isinstance(mock_data["items"], list)
    assert len(mock_data["items"]) == 2
    assert "item_id" in mock_data["items"][0]


def test_mock_avro():
    content = (EXAMPLES_DIR / "order_v1.avsc").read_text(encoding="utf-8")
    mock_data = MockGenerator.generate(
        schema_content=content,
        schema_type=SchemaType.AVRO,
    )
    assert isinstance(mock_data, dict)
    assert "order_id" in mock_data
    assert "total_amount" in mock_data
    assert mock_data["total_amount"] == 99.5


def test_mock_json_schema():
    content = (EXAMPLES_DIR / "customer_v1.json").read_text(encoding="utf-8")
    mock_data = MockGenerator.generate(
        schema_content=content,
        schema_type=SchemaType.JSON_SCHEMA,
    )
    assert isinstance(mock_data, dict)
    assert "id" in mock_data
    assert "email" in mock_data
    assert "@" in mock_data["email"]
