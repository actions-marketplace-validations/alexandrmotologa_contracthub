"""Semantic Versioning (SemVer) recommendation engine for schema evolution."""

import re

from pydantic import BaseModel, Field

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, SchemaType


class SemVerRecommendation(BaseModel):
    """Result of automated SemVer bump evaluation."""

    current_version: str
    recommended_version: str
    bump_type: str  # MAJOR, MINOR, PATCH
    reason: str
    is_breaking: bool
    breaking_changes: list[str] = Field(default_factory=list)
    compatible_changes: list[str] = Field(default_factory=list)


def parse_semver(version_str: str) -> tuple[int, int, int]:
    """Extract (major, minor, patch) integers from a semver string."""
    cleaned = version_str.strip().lstrip("v")
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", cleaned)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return 1, 0, 0


class SemVerEngine:
    """Calculates appropriate semantic version progression based on AST changes."""

    @classmethod
    def recommend_bump(
        cls,
        base_content: str,
        candidate_content: str,
        schema_type: SchemaType,
        current_version: str = "1.0.0",
        mode: CompatibilityMode = CompatibilityMode.FULL,
    ) -> SemVerRecommendation:
        major, minor, patch = parse_semver(current_version)

        # Run compatibility check
        result = SchemaComparator.compare_strings(
            base_content=base_content,
            candidate_content=candidate_content,
            schema_type=schema_type,
            mode=mode,
        )

        breaking_violations = [v.message for v in result.violations if v.severity == "BREAKING"]

        if not result.is_compatible or len(breaking_violations) > 0:
            rec_version = f"{major + 1}.0.0"
            first_code = result.violations[0].code if result.violations else "BREAKING_CHANGE"
            return SemVerRecommendation(
                current_version=current_version,
                recommended_version=rec_version,
                bump_type="MAJOR",
                reason=f"{len(breaking_violations)} breaking changes detected (e.g. {first_code})",
                is_breaking=True,
                breaking_changes=breaking_violations,
                compatible_changes=[],
            )

        # Content comparison for MINOR vs PATCH
        base_stripped = "".join(base_content.split())
        cand_stripped = "".join(candidate_content.split())

        if base_stripped != cand_stripped:
            rec_version = f"{major}.{minor + 1}.0"
            return SemVerRecommendation(
                current_version=current_version,
                recommended_version=rec_version,
                bump_type="MINOR",
                reason="Backward-compatible schema additions or modifications detected",
                is_breaking=False,
                breaking_changes=[],
                compatible_changes=["Non-breaking modifications or field additions"],
            )

        rec_version = f"{major}.{minor}.{patch + 1}"
        return SemVerRecommendation(
            current_version=current_version,
            recommended_version=rec_version,
            bump_type="PATCH",
            reason="No semantic schema alterations detected (patch level update)",
            is_breaking=False,
            breaking_changes=[],
            compatible_changes=[],
        )
