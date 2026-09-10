"""Git Pre-commit Hook Initializer for ContractHub."""

from __future__ import annotations

import os
from pathlib import Path

PRE_COMMIT_SCRIPT = """#!/usr/bin/env bash
# ContractHub Pre-commit Hook
# Automatically blocks breaking contract changes before committing.
set -e

echo "🔍 [ContractHub] Running schema compatibility validation..."

if command -v contracthub >/dev/null 2>&1; then
    contracthub scan --repo-path . --base-ref HEAD --mode BACKWARD
elif command -v uv >/dev/null 2>&1; then
    uv run contracthub scan --repo-path . --base-ref HEAD --mode BACKWARD
else
    python -m contracthub.cli scan --repo-path . --base-ref HEAD --mode BACKWARD
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ [ContractHub] Commit rejected! Incompatible breaking schema changes detected."
    echo "💡 Run 'contracthub diff' or 'contracthub fix' to inspect or remediate."
    exit 1
fi

echo "✅ [ContractHub] All schema contracts are compatible."
exit 0
"""

PRE_COMMIT_CONFIG_YAML = """# ContractHub Pre-commit Framework Configuration
# Run: pre-commit run --all-files
repos:
  - repo: local
    hooks:
      - id: contracthub-linter
        name: ContractHub Contract Compatibility Linter
        entry: contracthub scan --mode BACKWARD
        language: system
        types: [file]
        files: \\.(proto|avsc|json|graphql|gql)$
        pass_filenames: false
"""


def init_git_hooks(repo_path: Path | str = ".", force: bool = False) -> tuple[bool, list[str]]:
    """Install ContractHub pre-commit hooks into a git repository."""
    root = Path(repo_path).resolve()
    git_dir = root / ".git"

    if not git_dir.exists():
        return False, [f"'{root}' is not a git repository (missing .git directory)."]

    messages: list[str] = []
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_file = hooks_dir / "pre-commit"
    if hook_file.exists() and not force:
        messages.append(f"Pre-commit hook already exists at {hook_file} (use --force to overwrite)")
    else:
        hook_file.write_text(PRE_COMMIT_SCRIPT, encoding="utf-8")
        try:
            os.chmod(hook_file, 0o755)
        except OSError:
            pass
        messages.append(f"Installed executable Git hook at {hook_file}")

    config_file = root / ".pre-commit-config.yaml"
    if config_file.exists() and not force:
        messages.append(f".pre-commit-config.yaml already exists at {config_file}")
    else:
        config_file.write_text(PRE_COMMIT_CONFIG_YAML, encoding="utf-8")
        messages.append(f"Generated {config_file}")

    return True, messages
