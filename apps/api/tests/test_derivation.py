import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app
from domain.grammar.rule_catalog import get_rule_number_by_name


def _legacy_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_num_file(relative_path: str) -> str:
    return (_legacy_root() / relative_path).read_text(encoding="utf-8")


def _synthetic_pickup_state() -> dict:
    mover = ["x200-1", "N", [], ["1,11,ga"], "x200-1", [], "", ["zero", "zero"]]
    head = ["x201-1", "V", [], ["v"], "x201-1", [], "", ["zero", "zero"]]
    target = ["x1-1", "V", [], [], "x1-1", [], "", [mover, head]]
    filler = ["x2-1", "N", [], [], "x2-1", [], "", ["zero", "zero"]]
    return {
        "grammar_id": "japanese2",
        "memo": "synthetic-pickup",
        "newnum": 300,
        "basenum": 2,
        "history": "",
        "base": [None, target, filler],
    }


def _synthetic_landing_state() -> dict:
    mover = [
        "x300-1",
        "N",
        [],
        ["3,107,move", "1,11,ga"],
        "x300-1",
        [],
        "",
        ["zero", "zero"],
    ]
    payload = json.dumps(mover, ensure_ascii=False, separators=(",", ":"))
    target = [
        "x1-1",
        "V",
        [],
        [f"3,106,{payload}"],
        "x1-1",
        [],
        "",
        ["zero", "zero"],
    ]
    filler = ["x2-1", "N", [], [], "x2-1", [], "", ["zero", "zero"]]
    return {
        "grammar_id": "japanese2",
        "memo": "synthetic-landing",
        "newnum": 400,
        "basenum": 2,
        "history": "",
        "base": [None, target, filler],
    }


def test_derivation_init_imi03_04_num() -> None:
    client = TestClient(app)
    payload = {
        "grammar_id": "imi03",
        "numeration_text": _load_num_file("imi03/set-numeration/04.num"),
        "legacy_root": str(_legacy_root()),
    }
    response = client.post("/v1/derivation/init", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["memo"] == "ジョンがメアリを追いかけた"
    assert body["basenum"] == 6
    assert body["newnum"] == 7
    assert body["base"][5][1] == "V"  # 187 追いかける
    assert body["base"][6][1] == "T"  # 203 た


def test_derivation_numeration_generate_from_sentence_with_manual_tokens() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/derivation/numeration/generate",
        json={
            "grammar_id": "imi03",
            "sentence": "ジョンがメアリを追いかけた",
            "tokens": ["ジョン", "が", "メアリ", "を", "追いかける", "た"],
            "legacy_root": str(_legacy_root()),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["memo"] == "ジョンがメアリを追いかけた"
    assert body["lexicon_ids"] == [60, 19, 103, 23, 187, 203]
    first_row = body["numeration_text"].splitlines()[0].split("\t")
    assert first_row[1:7] == ["60", "19", "103", "23", "187", "203"]


def test_derivation_init_from_sentence_matches_init_with_same_lexicon_ids() -> None:
    client = TestClient(app)
    from_sentence = client.post(
        "/v1/derivation/init/from-sentence",
        json={
            "grammar_id": "imi03",
            "sentence": "ジョンがメアリを追いかけた",
            "tokens": ["ジョン", "が", "メアリ", "を", "追いかける", "た"],
            "legacy_root": str(_legacy_root()),
        },
    )
    assert from_sentence.status_code == 200
    from_sentence_body = from_sentence.json()

    numeration_text = from_sentence_body["numeration"]["numeration_text"]
    by_init = client.post(
        "/v1/derivation/init",
        json={
            "grammar_id": "imi03",
            "numeration_text": numeration_text,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_init.status_code == 200

    assert from_sentence_body["state"] == by_init.json()
    assert from_sentence_body["state"]["basenum"] == 6
    assert from_sentence_body["state"]["base"][5][1] == "V"
    assert from_sentence_body["state"]["base"][6][1] == "T"


def test_derivation_numeration_generate_returns_400_for_unknown_token() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/derivation/numeration/generate",
        json={
            "grammar_id": "imi03",
            "sentence": "未知語",
            "tokens": ["未知語"],
            "legacy_root": str(_legacy_root()),
        },
    )
    assert response.status_code == 400
    assert "Unknown token" in response.json()["detail"]


def test_derivation_numeration_tokenize_returns_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTokenizer:
        def tokenize(self, sentence: str, split_mode: str = "C") -> list[str]:
            if split_mode == "A":
                return ["ジョ", "ン", "が"]
            return ["ジョン", "が"]

    monkeypatch.setattr(
        "app.api.v1.derivation.SudachiMorphTokenizer",
        lambda dictionary="core": FakeTokenizer(),
    )

    client = TestClient(app)
    response = client.post(
        "/v1/derivation/numeration/tokenize",
        json={
            "grammar_id": "imi03",
            "sentence": "ジョンが",
            "split_mode": "A",
            "legacy_root": str(_legacy_root()),
        },
    )
    assert response.status_code == 200
    assert response.json()["tokens"] == ["ジョ", "ン", "が"]


def test_derivation_candidates_hypothesis_loop_pairs() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "imi03",
        "numeration_text": _load_num_file("imi03/set-numeration/04.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    state = init_response.json()

    # 実験A: RH/LH を _03 として観察
    base_03_vt = client.post(
        "/v1/derivation/candidates",
        json={
            "state": state,
            "left": 5,
            "right": 6,
            "rh_merge_version": "03",
            "lh_merge_version": "03",
        },
    )
    assert base_03_vt.status_code == 200
    assert [row["rule_name"] for row in base_03_vt.json()] == [
        "RH-Merge",
        "LH-Merge",
        "zero-Merge",
    ]

    # 実験B: RH/LH を _04 に差し替えた観察（right=T）
    swap_04_vt = client.post(
        "/v1/derivation/candidates",
        json={
            "state": state,
            "left": 5,
            "right": 6,
            "rh_merge_version": "04",
            "lh_merge_version": "04",
        },
    )
    assert swap_04_vt.status_code == 200
    assert [row["rule_name"] for row in swap_04_vt.json()] == [
        "LH-Merge",
        "zero-Merge",
    ]

    # 実験B: right=J の観察（left=60, right=19）
    swap_04_nj = client.post(
        "/v1/derivation/candidates",
        json={
            "state": state,
            "left": 1,
            "right": 2,
            "rh_merge_version": "04",
            "lh_merge_version": "04",
        },
    )
    assert swap_04_nj.status_code == 200
    assert [row["rule_name"] for row in swap_04_nj.json()] == ["RH-Merge"]


def test_derivation_execute_and_resume_roundtrip() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "imi03",
        "numeration_text": _load_num_file("imi03/set-numeration/04.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    t1_response = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "LH-Merge",
            "left": 5,
            "right": 6,
        },
    )
    assert t1_response.status_code == 200
    t1 = t1_response.json()
    assert t1["basenum"] == 5

    t2_response = client.post(
        "/v1/derivation/execute",
        json={
            "state": t1,
            "rule_name": "RH-Merge",
            "left": 1,
            "right": 2,
        },
    )
    assert t2_response.status_code == 200
    t2 = t2_response.json()
    assert t2["basenum"] == 4

    for state in (t0, t1, t2):
        export_response = client.post(
            "/v1/derivation/resume/export",
            json={"state": state},
        )
        assert export_response.status_code == 200
        resume_text = export_response.json()["resume_text"]
        import_response = client.post(
            "/v1/derivation/resume/import",
            json={"resume_text": resume_text},
        )
        assert import_response.status_code == 200
        restored = import_response.json()
        assert restored["memo"] == state["memo"]
        assert restored["newnum"] == state["newnum"]
        assert restored["basenum"] == state["basenum"]
        assert restored["history"] == state["history"]
        assert restored["base"] == state["base"]


def test_derivation_execute_accepts_rule_number() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "imi03",
        "numeration_text": _load_num_file("imi03/set-numeration/04.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    by_name = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "LH-Merge",
            "left": 5,
            "right": 6,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_name.status_code == 200

    by_number = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_number": 2,
            "left": 5,
            "right": 6,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_number.status_code == 200
    assert by_number.json() == by_name.json()


def test_derivation_execute_jmerge_japanese2_accepts_rule_number() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/00-00-01.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    by_name = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "J-Merge",
            "left": 1,
            "right": 2,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_name.status_code == 200

    by_number = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_number": 7,
            "left": 1,
            "right": 2,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_number.status_code == 200
    assert by_number.json() == by_name.json()


def test_derivation_execute_single_zero_merge_japanese2_accepts_rule_number() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/05-03-09.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    by_name = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "zero-Merge",
            "check": 4,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_name.status_code == 200

    rule_no = get_rule_number_by_name(
        grammar_id="japanese2",
        rule_name="zero-Merge",
        legacy_root=_legacy_root(),
    )
    assert rule_no is not None

    by_number = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_number": rule_no,
            "check": 4,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_number.status_code == 200
    assert by_number.json() == by_name.json()


@pytest.mark.parametrize(
    ("numeration_relpath", "rule_name", "left", "right"),
    [
        ("japanese2/set-numeration/00-00-01.num", "J-Merge", 1, 2),
        ("japanese2/set-numeration/03-05-831.num", "property-Merge", 8, 9),
        ("japanese2/set-numeration/03-05-831.num", "rel-Merge", 10, 1),
        ("japanese2/set-numeration/05-03-09.num", "property-da", 1, 4),
        ("japanese2/set-numeration/08-05-45.num", "P-Merge", 1, 5),
    ],
)
def test_derivation_execute_japanese2_double_rules_accept_rule_number(
    numeration_relpath: str,
    rule_name: str,
    left: int,
    right: int,
) -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file(numeration_relpath),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    by_name = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": rule_name,
            "left": left,
            "right": right,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_name.status_code == 200

    rule_no = get_rule_number_by_name(
        grammar_id="japanese2",
        rule_name=rule_name,
        legacy_root=_legacy_root(),
    )
    assert rule_no is not None
    by_number = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_number": rule_no,
            "left": left,
            "right": right,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_number.status_code == 200
    assert by_number.json() == by_name.json()


@pytest.mark.parametrize(
    ("numeration_relpath", "rule_name", "left", "right"),
    [
        ("japanese2/set-numeration/00-00-01.num", "RH-Merge", 1, 2),
        ("japanese2/set-numeration/03-01-29.num", "sase1", 7, 8),
        ("japanese2/set-numeration/03-05-831.num", "sase2", 9, 8),
        ("japanese2/set-numeration/03-05-831.num", "rare1", 7, 9),
        ("japanese2/set-numeration/03-05-832.num", "rare2", 7, 9),
    ],
)
def test_derivation_execute_japanese2_additional_double_rules_accept_rule_number(
    numeration_relpath: str,
    rule_name: str,
    left: int,
    right: int,
) -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file(numeration_relpath),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    by_name = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": rule_name,
            "left": left,
            "right": right,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_name.status_code == 200

    rule_no = get_rule_number_by_name(
        grammar_id="japanese2",
        rule_name=rule_name,
        legacy_root=_legacy_root(),
    )
    assert rule_no is not None
    by_number = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_number": rule_no,
            "left": left,
            "right": right,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_number.status_code == 200
    assert by_number.json() == by_name.json()


@pytest.mark.parametrize("grammar_id", ["imi01", "imi02"])
def test_derivation_execute_imi_rule_number_roundtrip(grammar_id: str) -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": grammar_id,
        "numeration_text": _load_num_file(f"{grammar_id}/set-numeration/04.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    by_name = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "LH-Merge",
            "left": 5,
            "right": 6,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_name.status_code == 200

    rule_no = get_rule_number_by_name(
        grammar_id=grammar_id,
        rule_name="LH-Merge",
        legacy_root=_legacy_root(),
    )
    assert rule_no is not None
    by_number = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_number": rule_no,
            "left": 5,
            "right": 6,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_number.status_code == 200
    assert by_number.json() == by_name.json()


def test_derivation_execute_japanese2_property_no_accepts_rule_number_synthetic() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": "synthetic\t60\t19\n\t\t\n\t1\t2",
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    state = init_response.json()

    # Perl differential と同じ最小条件を与えて property-no を成立させる。
    state["base"][1][4] = "x1-1"
    state["base"][2][3] = ["1,1,N", "2,3,N"]

    by_name = client.post(
        "/v1/derivation/execute",
        json={
            "state": state,
            "rule_name": "property-no",
            "left": 1,
            "right": 2,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_name.status_code == 200

    rule_no = get_rule_number_by_name(
        grammar_id="japanese2",
        rule_name="property-no",
        legacy_root=_legacy_root(),
    )
    assert rule_no is not None
    by_number = client.post(
        "/v1/derivation/execute",
        json={
            "state": state,
            "rule_number": rule_no,
            "left": 1,
            "right": 2,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_number.status_code == 200
    assert by_number.json() == by_name.json()


@pytest.mark.parametrize(
    ("state_factory", "rule_name", "check"),
    [
        ("num:05-03-09", "zero-Merge", 4),
        ("num:08-05-45", "Partitioning", 5),
        ("synthetic:pickup", "Pickup", 1),
        ("synthetic:landing", "Landing", 1),
    ],
)
def test_derivation_execute_japanese2_single_rules_accept_rule_number(
    state_factory: str,
    rule_name: str,
    check: int,
) -> None:
    client = TestClient(app)

    if state_factory == "num:05-03-09":
        init_payload = {
            "grammar_id": "japanese2",
            "numeration_text": _load_num_file("japanese2/set-numeration/05-03-09.num"),
            "legacy_root": str(_legacy_root()),
        }
        init_response = client.post("/v1/derivation/init", json=init_payload)
        assert init_response.status_code == 200
        state = init_response.json()
    elif state_factory == "num:08-05-45":
        init_payload = {
            "grammar_id": "japanese2",
            "numeration_text": _load_num_file("japanese2/set-numeration/08-05-45.num"),
            "legacy_root": str(_legacy_root()),
        }
        init_response = client.post("/v1/derivation/init", json=init_payload)
        assert init_response.status_code == 200
        state = init_response.json()
    elif state_factory == "synthetic:pickup":
        state = _synthetic_pickup_state()
    elif state_factory == "synthetic:landing":
        state = _synthetic_landing_state()
    else:
        raise AssertionError(f"unsupported state_factory: {state_factory}")

    by_name = client.post(
        "/v1/derivation/execute",
        json={
            "state": state,
            "rule_name": rule_name,
            "check": check,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_name.status_code == 200

    rule_no = get_rule_number_by_name(
        grammar_id="japanese2",
        rule_name=rule_name,
        legacy_root=_legacy_root(),
    )
    assert rule_no is not None
    by_number = client.post(
        "/v1/derivation/execute",
        json={
            "state": state,
            "rule_number": rule_no,
            "check": check,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_number.status_code == 200
    assert by_number.json() == by_name.json()


def test_derivation_execute_japanese2_single_rule_accepts_left_alias_for_check() -> None:
    client = TestClient(app)
    state = _synthetic_landing_state()

    rule_no = get_rule_number_by_name(
        grammar_id="japanese2",
        rule_name="Landing",
        legacy_root=_legacy_root(),
    )
    assert rule_no is not None
    by_left_alias = client.post(
        "/v1/derivation/execute",
        json={
            "state": state,
            "rule_number": rule_no,
            "left": 1,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_left_alias.status_code == 200

    by_check = client.post(
        "/v1/derivation/execute",
        json={
            "state": state,
            "rule_name": "Landing",
            "check": 1,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert by_check.status_code == 200
    assert by_left_alias.json() == by_check.json()


def test_derivation_execute_rule_number_unknown_returns_400() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/00-00-01.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    response = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_number": 9999,
            "left": 1,
            "right": 2,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert response.status_code == 400
    assert "Unknown rule_number" in response.json()["detail"]


def test_derivation_execute_rule_name_number_mismatch_returns_400() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/00-00-01.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    rh_number = get_rule_number_by_name(
        grammar_id="japanese2",
        rule_name="RH-Merge",
        legacy_root=_legacy_root(),
    )
    assert rh_number is not None
    response = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "J-Merge",
            "rule_number": rh_number,
            "left": 1,
            "right": 2,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert response.status_code == 400
    assert "rule_name/rule_number mismatch" in response.json()["detail"]


def test_derivation_candidates_japanese2_property_rel_rules() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/03-05-831.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    state = init_response.json()

    property_pair = client.post(
        "/v1/derivation/candidates",
        json={"state": state, "left": 8, "right": 9},
    )
    assert property_pair.status_code == 200
    assert [row["rule_name"] for row in property_pair.json()] == [
        "rare1",
        "property-Merge",
        "zero-Merge",
        "zero-Merge",
    ]

    rel_pair = client.post(
        "/v1/derivation/candidates",
        json={"state": state, "left": 10, "right": 1},
    )
    assert rel_pair.status_code == 200
    assert [row["rule_name"] for row in rel_pair.json()] == [
        "rel-Merge",
        "RH-Merge",
        "zero-Merge",
    ]


def test_derivation_candidates_japanese2_property_da_pmerge_rules() -> None:
    client = TestClient(app)

    property_da_init = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/05-03-09.num"),
        "legacy_root": str(_legacy_root()),
    }
    property_da_state = client.post("/v1/derivation/init", json=property_da_init)
    assert property_da_state.status_code == 200
    property_da_candidates = client.post(
        "/v1/derivation/candidates",
        json={"state": property_da_state.json(), "left": 1, "right": 4},
    )
    assert property_da_candidates.status_code == 200
    assert [row["rule_name"] for row in property_da_candidates.json()] == [
        "property-da",
        "RH-Merge",
        "zero-Merge",
    ]

    pmerge_init = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/08-05-45.num"),
        "legacy_root": str(_legacy_root()),
    }
    pmerge_state = client.post("/v1/derivation/init", json=pmerge_init)
    assert pmerge_state.status_code == 200
    pmerge_candidates = client.post(
        "/v1/derivation/candidates",
        json={"state": pmerge_state.json(), "left": 1, "right": 5},
    )
    assert pmerge_candidates.status_code == 200
    assert [row["rule_name"] for row in pmerge_candidates.json()] == [
        "P-Merge",
        "RH-Merge",
        "Partitioning",
    ]


def test_derivation_execute_japanese2_partitioning_single_rule() -> None:
    client = TestClient(app)
    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/08-05-45.num"),
        "legacy_root": str(_legacy_root()),
    }
    init_response = client.post("/v1/derivation/init", json=init_payload)
    assert init_response.status_code == 200
    t0 = init_response.json()

    execute_response = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "Partitioning",
            "check": 5,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert execute_response.status_code == 200
    t1 = execute_response.json()
    assert t1["basenum"] == t0["basenum"]  # single rule: base size unchanged
    assert t1["history"].endswith("Partitioning) ")


def test_derivation_candidates_japanese2_pickup_landing_single_rules() -> None:
    client = TestClient(app)

    pickup_candidates = client.post(
        "/v1/derivation/candidates",
        json={"state": _synthetic_pickup_state(), "left": 1, "right": 2},
    )
    assert pickup_candidates.status_code == 200
    pickup_rule_names = [row["rule_name"] for row in pickup_candidates.json()]
    assert "Pickup" in pickup_rule_names

    landing_candidates = client.post(
        "/v1/derivation/candidates",
        json={"state": _synthetic_landing_state(), "left": 1, "right": 2},
    )
    assert landing_candidates.status_code == 200
    landing_rule_names = [row["rule_name"] for row in landing_candidates.json()]
    assert "Landing" in landing_rule_names


def test_derivation_execute_japanese2_zero_pickup_landing_single_rules() -> None:
    client = TestClient(app)

    init_payload = {
        "grammar_id": "japanese2",
        "numeration_text": _load_num_file("japanese2/set-numeration/05-03-09.num"),
        "legacy_root": str(_legacy_root()),
    }
    zero_init = client.post("/v1/derivation/init", json=init_payload)
    assert zero_init.status_code == 200
    t0 = zero_init.json()

    zero_execute = client.post(
        "/v1/derivation/execute",
        json={
            "state": t0,
            "rule_name": "zero-Merge",
            "check": 4,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert zero_execute.status_code == 200
    t1 = zero_execute.json()
    assert t1["basenum"] == t0["basenum"]
    assert t1["newnum"] == t0["newnum"] + 1
    assert t1["history"].endswith("zero-Merge) ")

    pickup_execute = client.post(
        "/v1/derivation/execute",
        json={
            "state": _synthetic_pickup_state(),
            "rule_name": "Pickup",
            "check": 1,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert pickup_execute.status_code == 200
    p1 = pickup_execute.json()
    assert p1["basenum"] == 2
    assert p1["base"][1][7][0] == "zero"
    assert any("3,106," in value for value in p1["base"][1][3])
    assert p1["history"].endswith("Pickup) ")

    landing_execute = client.post(
        "/v1/derivation/execute",
        json={
            "state": _synthetic_landing_state(),
            "rule_name": "Landing",
            "check": 1,
            "legacy_root": str(_legacy_root()),
        },
    )
    assert landing_execute.status_code == 200
    l1 = landing_execute.json()
    assert l1["basenum"] == 2
    assert l1["base"][1][7][0][0] == "x300-1"
    assert all("107" not in value for value in l1["base"][1][7][0][3])
    assert l1["history"].endswith("Landing) ")
