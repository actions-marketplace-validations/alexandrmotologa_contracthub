"""Unit tests for Git Monorepo Scanner and GitHub Summary formatting."""

from contracthub.core.models import CompatibilityMode, Severity, Violation
from contracthub.core.scanner import FileScanResult, GitScanner, ScanSummary
from contracthub.tui.diff_viewer import render_github_summary


def test_git_scanner_file_detection():
    # Detect supported schema extensions
    files = GitScanner.get_changed_schema_files(target_ref="HEAD")
    assert isinstance(files, list)


def test_render_github_summary_passed():
    summary = ScanSummary(
        target_ref="origin/main",
        mode=CompatibilityMode.FULL,
        total_scanned=2,
        passed_count=2,
        failed_count=0,
        results=[
            FileScanResult(
                path="proto/order.proto", is_new_file=False, is_compatible=True, total_checks=10
            ),
            FileScanResult(
                path="openapi/api.json", is_new_file=True, is_compatible=True, total_checks=1
            ),
        ],
    )
    md = render_github_summary(summary)
    assert "# ContractHub Schema Scan Report" in md
    assert "Passed" in md
    assert "`proto/order.proto`" in md
    assert "`openapi/api.json`" in md


def test_render_github_summary_failed():
    violation = Violation(
        code="PROTO_TAG_MUTATED",
        severity=Severity.BREAKING,
        path="Order.id",
        message="Tag changed from 1 to 2",
        suggestion="Keep tag 1",
    )
    summary = ScanSummary(
        target_ref="origin/main",
        mode=CompatibilityMode.FULL,
        total_scanned=1,
        passed_count=0,
        failed_count=1,
        results=[
            FileScanResult(
                path="proto/breaking.proto",
                is_new_file=False,
                is_compatible=False,
                violations=[violation],
                total_checks=5,
            )
        ],
    )
    md = render_github_summary(summary)
    assert "Failed" in md
    assert "<details><summary>" in md
    assert "PROTO_TAG_MUTATED" in md
    assert "Keep tag 1" in md
