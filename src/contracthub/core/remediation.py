"""Auto-Remediation Engine for Breaking Schema Mutations.

Automatically repairs Proto3 breaking changes such as unreserved deleted fields
and enum values by injecting standard reserved statements.
"""

import re

from pydantic import BaseModel, Field

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, SchemaType, Severity
from contracthub.core.rules import PROTO_ENUM_VALUE_REMOVED, PROTO_FIELD_REMOVED


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
    def fix_proto(cls, base_content: str, candidate_content: str) -> RemediationResult:
        # Run comparator first to identify violations
        cmp_result = SchemaComparator.compare_strings(
            base_content=base_content,
            candidate_content=candidate_content,
            schema_type=SchemaType.PROTOBUF,
            mode=CompatibilityMode.FULL,
        )

        actions: list[RemediationAction] = []
        fixed = candidate_content

        # 1. Handle PROTO_FIELD_REMOVED
        # Violation path is: MsgName.fieldName, message has tag
        field_removals: list[tuple[str, str, int]] = []
        for v in cmp_result.violations:
            if v.code == PROTO_FIELD_REMOVED and v.severity == Severity.BREAKING and "." in v.path:
                msg_name, field_name = v.path.split(".", 1)
                # Extract tag from message: "Field 'customer_id' (tag 2) was deleted..."
                tag_match = re.search(r"\(tag\s+(\d+)\)", v.message)
                if tag_match:
                    tag = int(tag_match.group(1))
                    field_removals.append((msg_name, field_name, tag))

        for msg_name, f_name, tag in field_removals:
            # Locate message block in candidate content
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
        # Path: EnumName.VAL_NAME, message has: "Enum value 'VAL_NAME' (3) was removed..."
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

        was_modified = len(actions) > 0
        return RemediationResult(
            was_modified=was_modified,
            actions=actions,
            fixed_content=fixed,
        )
