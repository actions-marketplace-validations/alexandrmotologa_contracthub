"""Live payload validator verifying JSON data against registered contracts."""

import json
from typing import Any

import jsonschema
from pydantic import BaseModel, Field

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import ProtoAST, ProtoMessageAST, SchemaType
from contracthub.parsers.avro_parser import AvroParser, AvroRecordAST
from contracthub.parsers.json_schema_parser import JsonSchemaParser
from contracthub.parsers.openapi_parser import OpenApiParser
from contracthub.parsers.proto_parser import ProtoParser


class ValidationResult(BaseModel):
    """Result of payload validation against a contract schema."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    schema_type: SchemaType
    target_entity: str | None = None


class PayloadValidator:
    """Validates real or simulated JSON payloads against schema specifications."""

    @classmethod
    def validate(
        cls,
        schema_content: str,
        payload: Any,
        schema_type: SchemaType | None = None,
        target_entity: str | None = None,
    ) -> ValidationResult:
        detected_type = schema_type or SchemaComparator.detect_schema_type(schema_content)

        # Parse string payload if json string was passed
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, ValueError) as err:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Invalid JSON payload syntax: {err}"],
                    schema_type=detected_type,
                    target_entity=target_entity,
                )

        if detected_type == SchemaType.JSON_SCHEMA:
            return cls._validate_json_schema(schema_content, payload)

        elif detected_type == SchemaType.OPENAPI:
            return cls._validate_openapi(schema_content, payload, target_entity)

        elif detected_type == SchemaType.PROTOBUF:
            return cls._validate_proto(schema_content, payload, target_entity)

        elif detected_type == SchemaType.AVRO:
            return cls._validate_avro(schema_content, payload, target_entity)

        return ValidationResult(
            is_valid=True,
            errors=[],
            schema_type=detected_type,
            target_entity=target_entity,
        )

    @classmethod
    def _validate_json_schema(cls, schema_content: str, payload: Any) -> ValidationResult:
        ast = JsonSchemaParser.parse_string(schema_content)
        validator = jsonschema.Draft202012Validator(ast.raw)
        errors = [err.message for err in validator.iter_errors(payload)]
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            schema_type=SchemaType.JSON_SCHEMA,
            target_entity=ast.title,
        )

    @classmethod
    def _validate_openapi(
        cls, schema_content: str, payload: Any, target_entity: str | None
    ) -> ValidationResult:
        ast = OpenApiParser.parse_string(schema_content)
        schemas = ast.schemas
        target = target_entity or next(iter(schemas.keys()), None)

        if not target or target not in schemas:
            return ValidationResult(
                is_valid=False,
                errors=[f"Target component schema '{target}' not found in OpenAPI definition"],
                schema_type=SchemaType.OPENAPI,
                target_entity=target,
            )

        sub_schema = schemas[target]
        validator = jsonschema.Draft202012Validator(sub_schema)
        errors = [err.message for err in validator.iter_errors(payload)]
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            schema_type=SchemaType.OPENAPI,
            target_entity=target,
        )

    @classmethod
    def _validate_proto(
        cls, schema_content: str, payload: Any, target_entity: str | None
    ) -> ValidationResult:
        ast: ProtoAST = ProtoParser.parse_string(schema_content)
        if not ast.messages:
            return ValidationResult(
                is_valid=True,
                errors=[],
                schema_type=SchemaType.PROTOBUF,
            )

        msg_name = target_entity or next(iter(ast.messages.keys()))
        if msg_name not in ast.messages:
            return ValidationResult(
                is_valid=False,
                errors=[f"Target message '{msg_name}' not found in Protobuf definition"],
                schema_type=SchemaType.PROTOBUF,
                target_entity=msg_name,
            )

        msg: ProtoMessageAST = ast.messages[msg_name]
        errors: list[str] = []

        if not isinstance(payload, dict):
            return ValidationResult(
                is_valid=False,
                errors=[
                    f"Protobuf message payload must be an object/dict, got {type(payload).__name__}"
                ],
                schema_type=SchemaType.PROTOBUF,
                target_entity=msg_name,
            )

        for field_name, val in payload.items():
            if field_name not in msg.fields:
                # Disallow unknown fields unless reserved
                if field_name not in msg.reserved_names:
                    errors.append(f"Field '{field_name}' is not defined in message '{msg_name}'")
                continue

            field = msg.fields[field_name]
            f_type = field.type

            # Type checking
            if f_type in ("string",):
                if not isinstance(val, str):
                    errors.append(f"Field '{field_name}' expects string, got {type(val).__name__}")
            elif f_type in (
                "int32",
                "int64",
                "uint32",
                "uint64",
                "sint32",
                "sint64",
                "fixed32",
                "fixed64",
            ):
                if not isinstance(val, int) or isinstance(val, bool):
                    errors.append(f"Field '{field_name}' expects integer, got {type(val).__name__}")
            elif f_type in ("float", "double"):
                if not isinstance(val, (float, int)) or isinstance(val, bool):
                    errors.append(
                        f"Field '{field_name}' expects numeric float/double, got {type(val).__name__}"
                    )
            elif f_type in ("bool",) and not isinstance(val, bool):
                errors.append(f"Field '{field_name}' expects boolean, got {type(val).__name__}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            schema_type=SchemaType.PROTOBUF,
            target_entity=msg_name,
        )

    @classmethod
    def _validate_avro(
        cls, schema_content: str, payload: Any, target_entity: str | None
    ) -> ValidationResult:
        ast: AvroRecordAST = AvroParser.parse_string(schema_content)
        errors: list[str] = []

        if not isinstance(payload, dict):
            return ValidationResult(
                is_valid=False,
                errors=[f"Avro record payload must be a dict, got {type(payload).__name__}"],
                schema_type=SchemaType.AVRO,
                target_entity=ast.name,
            )

        for f_name, field in ast.fields.items():
            if f_name not in payload:
                if not field.has_default and field.type != "null":
                    errors.append(f"Missing required Avro field '{f_name}' with no default value")
                continue

            val = payload[f_name]
            f_type = field.type

            if f_type == "string" and not isinstance(val, str):
                errors.append(f"Field '{f_name}' expects string, got {type(val).__name__}")
            elif f_type in ("int", "long") and (not isinstance(val, int) or isinstance(val, bool)):
                errors.append(f"Field '{f_name}' expects integer, got {type(val).__name__}")
            elif f_type in ("float", "double") and (
                not isinstance(val, (float, int)) or isinstance(val, bool)
            ):
                errors.append(f"Field '{f_name}' expects float/double, got {type(val).__name__}")
            elif f_type == "boolean" and not isinstance(val, bool):
                errors.append(f"Field '{f_name}' expects boolean, got {type(val).__name__}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            schema_type=SchemaType.AVRO,
            target_entity=ast.name,
        )
