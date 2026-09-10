"""Apache Avro AST Parser.

Parses Apache Avro JSON schema specifications (.avsc) into structured AST objects.
"""

import json
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AvroFieldAST(BaseModel):
    name: str
    type: Any
    has_default: bool = False
    default: Any | None = None
    doc: str | None = None


class AvroRecordAST(BaseModel):
    name: str
    namespace: str | None = None
    doc: str | None = None
    fields: dict[str, AvroFieldAST] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class AvroParser:
    """Extracts structural AST from Apache Avro (.avsc) schema documents."""

    @classmethod
    def parse_string(cls, content: str) -> AvroRecordAST:
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, yaml.YAMLError):
            data = yaml.safe_load(content)

        if not isinstance(data, dict):
            raise TypeError("Invalid Avro specification: root must be a JSON record object.")

        name = data.get("name", "UnnamedRecord")
        namespace = data.get("namespace")
        doc = data.get("doc")

        record = AvroRecordAST(
            name=name,
            namespace=namespace,
            doc=doc,
            raw=data,
        )

        raw_fields = data.get("fields", [])
        if isinstance(raw_fields, list):
            for f in raw_fields:
                if isinstance(f, dict) and "name" in f:
                    f_name = f["name"]
                    f_type = f.get("type")
                    has_default = "default" in f
                    f_default = f.get("default")
                    f_doc = f.get("doc")

                    record.fields[f_name] = AvroFieldAST(
                        name=f_name,
                        type=f_type,
                        has_default=has_default,
                        default=f_default,
                        doc=f_doc,
                    )

        return record

    @classmethod
    def parse_file(cls, path: str) -> AvroRecordAST:
        with open(path, "r", encoding="utf-8") as f:
            return cls.parse_string(f.read())
