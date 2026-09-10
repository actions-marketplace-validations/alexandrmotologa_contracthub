"""Proto3 AST Parser.

Parses Google Protocol Buffers (Proto3) source definitions into structured AST objects
without requiring external binary compilers.
"""

import re

from contracthub.core.models import (
    ProtoAST,
    ProtoEnumAST,
    ProtoFieldAST,
    ProtoMessageAST,
)


class ProtoParser:
    """Extracts structural AST from Proto3 definition strings."""

    @classmethod
    def parse_string(cls, content: str) -> ProtoAST:
        cleaned = cls._strip_comments(content)
        ast = ProtoAST()

        # Parse syntax
        syntax_match = re.search(r'syntax\s*=\s*["\']([^"\']+)["\'];', cleaned)
        if syntax_match:
            ast.syntax = syntax_match.group(1)

        # Parse package
        pkg_match = re.search(r"package\s+([a-zA-Z0-9_.]+);", cleaned)
        if pkg_match:
            ast.package = pkg_match.group(1)

        # Parse imports
        for imp in re.finditer(r'import\s+["\']([^"\']+)["\'];', cleaned):
            ast.imports.append(imp.group(1))

        # Parse top-level blocks
        top_blocks = cls._extract_top_blocks(cleaned)
        for block_type, name, body in top_blocks:
            if block_type == "message":
                ast.messages[name] = cls._parse_message(name, body)
            elif block_type == "enum":
                ast.enums[name] = cls._parse_enum(name, body)

        return ast

    @classmethod
    def parse_file(cls, path: str) -> ProtoAST:
        with open(path, "r", encoding="utf-8") as f:
            return cls.parse_string(f.read())

    @classmethod
    def _strip_comments(cls, content: str) -> str:
        # Remove multi-line comments
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        # Remove single-line comments
        lines = []
        for line in content.splitlines():
            # Check if '//' appears outside quotes
            stripped_line = re.sub(r"//.*$", "", line)
            lines.append(stripped_line)
        return "\n".join(lines)

    @classmethod
    def _extract_top_blocks(cls, content: str) -> list[tuple[str, str, str]]:
        """Extract top-level message and enum declarations with their bodies."""
        blocks = []
        pattern = re.compile(r"\b(message|enum)\s+([a-zA-Z0-9_]+)\s*\{")
        idx = 0
        while idx < len(content):
            match = pattern.search(content, idx)
            if not match:
                break
            block_type = match.group(1)
            name = match.group(2)
            brace_start = match.end() - 1
            brace_end = cls._find_matching_brace(content, brace_start)
            if brace_end == -1:
                break
            body = content[brace_start + 1 : brace_end]
            blocks.append((block_type, name, body))
            idx = brace_end + 1
        return blocks

    @classmethod
    def _find_matching_brace(cls, content: str, start_idx: int) -> int:
        depth = 0
        for i in range(start_idx, len(content)):
            char = content[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return i
        return -1

    @classmethod
    def _parse_message(cls, name: str, body: str) -> ProtoMessageAST:
        msg = ProtoMessageAST(name=name)

        # First, extract any nested message or enum blocks
        nested_spans = []
        pattern = re.compile(r"\b(message|enum)\s+([a-zA-Z0-9_]+)\s*\{")
        idx = 0
        while idx < len(body):
            match = pattern.search(body, idx)
            if not match:
                break
            b_type = match.group(1)
            b_name = match.group(2)
            b_start = match.start()
            brace_start = match.end() - 1
            brace_end = cls._find_matching_brace(body, brace_start)
            if brace_end == -1:
                break
            b_body = body[brace_start + 1 : brace_end]
            if b_type == "message":
                msg.nested_messages[b_name] = cls._parse_message(b_name, b_body)
            elif b_type == "enum":
                msg.nested_enums[b_name] = cls._parse_enum(b_name, b_body)
            nested_spans.append((b_start, brace_end + 1))
            idx = brace_end + 1

        # Replace nested blocks with spaces to parse direct fields cleanly
        cleaned_body_chars = list(body)
        for start, end in nested_spans:
            for i in range(start, end):
                cleaned_body_chars[i] = " "
        direct_body = "".join(cleaned_body_chars)

        # Parse statements separated by ';'
        statements = [s.strip() for s in direct_body.split(";") if s.strip()]

        for stmt in statements:
            # Check reserved statements
            if stmt.startswith("reserved "):
                rest = stmt[len("reserved ") :].strip()
                if rest.startswith(('"', "'")):
                    # Reserved names: reserved "foo", "bar"
                    names = [n.strip(" \"'") for n in rest.split(",") if n.strip()]
                    msg.reserved_names.extend(names)
                else:
                    # Reserved tags: reserved 2, 15, 9 to 11
                    for part in rest.split(","):
                        part = part.strip()
                        if " to " in part:
                            start_s, end_s = part.split(" to ")
                            try:
                                for r in range(int(start_s.strip()), int(end_s.strip()) + 1):
                                    msg.reserved_tags.append(r)
                            except ValueError:
                                pass
                        else:
                            try:
                                msg.reserved_tags.append(int(part))
                            except ValueError:
                                pass
                continue

            # Field declaration pattern
            # [cardinality] <type> <name> = <tag> [options];
            # e.g.: repeated OrderItem items = 4;
            # e.g.: string order_id = 1;
            # e.g.: map<string, int32> attributes = 5;
            field_match = re.match(
                r"^(?:(optional|repeated)\s+)?(map<[^>]+>|[a-zA-Z0-9_.]+)\s+([a-zA-Z0-9_]+)\s*=\s*(\d+)(?:\s*\[.*\])?$",
                stmt,
            )
            if field_match:
                cardinality = field_match.group(1) or "singular"
                field_type = field_match.group(2)
                field_name = field_match.group(3)
                tag = int(field_match.group(4))

                field = ProtoFieldAST(
                    name=field_name, tag=tag, type=field_type, cardinality=cardinality
                )
                msg.fields[field_name] = field
                msg.fields_by_tag[tag] = field

        return msg

    @classmethod
    def _parse_enum(cls, name: str, body: str) -> ProtoEnumAST:
        enum_ast = ProtoEnumAST(name=name)
        statements = [s.strip() for s in body.split(";") if s.strip()]

        for stmt in statements:
            if stmt.startswith("reserved "):
                rest = stmt[len("reserved ") :].strip()
                if rest.startswith(('"', "'")):
                    names = [n.strip(" \"'") for n in rest.split(",") if n.strip()]
                    enum_ast.reserved_names.extend(names)
                else:
                    for part in rest.split(","):
                        part = part.strip()
                        if " to " in part:
                            start_s, end_s = part.split(" to ")
                            try:
                                for r in range(int(start_s.strip()), int(end_s.strip()) + 1):
                                    enum_ast.reserved_numbers.append(r)
                            except ValueError:
                                pass
                        else:
                            try:
                                enum_ast.reserved_numbers.append(int(part.strip()))
                            except ValueError:
                                pass
                continue

            # Enum item: NAME = 0 [options]
            match = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*(-?\d+)", stmt)
            if match:
                val_name = match.group(1)
                val_num = int(match.group(2))
                enum_ast.values[val_name] = val_num

        return enum_ast
