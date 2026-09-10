"""Auto-Remediation Engine for Breaking Schema Mutations.

Automatically repairs breaking changes across Proto3, Apache Avro, OpenAPI,
and GraphQL contracts to preserve backward compatibility.
"""

from __future__ import annotations

import json
import re
from typing import Any

import yaml
from pydantic import BaseModel, Field

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, SchemaType, Severity
from contracthub.core.rules import (
    AVRO_FIELD_ADDED_NO_DEFAULT,
    GRAPHQL_FIELD_REMOVED,
    GRAPHQL_INPUT_FIELD_REQUIRED_ADDED,
    PROTO_ENUM_VALUE_REMOVED,
    PROTO_FIELD_REMOVED,
    REST_ENDPOINT_REMOVED,
    REST_METHOD_REMOVED,
)
from contracthub.parsers.avro_parser import AvroParser
from contracthub.parsers.graphql_parser import GraphQLParser
from contracthub.parsers.openapi_parser import OpenApiParser


class RemediationAction(BaseModel):
    rule_code: str
    target: str
    description: str
    patch_snippet: str


class RemediationResult(BaseModel):
    was_modified: bool
    actions: list[RemediationAction] = Field(default_factory=list)
    fixed_content: str


class AutoRemediator:
    """Analyzes compatibility violations and synthesizes auto-fixes."""

    @classmethod
    def fix(
        cls,
        base_content: str,
        candidate_content: str,
        schema_type: SchemaType | None = None,
    ) -> RemediationResult:
        detected_type = schema_type or SchemaComparator.detect_schema_type(candidate_content)

        if detected_type == SchemaType.PROTOBUF:
            return cls.fix_proto(base_content, candidate_content)
        elif detected_type == SchemaType.AVRO:
            return cls.fix_avro(base_content, candidate_content)
        elif detected_type == SchemaType.OPENAPI:
            return cls.fix_openapi(base_content, candidate_content)
        elif detected_type == SchemaType.GRAPHQL:
            return cls.fix_graphql(base_content, candidate_content)

        return RemediationResult(
            was_modified=False,
            actions=[],
            fixed_content=candidate_content,
        )

    # -------------------------------------------------------------------------
    # PROTO3 AUTO-REMEDIATION
    # -------------------------------------------------------------------------
    @classmethod
    def fix_proto(cls, base_content: str, candidate_content: str) -> RemediationResult:
        cmp_result = SchemaComparator.compare_strings(
            base_content=base_content,
            candidate_content=candidate_content,
            schema_type=SchemaType.PROTOBUF,
            mode=CompatibilityMode.FULL,
        )

        actions: list[RemediationAction] = []
        fixed = candidate_content

        # 1. Handle PROTO_FIELD_REMOVED
        field_removals: list[tuple[str, str, int]] = []
        for v in cmp_result.violations:
            if v.code == PROTO_FIELD_REMOVED and v.severity == Severity.BREAKING and "." in v.path:
                msg_name, field_name = v.path.split(".", 1)
                tag_match = re.search(r"\(tag\s+(\d+)\)", v.message)
                if tag_match:
                    tag = int(tag_match.group(1))
                    field_removals.append((msg_name, field_name, tag))

        for msg_name, f_name, tag in field_removals:
            pattern = re.compile(rf"\bmessage\s+{re.escape(msg_name)}\s*\{{")
            match = pattern.search(fixed)
            if match:
                insert_pos = match.end()
                fix_statement = f'\n  reserved {tag};\n  reserved "{f_name}";'
                fixed = fixed[:insert_pos] + fix_statement + fixed[insert_pos:]
                actions.append(
                    RemediationAction(
                        rule_code=PROTO_FIELD_REMOVED,
                        target=f"{msg_name}.{f_name}",
                        description=f'Injected reserved tag {tag} and name "{f_name}" into message {msg_name}.',
                        patch_snippet=fix_statement.strip(),
                    )
                )

        # 2. Handle PROTO_ENUM_VALUE_REMOVED
        for v in cmp_result.violations:
            if (
                v.code == PROTO_ENUM_VALUE_REMOVED
                and v.severity == Severity.BREAKING
                and "." in v.path
            ):
                enum_name, val_name = v.path.split(".", 1)
                num_match = re.search(r"\((\d+)\)", v.message)
                if num_match:
                    num = int(num_match.group(1))
                    pattern = re.compile(rf"\benum\s+{re.escape(enum_name)}\s*\{{")
                    match = pattern.search(fixed)
                    if match:
                        insert_pos = match.end()
                        fix_statement = f'\n  reserved {num};\n  reserved "{val_name}";'
                        fixed = fixed[:insert_pos] + fix_statement + fixed[insert_pos:]
                        actions.append(
                            RemediationAction(
                                rule_code=PROTO_ENUM_VALUE_REMOVED,
                                target=f"{enum_name}.{val_name}",
                                description=f"Injected reserved number {num} into enum {enum_name}.",
                                patch_snippet=fix_statement.strip(),
                            )
                        )

        return RemediationResult(
            was_modified=len(actions) > 0,
            actions=actions,
            fixed_content=fixed,
        )

    # -------------------------------------------------------------------------
    # APACHE AVRO AUTO-REMEDIATION
    # -------------------------------------------------------------------------
    @classmethod
    def fix_avro(cls, base_content: str, candidate_content: str) -> RemediationResult:
        base_ast = AvroParser.parse_string(base_content)
        cand_ast = AvroParser.parse_string(candidate_content)

        cmp_result = SchemaComparator.compare_avro(
            base_ast, cand_ast, mode=CompatibilityMode.BACKWARD
        )
        actions: list[RemediationAction] = []

        try:
            data: dict[str, Any] = json.loads(candidate_content)
        except json.JSONDecodeError:
            return RemediationResult(was_modified=False, fixed_content=candidate_content)

        fields = data.get("fields", [])
        if not isinstance(fields, list):
            return RemediationResult(was_modified=False, fixed_content=candidate_content)

        for v in cmp_result.violations:
            if v.code == AVRO_FIELD_ADDED_NO_DEFAULT and v.severity == Severity.BREAKING:
                f_name = v.path.split(".")[-1]
                for f in fields:
                    if isinstance(f, dict) and f.get("name") == f_name and "default" not in f:
                        f_type = f.get("type")
                        default_val = cls._infer_avro_default(f_type)
                        f["default"] = default_val

                        actions.append(
                            RemediationAction(
                                rule_code=AVRO_FIELD_ADDED_NO_DEFAULT,
                                target=v.path,
                                description=f"Injected default value '{default_val}' for added field '{f_name}'.",
                                patch_snippet=f'"default": {json.dumps(default_val)}',
                            )
                        )

        if actions:
            fixed_content = json.dumps(data, indent=2) + "\n"
        else:
            fixed_content = candidate_content

        return RemediationResult(
            was_modified=len(actions) > 0,
            actions=actions,
            fixed_content=fixed_content,
        )

    @classmethod
    def _infer_avro_default(cls, avro_type: Any) -> Any:
        if avro_type == "string":
            return ""
        elif avro_type in ("int", "long"):
            return 0
        elif avro_type in ("float", "double"):
            return 0.0
        elif avro_type == "boolean":
            return False
        elif isinstance(avro_type, list) and "null" in avro_type:
            return None
        elif isinstance(avro_type, dict) and avro_type.get("type") == "array":
            return []
        return None

    # -------------------------------------------------------------------------
    # OPENAPI 3.X AUTO-REMEDIATION
    # -------------------------------------------------------------------------
    @classmethod
    def fix_openapi(cls, base_content: str, candidate_content: str) -> RemediationResult:
        base_ast = OpenApiParser.parse_string(base_content)
        cand_ast = OpenApiParser.parse_string(candidate_content)

        cmp_result = SchemaComparator.compare_openapi(
            base_ast, cand_ast, mode=CompatibilityMode.BACKWARD
        )
        actions: list[RemediationAction] = []

        try:
            cand_data = json.loads(candidate_content)
            is_json = True
        except json.JSONDecodeError:
            cand_data = yaml.safe_load(candidate_content)
            is_json = False

        if not isinstance(cand_data, dict):
            return RemediationResult(was_modified=False, fixed_content=candidate_content)

        paths = cand_data.setdefault("paths", {})

        for v in cmp_result.violations:
            if v.code == REST_ENDPOINT_REMOVED:
                # Path was removed e.g. /pets/{petId}
                path_name = v.path
                if path_name not in paths and path_name in base_ast.paths:
                    base_path_obj = base_ast.paths[path_name]
                    # Restore path with deprecated: true on operations
                    restored_ops: dict[str, Any] = {}
                    for op_method in base_path_obj.operations:
                        restored_ops[op_method] = {
                            "summary": f"[Deprecated] Retained endpoint '{path_name}'",
                            "deprecated": True,
                            "responses": {"200": {"description": "Deprecated response"}},
                        }
                    paths[path_name] = restored_ops
                    actions.append(
                        RemediationAction(
                            rule_code=REST_ENDPOINT_REMOVED,
                            target=path_name,
                            description=f"Restored deleted endpoint '{path_name}' with deprecated: true.",
                            patch_snippet=f'"{path_name}": {{ "deprecated": true }}',
                        )
                    )

            elif v.code == REST_METHOD_REMOVED:
                # e.g. "delete /users" or "/users:delete"
                parts = v.path.split(" ", 1) if " " in v.path else v.path.split(":", 1)
                if len(parts) == 2:
                    if parts[0].startswith("/"):
                        path_name, method = parts[0], parts[1]
                    else:
                        method, path_name = parts[0], parts[1]

                    op_dict = paths.setdefault(path_name, {})
                    op_dict[method.lower()] = {
                        "summary": f"[Deprecated] Retained method '{method.upper()}'",
                        "deprecated": True,
                        "responses": {"200": {"description": "Deprecated response"}},
                    }
                    actions.append(
                        RemediationAction(
                            rule_code=REST_METHOD_REMOVED,
                            target=v.path,
                            description=f"Restored deleted operation '{v.path}' with deprecated: true.",
                            patch_snippet=f'"{method.lower()}": {{ "deprecated": true }}',
                        )
                    )

        if actions:
            fixed_content = (
                json.dumps(cand_data, indent=2) + "\n"
                if is_json
                else yaml.dump(cand_data, sort_keys=False)
            )
        else:
            fixed_content = candidate_content

        return RemediationResult(
            was_modified=len(actions) > 0,
            actions=actions,
            fixed_content=fixed_content,
        )

    # -------------------------------------------------------------------------
    # GRAPHQL AUTO-REMEDIATION
    # -------------------------------------------------------------------------
    @classmethod
    def fix_graphql(cls, base_content: str, candidate_content: str) -> RemediationResult:
        base_ast = GraphQLParser.parse_string(base_content)
        cand_ast = GraphQLParser.parse_string(candidate_content)

        cmp_result = SchemaComparator.compare_graphql(
            base_ast, cand_ast, mode=CompatibilityMode.BACKWARD
        )
        actions: list[RemediationAction] = []
        fixed = candidate_content

        # 1. GRAPHQL_INPUT_FIELD_REQUIRED_ADDED: convert non-null to nullable
        for v in cmp_result.violations:
            if v.code == GRAPHQL_INPUT_FIELD_REQUIRED_ADDED:
                input_name, field_name = v.path.split(".", 1)
                # Find input block and replace "fieldName: Type!" with "fieldName: Type"
                input_pat = re.compile(rf"\binput\s+{re.escape(input_name)}\s*\{{([^}}]*)\}}")
                match = input_pat.search(fixed)
                if match:
                    body = match.group(1)
                    # Replace "fieldName: ...!" with "fieldName: ..."
                    field_sub_pat = re.compile(rf"({re.escape(field_name)}\s*:\s*[a-zA-Z0-9_]+)!")
                    if field_sub_pat.search(body):
                        new_body = field_sub_pat.sub(r"\1", body)
                        fixed = fixed[: match.start(1)] + new_body + fixed[match.end(1) :]
                        actions.append(
                            RemediationAction(
                                rule_code=GRAPHQL_INPUT_FIELD_REQUIRED_ADDED,
                                target=v.path,
                                description=f"Converted new input field '{field_name}' in '{input_name}' from required to optional.",
                                patch_snippet=f"{field_name}: (optional)",
                            )
                        )

        # 2. GRAPHQL_FIELD_REMOVED: restore field with @deprecated
        for v in cmp_result.violations:
            if v.code == GRAPHQL_FIELD_REMOVED:
                type_name, field_name = v.path.split(".", 1)
                if type_name in base_ast.types and field_name in base_ast.types[type_name].fields:
                    base_f = base_ast.types[type_name].fields[field_name]
                    type_pat = re.compile(rf"\btype\s+{re.escape(type_name)}\s*\{{")
                    match = type_pat.search(fixed)
                    if match:
                        insert_pos = match.end()
                        restored_snippet = f'\n  {field_name}: {base_f.raw_type} @deprecated(reason: "Scheduled for removal")'
                        fixed = fixed[:insert_pos] + restored_snippet + fixed[insert_pos:]
                        actions.append(
                            RemediationAction(
                                rule_code=GRAPHQL_FIELD_REMOVED,
                                target=v.path,
                                description=f"Restored removed field '{field_name}' with @deprecated directive in '{type_name}'.",
                                patch_snippet=restored_snippet.strip(),
                            )
                        )

        return RemediationResult(
            was_modified=len(actions) > 0,
            actions=actions,
            fixed_content=fixed,
        )
