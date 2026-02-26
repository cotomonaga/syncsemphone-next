from pathlib import Path

from domain.lexicon.commit import CompatibilityCheckResult, commit_lexicon_yaml


def _seed_legacy_root(tmp_path: Path) -> Path:
    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir(parents=True, exist_ok=True)
    line = "\t".join(["1", "old", "old", "N", "0", "", "", "", "0", "", "", "", "", "", "id", "0", "", "", "", "", "", "", "", "", "", "", "", "", "", "0"])
    (legacy_root / "lexicon-all.csv").write_text(line + "\n", encoding="utf-8")
    return legacy_root


def test_commit_lexicon_yaml_success_without_compatibility_check(tmp_path: Path) -> None:
    legacy_root = _seed_legacy_root(tmp_path)
    yaml_text = """
entries:
  - no: 1
    entry: "new"
    phono: "new"
    category: "N"
    predication: []
    sync: []
    idslot: "id"
    semantics: []
    note: ""
"""

    result = commit_lexicon_yaml(
        grammar_id="imi03",
        yaml_text=yaml_text,
        legacy_root=legacy_root,
        project_root=tmp_path,
        run_compatibility_tests=False,
    )

    assert result.committed is True
    assert result.rolled_back is False
    assert result.compatibility_passed is True
    committed_text = (legacy_root / "lexicon-all.csv").read_text(encoding="utf-8")
    assert committed_text == result.committed_csv_text
    assert Path(result.backup_path).exists()


def test_commit_lexicon_yaml_rolls_back_on_compatibility_failure(tmp_path: Path) -> None:
    legacy_root = _seed_legacy_root(tmp_path)
    original = (legacy_root / "lexicon-all.csv").read_text(encoding="utf-8")
    yaml_text = """
entries:
  - no: 1
    entry: "new"
    phono: "new"
    category: "N"
    predication: []
    sync: []
    idslot: "id"
    semantics: []
    note: ""
"""

    def _fail_runner(_project_root: Path, _legacy_root: Path) -> CompatibilityCheckResult:
        return CompatibilityCheckResult(
            passed=False,
            command="pytest -q ...",
            return_code=1,
            stdout="failed",
            stderr="failure",
        )

    result = commit_lexicon_yaml(
        grammar_id="imi03",
        yaml_text=yaml_text,
        legacy_root=legacy_root,
        project_root=tmp_path,
        run_compatibility_tests=True,
        compatibility_runner=_fail_runner,
    )

    assert result.committed is False
    assert result.rolled_back is True
    assert result.compatibility_passed is False
    assert (legacy_root / "lexicon-all.csv").read_text(encoding="utf-8") == original


def test_commit_lexicon_yaml_returns_validation_error() -> None:
    result = commit_lexicon_yaml(
        grammar_id="imi03",
        yaml_text="entries: not-a-list",
        legacy_root=Path("/tmp/does-not-matter"),
        project_root=Path("/tmp/does-not-matter"),
        run_compatibility_tests=False,
    )

    assert result.committed is False
    assert result.errors
