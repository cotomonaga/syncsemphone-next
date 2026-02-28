from __future__ import annotations

from contextlib import contextmanager
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from fastapi.testclient import TestClient

from app.api.v1 import lexicon_ext
from app.main import app


def _seed_lexicon_csv(path: Path) -> None:
    row = "\t".join(
        [
            "1",
            "ジョン",
            "ジョン",
            "N",
            "0",
            "",
            "",
            "",
            "0",
            "",
            "",
            "",
            "",
            "",
            "x1-1",
            "0",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "0",
        ]
    )
    path.write_text(row + "\n", encoding="utf-8")


class _FakeCursor:
    def __init__(self, store: dict[str, Any]) -> None:
        self._store = store
        self._rows: list[Any] = []
        self.rowcount = 0

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        params = params or ()
        compact = " ".join(sql.split())
        now = datetime(2026, 2, 28, tzinfo=timezone.utc)
        self._rows = []
        self.rowcount = 0

        if compact.startswith("CREATE TABLE IF NOT EXISTS"):
            return

        if "INSERT INTO lexicon_value_dictionary" in compact:
            next_id = self._store["value_next_id"]
            self._store["value_next_id"] += 1
            item = {
                "id": next_id,
                "kind": params[0],
                "normalized_value": params[1],
                "display_value": params[2],
                "metadata_json": json.loads(params[3]) if isinstance(params[3], str) else (params[3] or {}),
                "created_at": now,
                "updated_at": now,
            }
            self._store["values"][next_id] = item
            self._rows = [
                (
                    item["id"],
                    item["kind"],
                    item["normalized_value"],
                    item["display_value"],
                    item["metadata_json"],
                    item["created_at"],
                    item["updated_at"],
                )
            ]
            return

        if "UPDATE lexicon_value_dictionary" in compact and "RETURNING" in compact:
            item = self._store["values"].get(params[3])
            if item is None:
                self._rows = []
                return
            item["normalized_value"] = params[0]
            item["display_value"] = params[1]
            item["metadata_json"] = json.loads(params[2]) if isinstance(params[2], str) else (params[2] or {})
            item["updated_at"] = now
            self._rows = [
                (
                    item["id"],
                    item["kind"],
                    item["normalized_value"],
                    item["display_value"],
                    item["metadata_json"],
                    item["created_at"],
                    item["updated_at"],
                )
            ]
            return

        if "SELECT id, kind, normalized_value, display_value, metadata_json, created_at, updated_at FROM lexicon_value_dictionary WHERE kind = %s" in compact:
            kind = params[0]
            values = [
                row
                for row in self._store["values"].values()
                if row["kind"] == kind
            ]
            values.sort(key=lambda row: row["display_value"])
            self._rows = [
                (
                    row["id"],
                    row["kind"],
                    row["normalized_value"],
                    row["display_value"],
                    row["metadata_json"],
                    row["created_at"],
                    row["updated_at"],
                )
                for row in values
            ]
            return

        if "SELECT id, kind, normalized_value, display_value, metadata_json, created_at, updated_at FROM lexicon_value_dictionary ORDER BY kind, display_value" in compact:
            values = sorted(self._store["values"].values(), key=lambda row: (row["kind"], row["display_value"]))
            self._rows = [
                (
                    row["id"],
                    row["kind"],
                    row["normalized_value"],
                    row["display_value"],
                    row["metadata_json"],
                    row["created_at"],
                    row["updated_at"],
                )
                for row in values
            ]
            return

        if "SELECT id, kind, display_value FROM lexicon_value_dictionary WHERE id = %s" in compact:
            item = self._store["values"].get(params[0])
            self._rows = [] if item is None else [(item["id"], item["kind"], item["display_value"])]
            return

        if "DELETE FROM lexicon_value_dictionary WHERE id = %s" in compact:
            removed = self._store["values"].pop(params[0], None)
            self.rowcount = 0 if removed is None else 1
            return

        if "INSERT INTO lexicon_item_num_links" in compact:
            next_id = self._store["num_link_next_id"]
            self._store["num_link_next_id"] += 1
            row = {
                "id": next_id,
                "grammar_id": params[0],
                "lexicon_id": params[1],
                "num_path": params[2],
                "memo": params[3],
                "slot_no": params[4],
                "idx_value": params[5],
                "comment": params[6],
                "created_at": now,
                "updated_at": now,
            }
            self._store["num_links"][next_id] = row
            self._rows = [
                (
                    row["id"],
                    row["grammar_id"],
                    row["lexicon_id"],
                    row["num_path"],
                    row["memo"],
                    row["slot_no"],
                    row["idx_value"],
                    row["comment"],
                    row["created_at"],
                    row["updated_at"],
                )
            ]
            return

        if "SELECT id, grammar_id, lexicon_id, num_path, memo, slot_no, idx_value, comment, created_at, updated_at FROM lexicon_item_num_links" in compact:
            grammar_id, lexicon_id = params
            rows = [
                row
                for row in self._store["num_links"].values()
                if row["grammar_id"] == grammar_id and row["lexicon_id"] == lexicon_id
            ]
            rows.sort(key=lambda row: row["id"])
            self._rows = [
                (
                    row["id"],
                    row["grammar_id"],
                    row["lexicon_id"],
                    row["num_path"],
                    row["memo"],
                    row["slot_no"],
                    row["idx_value"],
                    row["comment"],
                    row["created_at"],
                    row["updated_at"],
                )
                for row in rows
            ]
            return

        if "UPDATE lexicon_item_num_links" in compact and "RETURNING" in compact:
            link_id, grammar_id, lexicon_id = params[4], params[5], params[6]
            row = self._store["num_links"].get(link_id)
            if row is None or row["grammar_id"] != grammar_id or row["lexicon_id"] != lexicon_id:
                self._rows = []
                return
            row["memo"] = params[0]
            row["slot_no"] = params[1]
            row["idx_value"] = params[2]
            row["comment"] = params[3]
            row["updated_at"] = now
            self._rows = [
                (
                    row["id"],
                    row["grammar_id"],
                    row["lexicon_id"],
                    row["num_path"],
                    row["memo"],
                    row["slot_no"],
                    row["idx_value"],
                    row["comment"],
                    row["created_at"],
                    row["updated_at"],
                )
            ]
            return

        if "DELETE FROM lexicon_item_num_links WHERE id = %s AND grammar_id = %s AND lexicon_id = %s" in compact:
            link_id, grammar_id, lexicon_id = params
            row = self._store["num_links"].get(link_id)
            if row and row["grammar_id"] == grammar_id and row["lexicon_id"] == lexicon_id:
                del self._store["num_links"][link_id]
                self.rowcount = 1
            else:
                self.rowcount = 0
            return

        if "SELECT current_markdown, updated_at FROM lexicon_item_notes" in compact:
            key = (params[0], params[1])
            note = self._store["notes"].get(key)
            self._rows = [] if note is None else [(note["markdown"], note["updated_at"])]
            return

        if "SELECT COALESCE(MAX(revision_no), 0) FROM lexicon_item_note_revisions" in compact:
            grammar_id, lexicon_id = params
            numbers = [
                row["revision_no"]
                for row in self._store["note_revisions"].values()
                if row["grammar_id"] == grammar_id and row["lexicon_id"] == lexicon_id
            ]
            self._rows = [(max(numbers) if numbers else 0,)]
            return

        if "INSERT INTO lexicon_item_note_revisions" in compact:
            next_id = self._store["note_revision_next_id"]
            self._store["note_revision_next_id"] += 1
            row = {
                "id": next_id,
                "grammar_id": params[0],
                "lexicon_id": params[1],
                "revision_no": params[2],
                "markdown": params[3],
                "author": params[4],
                "created_at": now,
                "change_summary": params[5],
            }
            self._store["note_revisions"][next_id] = row
            return

        if "INSERT INTO lexicon_item_notes" in compact and "RETURNING updated_at" in compact:
            key = (params[0], params[1])
            self._store["notes"][key] = {"markdown": params[2], "updated_at": now}
            self._rows = [(now,)]
            return

        if "SELECT id, revision_no, author, created_at, change_summary FROM lexicon_item_note_revisions" in compact:
            grammar_id, lexicon_id = params
            rows = [
                row
                for row in self._store["note_revisions"].values()
                if row["grammar_id"] == grammar_id and row["lexicon_id"] == lexicon_id
            ]
            rows.sort(key=lambda row: row["revision_no"], reverse=True)
            self._rows = [
                (row["id"], row["revision_no"], row["author"], row["created_at"], row["change_summary"])
                for row in rows
            ]
            return

        if "SELECT id, revision_no, markdown, author, created_at, change_summary FROM lexicon_item_note_revisions" in compact:
            revision_id, grammar_id, lexicon_id = params
            row = self._store["note_revisions"].get(revision_id)
            if row and row["grammar_id"] == grammar_id and row["lexicon_id"] == lexicon_id:
                self._rows = [
                    (
                        row["id"],
                        row["revision_no"],
                        row["markdown"],
                        row["author"],
                        row["created_at"],
                        row["change_summary"],
                    )
                ]
            else:
                self._rows = []
            return

        raise AssertionError(f"Unsupported SQL in fake cursor: {compact}")

    def fetchone(self) -> Any:
        if not self._rows:
            return None
        return self._rows[0]

    def fetchall(self) -> list[Any]:
        return list(self._rows)


class _FakeConn:
    def __init__(self, store: dict[str, Any]) -> None:
        self._store = store

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self._store)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


def _fake_meta_conn_factory(store: dict[str, Any]):
    @contextmanager
    def _fake_meta_conn():
        conn = _FakeConn(store)
        lexicon_ext._ensure_meta_schema(conn)
        yield conn

    return _fake_meta_conn


def test_lexicon_ext_items_crud(monkeypatch) -> None:
    client = TestClient(app)
    with TemporaryDirectory() as tmpdir:
        legacy_root = Path(tmpdir)
        _seed_lexicon_csv(legacy_root / "lexicon-all.csv")
        monkeypatch.setattr(lexicon_ext, "_default_legacy_root", lambda: legacy_root)

        list_response = client.get("/v1/lexicon/imi03/items")
        assert list_response.status_code == 200
        assert list_response.json()["total_count"] == 1

        create_response = client.post(
            "/v1/lexicon/imi03/items",
            json={
                "lexicon_id": 2,
                "entry": "メアリ",
                "phono": "メアリ",
                "category": "N",
                "predicates": [],
                "sync_features": [],
                "idslot": "x2-1",
                "semantics": ["Name|=|メアリ"],
                "note": "",
            },
        )
        assert create_response.status_code == 200
        assert create_response.json()["item"]["lexicon_id"] == 2

        update_response = client.put(
            "/v1/lexicon/imi03/items/2",
            json={
                "entry": "メアリ",
                "phono": "メアリ",
                "category": "iA",
                "predicates": [],
                "sync_features": ["0,17,N,,,right,nonhead"],
                "idslot": "x2-1",
                "semantics": ["Name|=|メアリ"],
                "note": "updated",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["item"]["category"] == "iA"

        get_response = client.get("/v1/lexicon/imi03/items/2")
        assert get_response.status_code == 200
        assert "updated" in get_response.json()["item"]["note"]

        delete_response = client.delete("/v1/lexicon/imi03/items/2")
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] is True


def test_lexicon_ext_metadata_endpoints(monkeypatch) -> None:
    client = TestClient(app)
    store = {
        "value_next_id": 1,
        "values": {},
        "num_link_next_id": 1,
        "num_links": {},
        "notes": {},
        "note_revision_next_id": 1,
        "note_revisions": {},
    }
    monkeypatch.setattr(lexicon_ext, "_meta_conn", _fake_meta_conn_factory(store))
    monkeypatch.setattr(lexicon_ext, "_count_value_usages", lambda **_: {"imi01": 2})
    monkeypatch.setattr(lexicon_ext, "_replace_value_in_entries", lambda **_: 3)

    create_dict = client.post(
        "/v1/lexicon/value-dictionary",
        json={"kind": "category", "display_value": "N", "metadata_json": {"memo": "noun"}},
    )
    assert create_dict.status_code == 200
    value_id = create_dict.json()["id"]

    list_dict = client.get("/v1/lexicon/value-dictionary?kind=category")
    assert list_dict.status_code == 200
    assert list_dict.json()["items"][0]["display_value"] == "N"

    usage = client.get(f"/v1/lexicon/value-dictionary/{value_id}/usages")
    assert usage.status_code == 200
    assert usage.json()["total_usages"] == 2

    create_dict2 = client.post(
        "/v1/lexicon/value-dictionary",
        json={"kind": "category", "display_value": "iA", "metadata_json": {}},
    )
    replacement_id = create_dict2.json()["id"]
    replace = client.post(
        f"/v1/lexicon/value-dictionary/{value_id}/replace",
        json={"replacement_value_id": replacement_id},
    )
    assert replace.status_code == 200
    assert replace.json()["changed_count"] == 3

    num_link_create = client.post(
        "/v1/lexicon/imi01/items/60/num-links",
        json={"num_path": "imi01/set-numeration/04.num", "memo": "test", "slot_no": 1, "idx_value": "x1-1"},
    )
    assert num_link_create.status_code == 200
    link_id = num_link_create.json()["id"]

    num_link_list = client.get("/v1/lexicon/imi01/items/60/num-links")
    assert num_link_list.status_code == 200
    assert len(num_link_list.json()["items"]) == 1

    note_put = client.put(
        "/v1/lexicon/imi01/items/60/notes",
        json={"markdown": "# memo", "author": "tester", "change_summary": "init"},
    )
    assert note_put.status_code == 200
    assert note_put.json()["markdown"] == "# memo"

    revisions = client.get("/v1/lexicon/imi01/items/60/notes/revisions")
    assert revisions.status_code == 200
    revision_id = revisions.json()["items"][0]["id"]

    revision = client.get(f"/v1/lexicon/imi01/items/60/notes/revisions/{revision_id}")
    assert revision.status_code == 200
    assert revision.json()["author"] == "tester"

    restore = client.post(f"/v1/lexicon/imi01/items/60/notes/revisions/{revision_id}/restore")
    assert restore.status_code == 200
    assert restore.json()["markdown"] == "# memo"

    delete_link = client.delete(f"/v1/lexicon/imi01/items/60/num-links/{link_id}")
    assert delete_link.status_code == 200
    assert delete_link.json()["deleted"] is True


def test_lexicon_ext_versions_fallback(monkeypatch) -> None:
    client = TestClient(app)
    with TemporaryDirectory() as tmpdir:
        legacy_root = Path(tmpdir)
        csv_path = legacy_root / "lexicon-all.csv"
        _seed_lexicon_csv(csv_path)
        backup = legacy_root / "lexicon-all.csv.bak.001"
        backup.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
        monkeypatch.setattr(lexicon_ext, "_default_legacy_root", lambda: legacy_root)

        versions = client.get("/v1/lexicon/imi03/versions?limit=10&offset=0")
        assert versions.status_code == 200
        assert versions.json()["items"]

        diff = client.get("/v1/lexicon/imi03/versions/not-found/diff")
        assert diff.status_code == 404
