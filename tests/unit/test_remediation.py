"""Unit tests for the Auto-Remediation Engine."""

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, SchemaType
from contracthub.core.remediation import AutoRemediator


def test_auto_remediation_proto_deleted_field():
    base = """
    syntax = "proto3";
    message User {
      string id = 1;
      string email = 2;
    }
    """

    # Candidate deleted field email (tag 2) without reserved
    candidate = """
    syntax = "proto3";
    message User {
      string id = 1;
    }
    """

    # Verify candidate was breaking
    res_before = SchemaComparator.compare_strings(
        base_content=base,
        candidate_content=candidate,
        schema_type=SchemaType.PROTOBUF,
        mode=CompatibilityMode.FULL,
    )
    assert res_before.is_compatible is False
    assert res_before.breaking_count == 1

    # Run auto-remediation
    fix_result = AutoRemediator.fix_proto(base_content=base, candidate_content=candidate)
    assert fix_result.was_modified is True
    assert "reserved 2;" in fix_result.fixed_content
    assert 'reserved "email";' in fix_result.fixed_content

    # Verify that the remediated candidate schema is now COMPATIBLE!
    res_after = SchemaComparator.compare_strings(
        base_content=base,
        candidate_content=fix_result.fixed_content,
        schema_type=SchemaType.PROTOBUF,
        mode=CompatibilityMode.FULL,
    )
    assert res_after.is_compatible is True
    assert res_after.breaking_count == 0
