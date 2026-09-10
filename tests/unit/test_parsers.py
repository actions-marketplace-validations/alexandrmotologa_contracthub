"""Unit tests for AST Parsers."""

from contracthub.parsers.json_schema_parser import JsonSchemaParser
from contracthub.parsers.openapi_parser import OpenApiParser
from contracthub.parsers.proto_parser import ProtoParser


def test_proto_parser_basic():
    proto_content = """
    syntax = "proto3";
    package test.orders;

    enum Status {
        STATUS_UNKNOWN = 0;
        STATUS_ACTIVE = 1;
        reserved 2, 5 to 7;
        reserved "DEPRECATED";
    }

    message Order {
        string id = 1;
        int32 count = 2;
        repeated string tags = 3;
        reserved 4, 10;
        reserved "old_field";
    }
    """
    ast = ProtoParser.parse_string(proto_content)
    assert ast.syntax == "proto3"
    assert ast.package == "test.orders"

    # Enums
    assert "Status" in ast.enums
    status_enum = ast.enums["Status"]
    assert status_enum.values["STATUS_UNKNOWN"] == 0
    assert status_enum.values["STATUS_ACTIVE"] == 1
    assert 2 in status_enum.reserved_numbers
    assert 6 in status_enum.reserved_numbers
    assert "DEPRECATED" in status_enum.reserved_names

    # Messages
    assert "Order" in ast.messages
    order_msg = ast.messages["Order"]
    assert order_msg.fields["id"].tag == 1
    assert order_msg.fields["id"].type == "string"
    assert order_msg.fields["count"].tag == 2
    assert order_msg.fields["tags"].cardinality == "repeated"
    assert 4 in order_msg.reserved_tags
    assert 10 in order_msg.reserved_tags
    assert "old_field" in order_msg.reserved_names


def test_openapi_parser_basic():
    spec = """
    openapi: 3.0.1
    info:
      title: Sample API
      version: 1.0.0
    paths:
      /users:
        get:
          operationId: getUsers
          parameters:
            - name: page
              in: query
              required: false
              schema:
                type: integer
          responses:
            '200':
              description: Successful response
    """
    ast = OpenApiParser.parse_string(spec)
    assert ast.title == "Sample API"
    assert "/users" in ast.paths
    path = ast.paths["/users"]
    assert "GET" in path.operations
    op = path.operations["GET"]
    assert op.operation_id == "getUsers"
    assert "query:page" in op.parameters
    assert op.parameters["query:page"].required is False
    assert "200" in op.responses


def test_json_schema_parser_basic():
    schema = """
    {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "title": "User",
      "type": "object",
      "required": ["id", "username"],
      "properties": {
        "id": { "type": "string" },
        "username": { "type": "string" }
      },
      "additionalProperties": false
    }
    """
    ast = JsonSchemaParser.parse_string(schema)
    assert ast.title == "User"
    assert ast.type == "object"
    assert "id" in ast.required
    assert "username" in ast.required
    assert ast.additional_properties is False
    assert "id" in ast.properties
