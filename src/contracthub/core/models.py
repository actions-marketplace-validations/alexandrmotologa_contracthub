"""Domain models and AST schema abstractions for ContractHub."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BREAKING = "BREAKING"


class CompatibilityMode(str, Enum):
    BACKWARD = "BACKWARD"
    FORWARD = "FORWARD"
    FULL = "FULL"
    NONE = "NONE"


class SchemaType(str, Enum):
    PROTOBUF = "PROTOBUF"
    OPENAPI = "OPENAPI"
    JSON_SCHEMA = "JSON_SCHEMA"
    AVRO = "AVRO"


class Violation(BaseModel):
    code: str
    severity: Severity = Severity.BREAKING
    path: str
    message: str
    suggestion: str | None = None


class CompatibilityResult(BaseModel):
    is_compatible: bool
    mode: CompatibilityMode
    violations: list[Violation] = Field(default_factory=list)
    total_checks: int = 0

    @property
    def breaking_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.BREAKING)

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.WARNING)


# Proto3 AST models
class ProtoFieldAST(BaseModel):
    name: str
    tag: int
    type: str
    cardinality: str = "singular"  # singular, optional, repeated, map
    is_reserved: bool = False
    comments: list[str] = Field(default_factory=list)


class ProtoEnumFieldAST(BaseModel):
    name: str
    number: int


class ProtoEnumAST(BaseModel):
    name: str
    values: dict[str, int] = Field(default_factory=dict)  # name -> number
    reserved_numbers: list[int] = Field(default_factory=list)
    reserved_names: list[str] = Field(default_factory=list)


class ProtoMessageAST(BaseModel):
    name: str
    fields: dict[str, ProtoFieldAST] = Field(default_factory=dict)  # field name -> field
    fields_by_tag: dict[int, ProtoFieldAST] = Field(default_factory=dict)  # tag -> field
    reserved_tags: list[int] = Field(default_factory=list)
    reserved_names: list[str] = Field(default_factory=list)
    nested_messages: dict[str, "ProtoMessageAST"] = Field(default_factory=dict)
    nested_enums: dict[str, ProtoEnumAST] = Field(default_factory=dict)


class ProtoAST(BaseModel):
    syntax: str = "proto3"
    package: str | None = None
    messages: dict[str, ProtoMessageAST] = Field(default_factory=dict)
    enums: dict[str, ProtoEnumAST] = Field(default_factory=dict)
    imports: list[str] = Field(default_factory=list)


# OpenAPI AST models
class OpenApiParameterAST(BaseModel):
    name: str
    location: str  # query, path, header, cookie
    required: bool = False
    type: str | None = None


class OpenApiResponseAST(BaseModel):
    status_code: str
    description: str | None = None
    content_types: dict[str, Any] = Field(default_factory=dict)


class OpenApiOperationAST(BaseModel):
    method: str
    operation_id: str | None = None
    parameters: dict[str, OpenApiParameterAST] = Field(default_factory=dict)
    request_body_required: bool = False
    request_body_types: dict[str, Any] = Field(default_factory=dict)
    responses: dict[str, OpenApiResponseAST] = Field(default_factory=dict)


class OpenApiPathAST(BaseModel):
    path: str
    operations: dict[str, OpenApiOperationAST] = Field(default_factory=dict)


class OpenApiAST(BaseModel):
    version: str
    title: str
    paths: dict[str, OpenApiPathAST] = Field(default_factory=dict)
    schemas: dict[str, Any] = Field(default_factory=dict)


# JSON Schema AST models
class JsonSchemaAST(BaseModel):
    title: str | None = None
    type: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
