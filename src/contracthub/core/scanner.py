"""Git Monorepo Scanner.

Scans local Git repository working tree against a target reference (e.g. origin/main)
to detect modified schema files, compares each against its base version, and aggregates
compatibility violations.
"""

import subprocess
from pathlib import Path

from pydantic import BaseModel, Field

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, CompatibilityResult, Severity, Violation

SUPPORTED_EXTENSIONS = {".proto", ".json", ".yaml", ".yml", ".avsc"}


class FileScanResult(BaseModel):
    path: str
    is_new_file: bool = False
    is_compatible: bool = True
    violations: list[Violation] = Field(default_factory=list)
    total_checks: int = 0

    @property
    def breaking_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.BREAKING)


class ScanSummary(BaseModel):
    target_ref: str
    mode: CompatibilityMode
    total_scanned: int = 0
    passed_count: int = 0
    failed_count: int = 0
    results: list[FileScanResult] = Field(default_factory=list)

    @property
    def is_compatible(self) -> bool:
        return self.failed_count == 0


class GitScanner:
    """Executes multi-file schema compatibility audits against Git revisions."""

    @classmethod
    def get_changed_schema_files(
        cls,
        target_ref: str = "origin/main",
        repo_root: Path | None = None,
    ) -> list[str]:
        cwd = str(repo_root) if repo_root else None

        # 1. Try git diff against target_ref
        try:
            cmd = ["git", "diff", "--name-only", target_ref, "--"]
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            else:
                # Fallback to git status if target_ref fails (e.g. no origin/main)
                proc_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                lines = []
                for line in proc_status.stdout.splitlines():
                    if len(line) > 3:
                        lines.append(line[3:].strip())
        except (subprocess.SubprocessError, OSError):
            return []

        # Filter by supported extensions
        matched = []
        for file_path in lines:
            p = Path(file_path)
            if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                matched.append(file_path.replace("\\", "/"))
        return sorted(set(matched))

    @classmethod
    def get_file_content_at_ref(
        cls,
        file_path: str,
        target_ref: str = "origin/main",
        repo_root: Path | None = None,
    ) -> str | None:
        cwd = str(repo_root) if repo_root else None
        norm_path = file_path.replace("\\", "/")
        try:
            proc = subprocess.run(
                ["git", "show", f"{target_ref}:{norm_path}"],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                return proc.stdout
            return None
        except (subprocess.SubprocessError, OSError):
            return None

    @classmethod
    def scan(
        cls,
        target_ref: str = "origin/main",
        mode: CompatibilityMode = CompatibilityMode.FULL,
        repo_root: Path | None = None,
    ) -> ScanSummary:
        root = repo_root or Path.cwd()
        changed_files = cls.get_changed_schema_files(target_ref=target_ref, repo_root=root)

        summary = ScanSummary(
            target_ref=target_ref,
            mode=mode,
            total_scanned=len(changed_files),
        )

        for rel_path in changed_files:
            full_path = root / rel_path
            if not full_path.exists():
                # File deleted in candidate - if candidate deleted a whole schema file
                continue

            try:
                candidate_content = full_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            base_content = cls.get_file_content_at_ref(
                file_path=rel_path,
                target_ref=target_ref,
                repo_root=root,
            )

            if base_content is None:
                # Newly created schema in PR
                res = FileScanResult(
                    path=rel_path,
                    is_new_file=True,
                    is_compatible=True,
                    violations=[],
                    total_checks=1,
                )
                summary.passed_count += 1
                summary.results.append(res)
                continue

            schema_type = SchemaComparator.detect_schema_type(
                content=candidate_content,
                filename=rel_path,
            )

            cmp_result: CompatibilityResult = SchemaComparator.compare_strings(
                base_content=base_content,
                candidate_content=candidate_content,
                schema_type=schema_type,
                mode=mode,
            )

            file_res = FileScanResult(
                path=rel_path,
                is_new_file=False,
                is_compatible=cmp_result.is_compatible,
                violations=cmp_result.violations,
                total_checks=cmp_result.total_checks,
            )

            if file_res.is_compatible:
                summary.passed_count += 1
            else:
                summary.failed_count += 1

            summary.results.append(file_res)

        return summary
