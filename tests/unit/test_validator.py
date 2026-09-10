"""Unit tests for payload validator engine."""

from contracthub.core.models import SchemaType
from contracthub.core.validator import PayloadValidator


def test_validate_json_schema():
    schema = """
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "User",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name"]
    }
    """

    valid_payload = {"name": "Alice", "age": 30}
    res_valid = PayloadValidator.validate(schema, valid_payload, SchemaType.JSON_SCHEMA)
    assert res_valid.is_valid is True
    assert len(res_valid.errors) == 0

    invalid_payload = {"age": 30}  # missing name
    res_invalid = PayloadValidator.validate(schema, invalid_payload, SchemaType.JSON_SCHEMA)
    assert res_invalid.is_valid is False
    assert any("name" in err for err in res_invalid.errors)


def test_validate_proto():
    proto_schema = """
    syntax = "proto3";
    message Order {
        string order_id = 1;
        int32 amount = 2;
        bool is_paid = 3;
    }
    """

    valid_payload = {"order_id": "ord_100", "amount": 50, "is_paid": True}
    res = PayloadValidator.validate(proto_schema, valid_payload, SchemaType.PROTOBUF)
    assert res.is_valid is True

    # Bad type for amount
    invalid_payload = {"order_id": "ord_100", "amount": "fifty", "is_paid": True}
    res_bad = PayloadValidator.validate(proto_schema, invalid_payload, SchemaType.PROTOBUF)
    assert res_bad.is_valid is False
    assert any("amount" in err for err in res_bad.errors)


def test_validate_avro():
    avro_schema = """
    {
        "type": "record",
        "name": "PaymentEvent",
        "fields": [
            {"name": "payment_id", "type": "string"},
            {"name": "amount", "type": "double"},
            {"name": "status", "type": "string", "default": "PENDING"}
        ]
    }
    """

    valid_payload = {"payment_id": "pay_1", "amount": 99.9}
    res = PayloadValidator.validate(avro_schema, valid_payload, SchemaType.AVRO)
    assert res.is_valid is True

    # Missing required field with no default
    invalid_payload = {"amount": 99.9}
    res_bad = PayloadValidator.validate(avro_schema, invalid_payload, SchemaType.AVRO)
    assert res_bad.is_valid is False
    assert any("payment_id" in err for err in res_bad.errors)
