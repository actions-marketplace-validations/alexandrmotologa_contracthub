"""Synthetic Mock Data Generator.

Generates schema-compliant JSON payloads for Protobuf Proto3, OpenAPI, JSON Schema,
and Apache Avro contracts to assist client testing.
"""

from typing import Any

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import GraphQLAST, ProtoAST, ProtoMessageAST, SchemaType
from contracthub.parsers.avro_parser import AvroParser, AvroRecordAST
from contracthub.parsers.graphql_parser import GraphQLParser
from contracthub.parsers.json_schema_parser import JsonSchemaParser
from contracthub.parsers.openapi_parser import OpenApiParser
from contracthub.parsers.proto_parser import ProtoParser


class MockGenerator:
    """Produces synthetic JSON payloads conforming to schema definitions."""

    @classmethod
    def generate(
        cls,
        schema_content: str,
        schema_type: SchemaType | None = None,
        target_entity: str | None = None,
    ) -> Any:
        detected_type = schema_type or SchemaComparator.detect_schema_type(schema_content)

        if detected_type == SchemaType.PROTOBUF:
            ast = ProtoParser.parse_string(schema_content)
            return cls._mock_proto(ast, target_message=target_entity)

        elif detected_type == SchemaType.AVRO:
            ast = AvroParser.parse_string(schema_content)
            return cls._mock_avro(ast)

        elif detected_type == SchemaType.JSON_SCHEMA:
            ast = JsonSchemaParser.parse_string(schema_content)
            return cls._mock_json_schema(ast.raw)

        elif detected_type == SchemaType.OPENAPI:
            ast = OpenApiParser.parse_string(schema_content)
            return cls._mock_openapi(ast, target_path=target_entity)

        elif detected_type == SchemaType.GRAPHQL:
            ast_gql = GraphQLParser.parse_string(schema_content)
            return cls._mock_graphql(ast_gql, target_type=target_entity)

        return {}

    @classmethod
    def _mock_proto(cls, ast: ProtoAST, target_message: str | None = None) -> dict[str, Any]:
        if not ast.messages:
            return {}

        msg_name = target_message or next(iter(ast.messages.keys()))
        if msg_name not in ast.messages:
            msg_name = next(iter(ast.messages.keys()))

        msg: ProtoMessageAST = ast.messages[msg_name]
        return cls._mock_proto_message(msg, ast)

    @classmethod
    def _mock_proto_message(
        cls,
        msg: ProtoMessageAST,
        ast: ProtoAST,
        depth: int = 0,
    ) -> dict[str, Any]:
        if depth > 5:
            return {}

        result: dict[str, Any] = {}
        for f_name, f_def in msg.fields.items():
            val = cls._mock_proto_field_val(f_def.type, ast, depth + 1)
            if f_def.cardinality == "repeated":
                result[f_name] = [val, val]
            else:
                result[f_name] = val
        return result

    @classmethod
    def _mock_proto_field_val(cls, f_type: str, ast: ProtoAST, depth: int) -> Any:
        # Scalar primitives
        if f_type in ("string", "bytes"):
            return "example_value"
        elif f_type in ("int32", "int64", "sint32", "sint64", "uint32", "uint64"):
            return 42
        elif f_type in ("double", "float"):
            return 19.99
        elif f_type == "bool":
            return True

        # Check if type is an enum in AST
        if f_type in ast.enums:
            enum_obj = ast.enums[f_type]
            if enum_obj.values:
                return next(iter(enum_obj.values.keys()))
            return 0

        # Check if type is a nested or sibling message in AST
        if f_type in ast.messages:
            return cls._mock_proto_message(ast.messages[f_type], ast, depth + 1)

        return "mock_scalar"

    @classmethod
    def _mock_avro(cls, record: AvroRecordAST) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for f_name, f_field in record.fields.items():
            if f_field.has_default:
                data[f_name] = f_field.default
            else:
                data[f_name] = cls._mock_avro_type(f_field.type)
        return data

    @classmethod
    def _mock_avro_type(cls, t: Any) -> Any:
        if isinstance(t, list):
            # Avro union: e.g. ["null", "string"]
            # Pick first non-null type
            for option in t:
                if option != "null":
                    return cls._mock_avro_type(option)
            return None
        if t == "string":
            return "mock_avro_string"
        elif t in ("int", "long"):
            return 100
        elif t in ("float", "double"):
            return 99.5
        elif t == "boolean":
            return True
        elif isinstance(t, dict) and t.get("type") == "record":
            return {
                f["name"]: cls._mock_avro_type(f.get("type", "string")) for f in t.get("fields", [])
            }
        return "sample_data"

    @classmethod
    def _mock_json_schema(cls, schema: dict[str, Any]) -> Any:
        stype = schema.get("type", "object")
        if stype == "object":
            obj: dict[str, Any] = {}
            props = schema.get("properties", {})
            for p_name, p_def in props.items():
                if isinstance(p_def, dict):
                    obj[p_name] = cls._mock_json_schema(p_def)
                else:
                    obj[p_name] = "value"
            return obj
        elif stype == "string":
            fmt = schema.get("format")
            if fmt == "email":
                return "user@example.com"
            if fmt == "date-time":
                return "2026-09-10T12:00:00Z"
            return "string_sample"
        elif stype == "integer":
            return 1
        elif stype == "number":
            return 3.14
        elif stype == "boolean":
            return True
        elif stype == "array":
            items = schema.get("items", {})
            if isinstance(items, dict):
                return [cls._mock_json_schema(items)]
            return []
        return None

    @classmethod
    def _mock_openapi(cls, ast: OpenApiParser, target_path: str | None = None) -> dict[str, Any]:
        # Return first component schema or first endpoint mock
        if ast.schemas:
            schema_name = next(iter(ast.schemas.keys()))
            return cls._mock_json_schema(ast.schemas[schema_name])
        return {"status": "ok", "message": "Mock response"}

    @classmethod
    def _mock_graphql(cls, ast: GraphQLAST, target_type: str | None = None) -> dict[str, Any]:
        """Generate mock JSON matching GraphQL object type fields."""
        candidate_types = [t for t in ast.types if t not in ("Query", "Mutation", "Subscription")]
        target = target_type or (
            candidate_types[0] if candidate_types else next(iter(ast.types), None)
        )

        if not target or target not in ast.types:
            return {}

        type_ast = ast.types[target]
        result: dict[str, Any] = {}

        for f_name, f in type_ast.fields.items():
            base_t = f.type_name
            if base_t in ("String", "ID"):
                val = f"{f_name}_val" if base_t == "String" else "id_101"
            elif base_t == "Int":
                val = 42
            elif base_t == "Float":
                val = 19.99
            elif base_t == "Boolean":
                val = True
            elif base_t in ast.enums:
                enum_vals = ast.enums[base_t].values
                val = enum_vals[0] if enum_vals else "DEFAULT"
            else:
                val = {}

            if f.is_list:
                result[f_name] = [val]
            else:
                result[f_name] = val

        return result
