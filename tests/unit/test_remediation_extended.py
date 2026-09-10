"""Unit tests for extended auto-remediation (Avro, OpenAPI, GraphQL) and git hooks."""

import json
from pathlib import Path

from contracthub.core.hooks import init_git_hooks
from contracthub.core.models import SchemaType
from contracthub.core.remediation import AutoRemediator


def test_remediation_avro():
    base = json.dumps(
        {
            "type": "record",
            "name": "Order",
            "fields": [{"name": "id", "type": "string"}],
        }
    )
    # Candidate adds newly created field "discount" with no default
    candidate = json.dumps(
        {
            "type": "record",
            "name": "Order",
            "fields": [
                {"name": "id", "type": "string"},
                {"name": "discount", "type": "double"},
            ],
        }
    )

    result = AutoRemediator.fix(base, candidate, schema_type=SchemaType.AVRO)
    assert result.was_modified is True
    fixed_data = json.loads(result.fixed_content)
    discount_field = next(f for f in fixed_data["fields"] if f["name"] == "discount")
    assert "default" in discount_field
    assert discount_field["default"] == 0.0


def test_remediation_openapi():
    base = json.dumps(
        {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/users": {
                    "get": {"responses": {"200": {"description": "ok"}}},
                    "delete": {"responses": {"200": {"description": "ok"}}},
                }
            },
        }
    )
    # Candidate removes DELETE method
    candidate = json.dumps(
        {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/users": {
                    "get": {"responses": {"200": {"description": "ok"}}},
                }
            },
        }
    )

    result = AutoRemediator.fix(base, candidate, schema_type=SchemaType.OPENAPI)
    assert result.was_modified is True
    fixed_data = json.loads(result.fixed_content)
    assert "delete" in fixed_data["paths"]["/users"]
    assert fixed_data["paths"]["/users"]["delete"]["deprecated"] is True


def test_remediation_graphql():
    base = """
type User {
  id: ID!
  name: String!
}
"""
    # Candidate removes 'name'
    candidate = """
type User {
  id: ID!
}
"""
    result = AutoRemediator.fix(base, candidate, schema_type=SchemaType.GRAPHQL)
    assert result.was_modified is True
    assert "name: String! @deprecated" in result.fixed_content


def test_init_git_hooks(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    success, _msgs = init_git_hooks(tmp_path)
    assert success is True
    assert (git_dir / "hooks" / "pre-commit").exists()
    assert (tmp_path / ".pre-commit-config.yaml").exists()

    hook_content = (git_dir / "hooks" / "pre-commit").read_text(encoding="utf-8")
    assert "contracthub scan" in hook_content


def test_init_git_hooks_non_git_dir(tmp_path: Path):
    success, msgs = init_git_hooks(tmp_path)
    assert success is False
    assert any("not a git repository" in m for m in msgs)
