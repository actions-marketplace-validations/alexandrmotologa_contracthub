"""Core compatibility models, rules, and comparator engine."""

from contracthub.core.codegen import CodeGenerator, TargetLanguage
from contracthub.core.models import (
    CompatibilityMode,
    CompatibilityResult,
    SchemaType,
    Severity,
    Violation,
)

__all__ = [
    "CodeGenerator",
    "CompatibilityMode",
    "CompatibilityResult",
    "SchemaType",
    "Severity",
    "TargetLanguage",
    "Violation",
]
