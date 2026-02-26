from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable, Optional

from domain.lexicon.importer import validate_lexicon_yaml_text
from domain.lexicon.legacy_loader import resolve_legacy_lexicon_path


@dataclass(frozen=True)
class CompatibilityCheckResult:
    passed: bool
    command: str
    return_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class LexiconCommitResult:
    grammar_id: str
    lexicon_path: str
    backup_path: str
    entry_count: int
    committed: bool
    rolled_back: bool
    compatibility_passed: bool
    run_compatibility_tests: bool
    message: str
    errors: list[str]
    normalized_yaml_text: str
    committed_csv_text: str
    command: str
    stdout: str
    stderr: str


def _atomic_replace_text(path: Path, text: str) -> None:
    tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}-{os.urandom(4).hex()}")
    tmp_path.write_text(text, encoding="utf-8")
    os.replace(tmp_path, path)


def _default_compatibility_runner(project_root: Path, legacy_root: Path) -> CompatibilityCheckResult:
    tests = [
        "packages/domain/tests/test_differential_candidates_perl.py",
        "packages/domain/tests/test_differential_execute_perl.py",
        "packages/domain/tests/test_differential_tree_perl.py",
        "packages/domain/tests/test_differential_semantics_perl.py",
    ]
    cmd = [sys.executable, "-m", "pytest", "-q", *tests]
    env = os.environ.copy()
    py_paths = [str(project_root / "packages" / "domain" / "src"), str(project_root / "apps" / "api")]
    if env.get("PYTHONPATH"):
        py_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = ":".join(py_paths)
    env["SYNCSEMPHONE_LEGACY_ROOT"] = str(legacy_root)

    command_text = " ".join(cmd)
    try:
        completed = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=1200,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CompatibilityCheckResult(
            passed=False,
            command=command_text,
            return_code=124,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + "\nCompatibility checks timed out",
        )

    return CompatibilityCheckResult(
        passed=completed.returncode == 0,
        command=command_text,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _tail_text(text: str, max_lines: int = 120) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def commit_lexicon_yaml(
    *,
    grammar_id: str,
    yaml_text: str,
    legacy_root: Path,
    project_root: Path,
    source_csv: Optional[str] = None,
    run_compatibility_tests: bool = True,
    compatibility_runner: Optional[Callable[[Path, Path], CompatibilityCheckResult]] = None,
) -> LexiconCommitResult:
    validated = validate_lexicon_yaml_text(
        grammar_id=grammar_id,
        yaml_text=yaml_text,
        source_csv=source_csv,
    )
    if not validated.valid:
        return LexiconCommitResult(
            grammar_id=grammar_id,
            lexicon_path="",
            backup_path="",
            entry_count=validated.entry_count,
            committed=False,
            rolled_back=False,
            compatibility_passed=False,
            run_compatibility_tests=run_compatibility_tests,
            message="YAML validation failed",
            errors=validated.errors,
            normalized_yaml_text=validated.normalized_yaml_text,
            committed_csv_text=validated.preview_csv_text,
            command="",
            stdout="",
            stderr="",
        )

    lexicon_path = resolve_legacy_lexicon_path(legacy_root=legacy_root, grammar_id=grammar_id)
    if not lexicon_path.exists():
        return LexiconCommitResult(
            grammar_id=grammar_id,
            lexicon_path=str(lexicon_path),
            backup_path="",
            entry_count=validated.entry_count,
            committed=False,
            rolled_back=False,
            compatibility_passed=False,
            run_compatibility_tests=run_compatibility_tests,
            message=f"Lexicon file not found: {lexicon_path}",
            errors=[f"Lexicon file not found: {lexicon_path}"],
            normalized_yaml_text=validated.normalized_yaml_text,
            committed_csv_text=validated.preview_csv_text,
            command="",
            stdout="",
            stderr="",
        )

    old_text = lexicon_path.read_text(encoding="utf-8")
    backup_stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_path = lexicon_path.with_name(f"{lexicon_path.name}.bak.{backup_stamp}")
    backup_path.write_text(old_text, encoding="utf-8")

    command = ""
    stdout = ""
    stderr = ""

    _atomic_replace_text(lexicon_path, validated.preview_csv_text)

    passed = True
    if run_compatibility_tests:
        runner = compatibility_runner or _default_compatibility_runner
        check = runner(project_root, legacy_root)
        passed = check.passed
        command = check.command
        stdout = check.stdout
        stderr = check.stderr

    if not passed:
        _atomic_replace_text(lexicon_path, old_text)
        return LexiconCommitResult(
            grammar_id=grammar_id,
            lexicon_path=str(lexicon_path),
            backup_path=str(backup_path),
            entry_count=validated.entry_count,
            committed=False,
            rolled_back=True,
            compatibility_passed=False,
            run_compatibility_tests=run_compatibility_tests,
            message="Compatibility checks failed. Rolled back to previous CSV.",
            errors=["Compatibility checks failed"],
            normalized_yaml_text=validated.normalized_yaml_text,
            committed_csv_text=validated.preview_csv_text,
            command=command,
            stdout=_tail_text(stdout),
            stderr=_tail_text(stderr),
        )

    return LexiconCommitResult(
        grammar_id=grammar_id,
        lexicon_path=str(lexicon_path),
        backup_path=str(backup_path),
        entry_count=validated.entry_count,
        committed=True,
        rolled_back=False,
        compatibility_passed=True,
        run_compatibility_tests=run_compatibility_tests,
        message="Committed lexicon YAML to CSV successfully",
        errors=[],
        normalized_yaml_text=validated.normalized_yaml_text,
        committed_csv_text=validated.preview_csv_text,
        command=command,
        stdout=_tail_text(stdout),
        stderr=_tail_text(stderr),
    )
