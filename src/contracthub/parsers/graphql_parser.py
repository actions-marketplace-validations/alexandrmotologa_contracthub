"""GraphQL Schema Definition Language (SDL) AST Parser.

Parses GraphQL SDL documents into structured AST objects for compatibility analysis,
mock generation, and client code generation.
"""

from __future__ import annotations

import re
from pathlib import Path

from contracthub.core.models import (
    GraphQLAST,
    GraphQLEnumAST,
    GraphQLFieldAST,
    GraphQLTypeAST,
)


class GraphQLParser:
    """Extracts structural AST from GraphQL Schema Definition Language (SDL)."""

    @classmethod
    def parse_string(cls, content: str) -> GraphQLAST:
        ast = GraphQLAST()
        cleaned = cls._strip_comments(content)

        # 1. Parse Scalars: scalar DateTime
        for scalar_match in re.finditer(r"\bscalar\s+([A-Za-z0-9_]+)", cleaned):
            scalar_name = scalar_match.group(1).strip()
            if scalar_name not in ast.scalars:
                ast.scalars.append(scalar_name)

        # 2. Parse Unions: union SearchResult = User | Product | Order
        for union_match in re.finditer(r"\bunion\s+([A-Za-z0-9_]+)\s*=\s*([^#\n{}]+)", cleaned):
            union_name = union_match.group(1).strip()
            members_raw = union_match.group(2).strip()
            members = [m.strip() for m in members_raw.split("|") if m.strip()]
            ast.unions[union_name] = GraphQLTypeAST(
                name=union_name,
                kind="union",
                union_members=members,
            )

        # 3. Parse Enums: enum Role { ADMIN USER GUEST }
        for enum_match in re.finditer(r"\benum\s+([A-Za-z0-9_]+)\s*\{([^}]*)\}", cleaned):
            enum_name = enum_match.group(1).strip()
            enum_body = enum_match.group(2)
            values = cls._parse_enum_values(enum_body)
            ast.enums[enum_name] = GraphQLEnumAST(
                name=enum_name,
                values=values,
            )

        # 4. Parse Types, Inputs, and Interfaces
        type_pattern = re.compile(
            r"\b(type|input|interface)\s+([A-Za-z0-9_]+)(?:\s+implements\s+([A-Za-z0-9_,\s&]+))?\s*\{([^}]*)\}"
        )
        for match in type_pattern.finditer(cleaned):
            kind = match.group(1).strip()
            name = match.group(2).strip()
            implements_raw = match.group(3)
            body = match.group(4)

            interfaces = []
            if implements_raw:
                # Can be separated by & or comma or whitespace
                interfaces = [i.strip() for i in re.split(r"[&,]", implements_raw) if i.strip()]

            fields = cls._parse_fields(body)
            type_ast = GraphQLTypeAST(
                name=name,
                kind=kind,
                fields=fields,
                interfaces=interfaces,
            )

            if kind == "type":
                ast.types[name] = type_ast
            elif kind == "input":
                ast.inputs[name] = type_ast
            elif kind == "interface":
                ast.interfaces[name] = type_ast

        return ast

    @classmethod
    def parse_file(cls, path: str | Path) -> GraphQLAST:
        content = Path(path).read_text(encoding="utf-8")
        return cls.parse_string(content)

    @classmethod
    def _strip_comments(cls, content: str) -> str:
        # Strip block docstrings """ ... """
        content = re.sub(r'"""[\s\S]*?"""', "", content)
        # Strip single line comments # ...
        lines = []
        for line in content.splitlines():
            # Remove everything after # if not in string
            line_no_comment = re.sub(r"#.*$", "", line)
            lines.append(line_no_comment)
        return "\n".join(lines)

    @classmethod
    def _parse_enum_values(cls, body: str) -> list[str]:
        values = []
        for token in re.split(r"[\s,]+", body.strip()):
            val = token.strip()
            if val and re.match(r"^[A-Za-z0-9_]+$", val):
                values.append(val)
        return values

    @classmethod
    def _parse_fields(cls, body: str) -> dict[str, GraphQLFieldAST]:
        fields: dict[str, GraphQLFieldAST] = {}
        # Matches: fieldName(arg1: Type, ...): ReturnType [@directive ...]
        # Handles newlines and arguments inside parentheses
        field_pattern = re.compile(r"([a-zA-Z0-9_]+)(?:\s*\(([^)]*)\))?\s*:\s*([a-zA-Z0-9_!\[\]]+)")

        for match in field_pattern.finditer(body):
            field_name = match.group(1).strip()
            args_raw = match.group(2)
            raw_type = match.group(3).strip()

            type_name = re.sub(r"[!\[\]]", "", raw_type).strip()
            is_non_null = raw_type.endswith("!")
            is_list = "[" in raw_type

            # Parse optional arguments
            field_args: dict[str, GraphQLFieldAST] = {}
            if args_raw:
                for arg_match in re.finditer(
                    r"([a-zA-Z0-9_]+)\s*:\s*([a-zA-Z0-9_!\[\]]+)(?:\s*=[^,]*)?",
                    args_raw,
                ):
                    arg_name = arg_match.group(1).strip()
                    arg_raw_type = arg_match.group(2).strip()
                    arg_type_name = re.sub(r"[!\[\]]", "", arg_raw_type).strip()
                    field_args[arg_name] = GraphQLFieldAST(
                        name=arg_name,
                        type_name=arg_type_name,
                        is_non_null=arg_raw_type.endswith("!"),
                        is_list="[" in arg_raw_type,
                        raw_type=arg_raw_type,
                    )

            fields[field_name] = GraphQLFieldAST(
                name=field_name,
                type_name=type_name,
                is_non_null=is_non_null,
                is_list=is_list,
                raw_type=raw_type,
                args=field_args,
            )

        return fields
