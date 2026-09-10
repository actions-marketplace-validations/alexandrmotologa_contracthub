"""Unit tests for SemVer recommendation engine."""

from contracthub.core.models import SchemaType
from contracthub.core.semver import SemVerEngine, parse_semver


def test_parse_semver():
    assert parse_semver("1.2.3") == (1, 2, 3)
    assert parse_semver("v2.5.10") == (2, 5, 10)
    assert parse_semver("invalid") == (1, 0, 0)


def test_semver_major_on_breaking_proto():
    base_proto = """
    syntax = "proto3";
    message Order {
        string order_id = 1;
        int32 quantity = 2;
    }
    """

    # Breaking change: field deleted without reserved tag
    cand_proto = """
    syntax = "proto3";
    message Order {
        string order_id = 1;
    }
    """

    rec = SemVerEngine.recommend_bump(
        base_content=base_proto,
        candidate_content=cand_proto,
        schema_type=SchemaType.PROTOBUF,
        current_version="1.4.2",
    )

    assert rec.bump_type == "MAJOR"
    assert rec.recommended_version == "2.0.0"
    assert rec.is_breaking is True
    assert len(rec.breaking_changes) > 0


def test_semver_minor_on_compatible_addition():
    base_proto = """
    syntax = "proto3";
    message Order {
        string order_id = 1;
    }
    """

    # Compatible addition: new field added
    cand_proto = """
    syntax = "proto3";
    message Order {
        string order_id = 1;
        int32 quantity = 2;
    }
    """

    rec = SemVerEngine.recommend_bump(
        base_content=base_proto,
        candidate_content=cand_proto,
        schema_type=SchemaType.PROTOBUF,
        current_version="1.4.2",
    )

    assert rec.bump_type == "MINOR"
    assert rec.recommended_version == "1.5.0"
    assert rec.is_breaking is False


def test_semver_patch_on_identical_ast():
    base_proto = """
    syntax = "proto3";
    message Order {
        string order_id = 1;
    }
    """

    cand_proto = """
    syntax = "proto3";
    message Order {
        string order_id = 1;
    }
    """

    rec = SemVerEngine.recommend_bump(
        base_content=base_proto,
        candidate_content=cand_proto,
        schema_type=SchemaType.PROTOBUF,
        current_version="1.4.2",
    )

    assert rec.bump_type == "PATCH"
    assert rec.recommended_version == "1.4.3"
    assert rec.is_breaking is False
