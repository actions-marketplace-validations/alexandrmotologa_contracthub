"""Unit tests for the Schema Comparator and Breaking Change Rules."""

from pathlib import Path

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, SchemaType
from contracthub.core.rules import (
    JSON_SCHEMA_REQUIRED_ADDED,
    PROTO_ENUM_VALUE_REMOVED,
    PROTO_FIELD_REMOVED,
    PROTO_TAG_MUTATED,
    PROTO_TYPE_CHANGED,
    REST_ENDPOINT_REMOVED,
    REST_REQUIRED_PARAM_ADDED,
    REST_STATUS_MUTATED,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


def test_proto_compatible_evolution():
    v1 = (EXAMPLES_DIR / "order_v1.proto").read_text(encoding="utf-8")
    v2 = (EXAMPLES_DIR / "order_v2_compatible.proto").read_text(encoding="utf-8")

    result = SchemaComparator.compare_strings(
        base_content=v1,
        candidate_content=v2,
        schema_type=SchemaType.PROTOBUF,
        mode=CompatibilityMode.FULL,
    )

    assert result.is_compatible is True
    assert result.breaking_count == 0


def test_proto_breaking_changes_detected():
    v1 = (EXAMPLES_DIR / "order_v1.proto").read_text(encoding="utf-8")
    v2 = (EXAMPLES_DIR / "order_v2_breaking.proto").read_text(encoding="utf-8")

    result = SchemaComparator.compare_strings(
        base_content=v1,
        candidate_content=v2,
        schema_type=SchemaType.PROTOBUF,
        mode=CompatibilityMode.FULL,
    )

    assert result.is_compatible is False
    assert result.breaking_count >= 4

    codes = [v.code for v in result.violations]
    assert PROTO_TAG_MUTATED in codes
    assert PROTO_FIELD_REMOVED in codes
    assert PROTO_TYPE_CHANGED in codes
    assert PROTO_ENUM_VALUE_REMOVED in codes


def test_openapi_breaking_changes_detected():
    v1 = (EXAMPLES_DIR / "petstore_v1.json").read_text(encoding="utf-8")
    v2 = (EXAMPLES_DIR / "petstore_v2_breaking.json").read_text(encoding="utf-8")

    result = SchemaComparator.compare_strings(
        base_content=v1,
        candidate_content=v2,
        schema_type=SchemaType.OPENAPI,
        mode=CompatibilityMode.FULL,
    )

    assert result.is_compatible is False
    codes = [v.code for v in result.violations]
    assert REST_ENDPOINT_REMOVED in codes
    assert REST_REQUIRED_PARAM_ADDED in codes
    assert REST_STATUS_MUTATED in codes


def test_json_schema_compatible_and_breaking():
    v1 = (EXAMPLES_DIR / "customer_v1.json").read_text(encoding="utf-8")
    v2_comp = (EXAMPLES_DIR / "customer_v2_compatible.json").read_text(encoding="utf-8")
    v2_break = (EXAMPLES_DIR / "customer_v2_breaking.json").read_text(encoding="utf-8")

    # Compatible check
    res_comp = SchemaComparator.compare_strings(
        base_content=v1,
        candidate_content=v2_comp,
        schema_type=SchemaType.JSON_SCHEMA,
        mode=CompatibilityMode.FULL,
    )
    assert res_comp.is_compatible is True
    assert res_comp.breaking_count == 0

    # Breaking check
    res_break = SchemaComparator.compare_strings(
        base_content=v1,
        candidate_content=v2_break,
        schema_type=SchemaType.JSON_SCHEMA,
        mode=CompatibilityMode.FULL,
    )
    assert res_break.is_compatible is False
    codes = [v.code for v in res_break.violations]
    assert JSON_SCHEMA_REQUIRED_ADDED in codes
