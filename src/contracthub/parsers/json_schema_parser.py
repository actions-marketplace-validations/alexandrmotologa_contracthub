"""JSON Schema AST Parser."""

import json
from typing import Any

import yaml

from contracthub.core.models import JsonSchemaAST


class JsonSchemaParser:
    """Parses JSON Schema definitions into AST models."""

    @classmethod
    def parse_string(cls, content: str) -> JsonSchemaAST:
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, yaml.YAMLError):
            data = yaml.safe_load(content)

        if not isinstance(data, dict):
            raise TypeError("Invalid JSON Schema: root must be an object.")

        return cls._parse_dict(data)

    @classmethod
    def parse_file(cls, path: str) -> JsonSchemaAST:
        with open(path, "r", encoding="utf-8") as f:
            return cls.parse_string(f.read())

    @classmethod
    def _parse_dict(cls, data: dict[str, Any]) -> JsonSchemaAST:
        title = data.get("title")
        schema_type = data.get("type")
        properties = data.get("properties", {})
        required = data.get("required", [])
        additional_props = data.get("additionalProperties")

        if not isinstance(properties, dict):
            properties = {}
        if not isinstance(required, list):
            required = []

        return JsonSchemaAST(
            title=title,
            type=str(schema_type) if schema_type else None,
            properties=properties,
            required=required,
            additional_properties=additional_props if isinstance(additional_props, bool) else None,
            raw=data,
        )
