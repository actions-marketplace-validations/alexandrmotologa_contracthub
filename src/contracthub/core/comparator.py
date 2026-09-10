"""Core Compatibility Comparator Engine.

Evaluates schema candidate updates against base schemas across Proto3, OpenAPI, and JSON Schema
definitions according to BACKWARD, FORWARD, and FULL compatibility modes.
"""

from contracthub.core.models import (
    CompatibilityMode,
    CompatibilityResult,
    JsonSchemaAST,
    OpenApiAST,
    ProtoAST,
    SchemaType,
    Severity,
    Violation,
)
from contracthub.core.rules import (
    AVRO_FIELD_ADDED_NO_DEFAULT,
    AVRO_FIELD_REMOVED_NO_DEFAULT,
    AVRO_TYPE_MUTATED,
    JSON_SCHEMA_PROPERTY_REMOVED,
    JSON_SCHEMA_REQUIRED_ADDED,
    JSON_SCHEMA_TYPE_NARROWED,
    PROTO_CARDINALITY_CHANGED,
    PROTO_ENUM_NUM_MUTATED,
    PROTO_ENUM_VALUE_REMOVED,
    PROTO_FIELD_REMOVED,
    PROTO_MESSAGE_REMOVED,
    PROTO_TAG_COLLISION,
    PROTO_TAG_MUTATED,
    PROTO_TYPE_CHANGED,
    REST_ENDPOINT_REMOVED,
    REST_METHOD_REMOVED,
    REST_PARAM_TYPE_MUTATED,
    REST_REQUIRED_BODY_ADDED,
    REST_REQUIRED_PARAM_ADDED,
    REST_STATUS_MUTATED,
)
from contracthub.parsers.avro_parser import AvroParser, AvroRecordAST
from contracthub.parsers.json_schema_parser import JsonSchemaParser
from contracthub.parsers.openapi_parser import OpenApiParser
from contracthub.parsers.proto_parser import ProtoParser


class SchemaComparator:
    """Compares base and candidate schemas to identify breaking changes."""

    @classmethod
    def compare_strings(
        cls,
        base_content: str,
        candidate_content: str,
        schema_type: SchemaType,
        mode: CompatibilityMode = CompatibilityMode.FULL,
    ) -> CompatibilityResult:
        if mode == CompatibilityMode.NONE:
            return CompatibilityResult(is_compatible=True, mode=mode, violations=[])

        if schema_type == SchemaType.PROTOBUF:
            base_ast = ProtoParser.parse_string(base_content)
            candidate_ast = ProtoParser.parse_string(candidate_content)
            return cls.compare_proto(base_ast, candidate_ast, mode)

        elif schema_type == SchemaType.OPENAPI:
            base_ast = OpenApiParser.parse_string(base_content)
            candidate_ast = OpenApiParser.parse_string(candidate_content)
            return cls.compare_openapi(base_ast, candidate_ast, mode)

        elif schema_type == SchemaType.JSON_SCHEMA:
            base_ast = JsonSchemaParser.parse_string(base_content)
            candidate_ast = JsonSchemaParser.parse_string(candidate_content)
            return cls.compare_json_schema(base_ast, candidate_ast, mode)

        elif schema_type == SchemaType.AVRO:
            base_ast = AvroParser.parse_string(base_content)
            candidate_ast = AvroParser.parse_string(candidate_content)
            return cls.compare_avro(base_ast, candidate_ast, mode)

        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

    @classmethod
    def detect_schema_type(cls, content: str, filename: str | None = None) -> SchemaType:
        if filename:
            if filename.endswith(".proto"):
                return SchemaType.PROTOBUF
            if filename.endswith(".avsc"):
                return SchemaType.AVRO
            if "openapi" in filename.lower() or "swagger" in filename.lower():
                return SchemaType.OPENAPI

        trimmed = content.strip()
        if trimmed.startswith("syntax =") or 'syntax="' in trimmed or "syntax = " in trimmed:
            return SchemaType.PROTOBUF
        if (
            '"type": "record"' in trimmed
            or '"type":"record"' in trimmed
            or "'type': 'record'" in trimmed
        ):
            return SchemaType.AVRO
        if '"openapi":' in trimmed or "'openapi':" in trimmed or "openapi:" in trimmed:
            return SchemaType.OPENAPI
        if "$schema" in trimmed or '"properties":' in trimmed or "'properties':" in trimmed:
            return SchemaType.JSON_SCHEMA

        # Default fallback to JSON Schema if it starts with { or [
        if trimmed.startswith(("{", "[")):
            return SchemaType.JSON_SCHEMA

        return SchemaType.PROTOBUF

    @classmethod
    def compare_proto(
        cls,
        base: ProtoAST,
        cand: ProtoAST,
        mode: CompatibilityMode = CompatibilityMode.FULL,
    ) -> CompatibilityResult:
        violations: list[Violation] = []
        checks = 0

        # 1. Check messages
        for msg_name, base_msg in base.messages.items():
            checks += 1
            if msg_name not in cand.messages:
                violations.append(
                    Violation(
                        code=PROTO_MESSAGE_REMOVED,
                        severity=Severity.BREAKING,
                        path=msg_name,
                        message=f"Message '{msg_name}' was removed in candidate schema.",
                        suggestion=f"Retain message '{msg_name}' to maintain compatibility.",
                    )
                )
                continue

            cand_msg = cand.messages[msg_name]

            # Check fields
            for f_name, base_field in base_msg.fields.items():
                checks += 1
                if f_name in cand_msg.fields:
                    cand_field = cand_msg.fields[f_name]

                    # Tag mutation
                    if base_field.tag != cand_field.tag:
                        violations.append(
                            Violation(
                                code=PROTO_TAG_MUTATED,
                                severity=Severity.BREAKING,
                                path=f"{msg_name}.{f_name}",
                                message=(
                                    f"Field '{f_name}' numeric tag changed from "
                                    f"{base_field.tag} to {cand_field.tag}."
                                ),
                                suggestion=(
                                    f"Restore original tag {base_field.tag} for field '{f_name}'."
                                ),
                            )
                        )

                    # Type mutation
                    if base_field.type != cand_field.type:
                        violations.append(
                            Violation(
                                code=PROTO_TYPE_CHANGED,
                                severity=Severity.BREAKING,
                                path=f"{msg_name}.{f_name}",
                                message=(
                                    f"Field '{f_name}' type changed from "
                                    f"'{base_field.type}' to '{cand_field.type}'."
                                ),
                                suggestion=(
                                    f"Keep original type '{base_field.type}' or deprecate this field."
                                ),
                            )
                        )

                    # Cardinality mutation (e.g. repeated to singular or vice-versa)
                    if base_field.cardinality != cand_field.cardinality:
                        violations.append(
                            Violation(
                                code=PROTO_CARDINALITY_CHANGED,
                                severity=Severity.BREAKING,
                                path=f"{msg_name}.{f_name}",
                                message=(
                                    f"Field '{f_name}' cardinality changed from "
                                    f"'{base_field.cardinality}' to '{cand_field.cardinality}'."
                                ),
                            )
                        )
                else:
                    # Field missing by name: check if tag was reused or reserved
                    checks += 1
                    if base_field.tag in cand_msg.fields_by_tag:
                        reused_field = cand_msg.fields_by_tag[base_field.tag]
                        violations.append(
                            Violation(
                                code=PROTO_TAG_COLLISION,
                                severity=Severity.BREAKING,
                                path=f"{msg_name}.{f_name}",
                                message=(
                                    f"Field '{f_name}' (tag {base_field.tag}) was replaced by "
                                    f"'{reused_field.name}' with the same tag number."
                                ),
                                suggestion=(
                                    f"Assign '{reused_field.name}' a unique unused tag number."
                                ),
                            )
                        )
                    else:
                        # Field deleted: check if tag is marked as reserved
                        is_reserved = (
                            base_field.tag in cand_msg.reserved_tags
                            or f_name in cand_msg.reserved_names
                        )
                        if not is_reserved:
                            violations.append(
                                Violation(
                                    code=PROTO_FIELD_REMOVED,
                                    severity=Severity.BREAKING,
                                    path=f"{msg_name}.{f_name}",
                                    message=(
                                        f"Field '{f_name}' (tag {base_field.tag}) was deleted without "
                                        f"marking its tag as reserved."
                                    ),
                                    suggestion=(
                                        f"Add 'reserved {base_field.tag};' and "
                                        f"'reserved \"{f_name}\";' in message '{msg_name}'."
                                    ),
                                )
                            )

            # Check if candidate added fields using reserved tags
            for c_name, cand_field in cand_msg.fields.items():
                if c_name not in base_msg.fields and cand_field.tag in base_msg.reserved_tags:
                    violations.append(
                        Violation(
                            code=PROTO_TAG_COLLISION,
                            severity=Severity.BREAKING,
                            path=f"{msg_name}.{c_name}",
                            message=(
                                f"New field '{c_name}' uses tag {cand_field.tag}, "
                                f"which was reserved in the base schema."
                            ),
                        )
                    )

        # 2. Check enums
        for enum_name, base_enum in base.enums.items():
            checks += 1
            if enum_name not in cand.enums:
                violations.append(
                    Violation(
                        code=PROTO_ENUM_VALUE_REMOVED,
                        severity=Severity.BREAKING,
                        path=enum_name,
                        message=f"Enum '{enum_name}' was removed in candidate schema.",
                    )
                )
                continue

            cand_enum = cand.enums[enum_name]
            for v_name, v_num in base_enum.values.items():
                checks += 1
                if v_name not in cand_enum.values:
                    # Enum value removed: check if number is reserved
                    if v_num not in cand_enum.reserved_numbers:
                        violations.append(
                            Violation(
                                code=PROTO_ENUM_VALUE_REMOVED,
                                severity=Severity.BREAKING,
                                path=f"{enum_name}.{v_name}",
                                message=(
                                    f"Enum value '{v_name}' ({v_num}) was removed without reservation."
                                ),
                                suggestion=f"Add 'reserved {v_num};' to enum '{enum_name}'.",
                            )
                        )
                else:
                    cand_v_num = cand_enum.values[v_name]
                    if v_num != cand_v_num:
                        violations.append(
                            Violation(
                                code=PROTO_ENUM_NUM_MUTATED,
                                severity=Severity.BREAKING,
                                path=f"{enum_name}.{v_name}",
                                message=(
                                    f"Enum value '{v_name}' numeric value changed from "
                                    f"{v_num} to {cand_v_num}."
                                ),
                            )
                        )

        is_compatible = len([v for v in violations if v.severity == Severity.BREAKING]) == 0
        return CompatibilityResult(
            is_compatible=is_compatible,
            mode=mode,
            violations=violations,
            total_checks=checks,
        )

    @classmethod
    def compare_openapi(
        cls,
        base: OpenApiAST,
        cand: OpenApiAST,
        mode: CompatibilityMode = CompatibilityMode.FULL,
    ) -> CompatibilityResult:
        violations: list[Violation] = []
        checks = 0

        for path_url, base_path in base.paths.items():
            checks += 1
            if path_url not in cand.paths:
                violations.append(
                    Violation(
                        code=REST_ENDPOINT_REMOVED,
                        severity=Severity.BREAKING,
                        path=path_url,
                        message=f"Path '{path_url}' was removed in candidate specification.",
                        suggestion=f"Retain path '{path_url}' or deprecate it before removal.",
                    )
                )
                continue

            cand_path = cand.paths[path_url]
            for method, base_op in base_path.operations.items():
                checks += 1
                if method not in cand_path.operations:
                    violations.append(
                        Violation(
                            code=REST_METHOD_REMOVED,
                            severity=Severity.BREAKING,
                            path=f"{method} {path_url}",
                            message=f"Method '{method}' was removed from '{path_url}'.",
                        )
                    )
                    continue

                cand_op = cand_path.operations[method]

                # Check if candidate added new required parameters
                for p_key, cand_param in cand_op.parameters.items():
                    checks += 1
                    if cand_param.required:
                        base_param = base_op.parameters.get(p_key)
                        if not base_param or not base_param.required:
                            violations.append(
                                Violation(
                                    code=REST_REQUIRED_PARAM_ADDED,
                                    severity=Severity.BREAKING,
                                    path=f"{method} {path_url} [{cand_param.name}]",
                                    message=(
                                        f"New required parameter '{cand_param.name}' was added "
                                        f"to {method} {path_url}."
                                    ),
                                    suggestion="Make the parameter optional with a default value.",
                                )
                            )

                # Check parameter type mutations
                for p_key, base_param in base_op.parameters.items():
                    if p_key in cand_op.parameters:
                        cand_param = cand_op.parameters[p_key]
                        if (
                            base_param.type
                            and cand_param.type
                            and base_param.type != cand_param.type
                        ):
                            violations.append(
                                Violation(
                                    code=REST_PARAM_TYPE_MUTATED,
                                    severity=Severity.BREAKING,
                                    path=f"{method} {path_url} [{base_param.name}]",
                                    message=(
                                        f"Parameter '{base_param.name}' type changed from "
                                        f"'{base_param.type}' to '{cand_param.type}'."
                                    ),
                                )
                            )

                # Check request body required mutation
                if not base_op.request_body_required and cand_op.request_body_required:
                    violations.append(
                        Violation(
                            code=REST_REQUIRED_BODY_ADDED,
                            severity=Severity.BREAKING,
                            path=f"{method} {path_url} [requestBody]",
                            message=f"Request body for {method} {path_url} is now required.",
                        )
                    )

                # Check responses: did an existing status code disappear?
                for status_code in base_op.responses:
                    checks += 1
                    if status_code not in cand_op.responses:
                        violations.append(
                            Violation(
                                code=REST_STATUS_MUTATED,
                                severity=Severity.BREAKING,
                                path=f"{method} {path_url} -> {status_code}",
                                message=(
                                    f"Declared response status '{status_code}' was removed "
                                    f"from {method} {path_url}."
                                ),
                            )
                        )

        is_compatible = len([v for v in violations if v.severity == Severity.BREAKING]) == 0
        return CompatibilityResult(
            is_compatible=is_compatible,
            mode=mode,
            violations=violations,
            total_checks=checks,
        )

    @classmethod
    def compare_json_schema(
        cls,
        base: JsonSchemaAST,
        cand: JsonSchemaAST,
        mode: CompatibilityMode = CompatibilityMode.FULL,
    ) -> CompatibilityResult:
        violations: list[Violation] = []
        checks = 0

        # Check required fields additions
        base_req = set(base.required)
        cand_req = set(cand.required)
        newly_required = cand_req - base_req

        if newly_required and mode in (CompatibilityMode.BACKWARD, CompatibilityMode.FULL):
            checks += 1
            for field in newly_required:
                violations.append(
                    Violation(
                        code=JSON_SCHEMA_REQUIRED_ADDED,
                        severity=Severity.BREAKING,
                        path=f"properties.{field}",
                        message=f"Field '{field}' was added to the required array.",
                        suggestion="Keep the field optional or provide a default value.",
                    )
                )

        # Check property types
        for prop_name, base_prop in base.properties.items():
            checks += 1
            if prop_name in cand.properties:
                cand_prop = cand.properties[prop_name]
                base_type = base_prop.get("type") if isinstance(base_prop, dict) else None
                cand_type = cand_prop.get("type") if isinstance(cand_prop, dict) else None
                if base_type and cand_type and base_type != cand_type:
                    violations.append(
                        Violation(
                            code=JSON_SCHEMA_TYPE_NARROWED,
                            severity=Severity.BREAKING,
                            path=f"properties.{prop_name}",
                            message=(
                                f"Property '{prop_name}' type changed from "
                                f"'{base_type}' to '{cand_type}'."
                            ),
                        )
                    )
            else:
                # Property removed: check if additionalProperties is false
                if cand.additional_properties is False:
                    violations.append(
                        Violation(
                            code=JSON_SCHEMA_PROPERTY_REMOVED,
                            severity=Severity.BREAKING,
                            path=f"properties.{prop_name}",
                            message=(
                                f"Property '{prop_name}' was removed and candidate schema "
                                f"disallows additional properties."
                            ),
                        )
                    )

        is_compatible = len([v for v in violations if v.severity == Severity.BREAKING]) == 0
        return CompatibilityResult(
            is_compatible=is_compatible,
            mode=mode,
            violations=violations,
            total_checks=checks,
        )

    @classmethod
    def compare_avro(
        cls,
        base: AvroRecordAST,
        cand: AvroRecordAST,
        mode: CompatibilityMode = CompatibilityMode.FULL,
    ) -> CompatibilityResult:
        violations: list[Violation] = []
        checks = 0

        # Check fields in base
        for f_name, base_field in base.fields.items():
            checks += 1
            if f_name not in cand.fields:
                if (
                    mode in (CompatibilityMode.FORWARD, CompatibilityMode.FULL)
                    and not base_field.has_default
                ):
                    violations.append(
                        Violation(
                            code=AVRO_FIELD_REMOVED_NO_DEFAULT,
                            severity=Severity.BREAKING,
                            path=f"{base.name}.{f_name}",
                            message=f"Field '{f_name}' removed from record '{base.name}' without a default value in base schema.",
                            suggestion=f"Provide a default value for '{f_name}' before removal.",
                        )
                    )
            else:
                cand_field = cand.fields[f_name]
                if base_field.type != cand_field.type:
                    violations.append(
                        Violation(
                            code=AVRO_TYPE_MUTATED,
                            severity=Severity.BREAKING,
                            path=f"{base.name}.{f_name}",
                            message=f"Field '{f_name}' type changed from '{base_field.type}' to '{cand_field.type}'.",
                        )
                    )

        # Check fields in candidate
        for c_name, cand_field in cand.fields.items():
            if c_name not in base.fields:
                checks += 1
                if (
                    mode in (CompatibilityMode.BACKWARD, CompatibilityMode.FULL)
                    and not cand_field.has_default
                ):
                    violations.append(
                        Violation(
                            code=AVRO_FIELD_ADDED_NO_DEFAULT,
                            severity=Severity.BREAKING,
                            path=f"{cand.name}.{c_name}",
                            message=f"New field '{c_name}' added to record '{cand.name}' without a default value.",
                            suggestion=f"Specify a 'default' attribute for '{c_name}'.",
                        )
                    )

        is_compatible = len([v for v in violations if v.severity == Severity.BREAKING]) == 0
        return CompatibilityResult(
            is_compatible=is_compatible,
            mode=mode,
            violations=violations,
            total_checks=checks,
        )
