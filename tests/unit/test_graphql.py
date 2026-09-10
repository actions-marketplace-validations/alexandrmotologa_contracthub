"""Unit tests for GraphQL SDL parser, compatibility rules, mock, and codegen."""

from pathlib import Path

from contracthub.core.codegen import CodeGenerator
from contracthub.core.comparator import SchemaComparator
from contracthub.core.mock_generator import MockGenerator
from contracthub.core.models import CompatibilityMode, SchemaType
from contracthub.core.rules import (
    GRAPHQL_ENUM_VALUE_REMOVED,
    GRAPHQL_FIELD_REMOVED,
    GRAPHQL_FIELD_TYPE_CHANGED,
    GRAPHQL_INPUT_FIELD_REQUIRED_ADDED,
)
from contracthub.core.validator import PayloadValidator
from contracthub.parsers.graphql_parser import GraphQLParser

EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"


def test_graphql_parser():
    content = (EXAMPLES / "user_v1.graphql").read_text(encoding="utf-8")
    ast = GraphQLParser.parse_string(content)

    assert "UserRole" in ast.enums
    assert ast.enums["UserRole"].values == ["ADMIN", "MEMBER", "GUEST"]

    assert "User" in ast.types
    user_fields = ast.types["User"].fields
    assert "id" in user_fields
    assert user_fields["id"].is_non_null is True
    assert "name" in user_fields
    assert user_fields["name"].type_name == "String"
    assert "friends" in user_fields
    assert user_fields["friends"].is_list is True

    assert "CreateUserInput" in ast.inputs
    input_fields = ast.inputs["CreateUserInput"].fields
    assert "name" in input_fields
    assert input_fields["name"].is_non_null is True


def test_graphql_compatibility_breaking():
    base = (EXAMPLES / "user_v1.graphql").read_text(encoding="utf-8")
    cand = (EXAMPLES / "user_v2_breaking.graphql").read_text(encoding="utf-8")

    result = SchemaComparator.compare_strings(
        base_content=base,
        candidate_content=cand,
        schema_type=SchemaType.GRAPHQL,
        mode=CompatibilityMode.BACKWARD,
    )

    assert result.is_compatible is False
    codes = {v.code for v in result.violations}
    assert GRAPHQL_FIELD_REMOVED in codes
    assert GRAPHQL_FIELD_TYPE_CHANGED in codes
    assert GRAPHQL_INPUT_FIELD_REQUIRED_ADDED in codes
    assert GRAPHQL_ENUM_VALUE_REMOVED in codes


def test_graphql_compatibility_compatible():
    base = (EXAMPLES / "user_v1.graphql").read_text(encoding="utf-8")
    cand = (EXAMPLES / "user_v2_compatible.graphql").read_text(encoding="utf-8")

    result = SchemaComparator.compare_strings(
        base_content=base,
        candidate_content=cand,
        schema_type=SchemaType.GRAPHQL,
        mode=CompatibilityMode.BACKWARD,
    )

    assert result.is_compatible is True
    assert result.breaking_count == 0


def test_graphql_codegen():
    content = (EXAMPLES / "user_v1.graphql").read_text(encoding="utf-8")

    ts_code = CodeGenerator.generate(content, target="typescript", schema_type=SchemaType.GRAPHQL)
    assert "export enum UserRole {" in ts_code
    assert "export interface User {" in ts_code
    assert "export interface CreateUserInput {" in ts_code
    assert "id: string;" in ts_code

    py_code = CodeGenerator.generate(content, target="pydantic", schema_type=SchemaType.GRAPHQL)
    assert "class UserRole(StrEnum):" in py_code
    assert "class User(BaseModel):" in py_code
    assert "id: str" in py_code


def test_graphql_mock_generation():
    content = (EXAMPLES / "user_v1.graphql").read_text(encoding="utf-8")
    mock = MockGenerator.generate(content, schema_type=SchemaType.GRAPHQL, target_entity="User")

    assert isinstance(mock, dict)
    assert "id" in mock
    assert "name" in mock
    assert "role" in mock
    assert mock["role"] == "ADMIN"
    assert isinstance(mock["friends"], list)


def test_graphql_payload_validation():
    content = (EXAMPLES / "user_v1.graphql").read_text(encoding="utf-8")

    # Valid payload
    valid_payload = {
        "id": "u123",
        "name": "Alex",
        "email": "alex@example.com",
        "role": "ADMIN",
        "friends": [],
    }
    res_valid = PayloadValidator.validate(content, valid_payload, target_entity="User")
    assert res_valid.is_valid is True

    # Invalid payload (missing non-null field 'name')
    invalid_payload = {
        "id": "u123",
        "role": "ADMIN",
    }
    res_invalid = PayloadValidator.validate(content, invalid_payload, target_entity="User")
    assert res_invalid.is_valid is False
    assert any("Missing required non-null GraphQL field 'name'" in e for e in res_invalid.errors)
