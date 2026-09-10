"""OpenAPI 3.x AST Parser.

Parses OpenAPI 3.0 and 3.1 specifications (in YAML or JSON) into structured AST objects.
"""

import json
from typing import Any

import yaml

from contracthub.core.models import (
    OpenApiAST,
    OpenApiOperationAST,
    OpenApiParameterAST,
    OpenApiPathAST,
    OpenApiResponseAST,
)


class OpenApiParser:
    """Extracts structural AST from OpenAPI 3.x specifications."""

    @classmethod
    def parse_string(cls, content: str) -> OpenApiAST:
        # Load JSON or YAML
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, yaml.YAMLError):
            data = yaml.safe_load(content)

        if not isinstance(data, dict):
            raise TypeError("Invalid OpenAPI document: root must be a mapping/object.")

        openapi_version = str(data.get("openapi", "3.0.0"))
        info = data.get("info", {})
        title = info.get("title", "Untitled API")

        ast = OpenApiAST(version=openapi_version, title=title)
        ast.schemas = data.get("components", {}).get("schemas", {})

        paths_dict = data.get("paths", {})
        for path_url, path_item in paths_dict.items():
            if not isinstance(path_item, dict):
                continue
            path_ast = OpenApiPathAST(path=path_url)

            # Standard HTTP methods
            for method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                if method in path_item and isinstance(path_item[method], dict):
                    op_data = path_item[method]
                    op_ast = cls._parse_operation(method.upper(), op_data)
                    path_ast.operations[method.upper()] = op_ast

            ast.paths[path_url] = path_ast

        return ast

    @classmethod
    def parse_file(cls, path: str) -> OpenApiAST:
        with open(path, "r", encoding="utf-8") as f:
            return cls.parse_string(f.read())

    @classmethod
    def _parse_operation(cls, method: str, data: dict[str, Any]) -> OpenApiOperationAST:
        op = OpenApiOperationAST(method=method, operation_id=data.get("operationId"))

        # Parse parameters
        params = data.get("parameters", [])
        if isinstance(params, list):
            for p in params:
                if isinstance(p, dict) and "name" in p:
                    p_name = p["name"]
                    p_in = p.get("in", "query")
                    p_req = bool(p.get("required", False))
                    p_type = p.get("schema", {}).get("type")
                    op.parameters[f"{p_in}:{p_name}"] = OpenApiParameterAST(
                        name=p_name, location=p_in, required=p_req, type=p_type
                    )

        # Parse requestBody
        req_body = data.get("requestBody")
        if isinstance(req_body, dict):
            op.request_body_required = bool(req_body.get("required", False))
            content = req_body.get("content", {})
            if isinstance(content, dict):
                op.request_body_types = content

        # Parse responses
        responses = data.get("responses", {})
        if isinstance(responses, dict):
            for status, resp_data in responses.items():
                if isinstance(resp_data, dict):
                    content = resp_data.get("content", {})
                    desc = resp_data.get("description")
                    op.responses[str(status)] = OpenApiResponseAST(
                        status_code=str(status),
                        description=desc,
                        content_types=content if isinstance(content, dict) else {},
                    )

        return op
