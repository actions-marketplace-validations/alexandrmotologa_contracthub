"""Unit tests for Apache Avro Schema Parser and Comparator."""

from pathlib import Path

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, SchemaType
from contracthub.core.rules import AVRO_FIELD_ADDED_NO_DEFAULT, AVRO_TYPE_MUTATED
from contracthub.parsers.avro_parser import AvroParser

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


def test_avro_parser_basic():
    content = (EXAMPLES_DIR / "order_v1.avsc").read_text(encoding="utf-8")
    record = AvroParser.parse_string(content)
    assert record.name == "OrderEvent"
    assert record.namespace == "commerce.orders"
    assert "order_id" in record.fields
    assert record.fields["total_amount"].type == "double"
    assert record.fields["total_amount"].has_default is False


def test_avro_compatible_evolution():
    v1 = (EXAMPLES_DIR / "order_v1.avsc").read_text(encoding="utf-8")
    v2_comp = (EXAMPLES_DIR / "order_v2_compatible.avsc").read_text(encoding="utf-8")

    result = SchemaComparator.compare_strings(
        base_content=v1,
        candidate_content=v2_comp,
        schema_type=SchemaType.AVRO,
        mode=CompatibilityMode.FULL,
    )
    assert result.is_compatible is True
    assert result.breaking_count == 0


def test_avro_breaking_evolution():
    v1 = (EXAMPLES_DIR / "order_v1.avsc").read_text(encoding="utf-8")
    v2_break = (EXAMPLES_DIR / "order_v2_breaking.avsc").read_text(encoding="utf-8")

    result = SchemaComparator.compare_strings(
        base_content=v1,
        candidate_content=v2_break,
        schema_type=SchemaType.AVRO,
        mode=CompatibilityMode.FULL,
    )
    assert result.is_compatible is False
    assert result.breaking_count >= 2

    codes = [v.code for v in result.violations]
    assert AVRO_FIELD_ADDED_NO_DEFAULT in codes
    assert AVRO_TYPE_MUTATED in codes
