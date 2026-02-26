import json
from pathlib import Path

from domain.common.types import DerivationState
from domain.observation.tree import build_treedrawer_csv_lines
from domain.resume.codec import export_resume_text


def _fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "test-fixtures/cases/golden/tree-resume-v1.json"
    )


def _load_cases() -> list[dict]:
    data = json.loads(_fixture_path().read_text(encoding="utf-8"))
    assert data["version"] == "v1"
    cases = data["cases"]
    assert len(cases) == 30
    return cases


def test_golden_case_count_is_30() -> None:
    assert len(_load_cases()) == 30


def test_golden_tree_tree_cat_resume_cases_match() -> None:
    for case in _load_cases():
        state = DerivationState.model_validate(case["state"])
        kind = case["kind"]
        if kind in {"tree", "tree_cat"}:
            got = build_treedrawer_csv_lines(state=state, mode=kind)  # type: ignore[arg-type]
            assert got == case["expected_lines"], case["id"]
        elif kind == "resume":
            got_resume = export_resume_text(state)
            assert got_resume == case["expected_resume_text"], case["id"]
        else:
            raise AssertionError(f"Unsupported kind: {kind}")
