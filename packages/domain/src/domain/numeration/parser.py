from __future__ import annotations

from dataclasses import dataclass

NUMERATION_SLOT_COUNT = 30


@dataclass(frozen=True)
class NumerationRows:
    memo: str
    lexicon_cells: list[str]
    plus_cells: list[str]
    idx_cells: list[str]

    def lexicon_slot(self, slot: int) -> str:
        return _cell(self.lexicon_cells, slot)

    def plus_slot(self, slot: int) -> str:
        return _cell(self.plus_cells, slot)

    def idx_slot(self, slot: int) -> str:
        return _cell(self.idx_cells, slot)


def _cell(cells: list[str], index: int) -> str:
    if index < len(cells):
        return cells[index].strip()
    return ""


def parse_numeration_text(numeration_text: str) -> NumerationRows:
    lines = numeration_text.splitlines()
    if len(lines) < 1:
        raise ValueError(
            f"Numeration text must contain at least 1 line. got={len(lines)}"
        )

    lexicon_cells = lines[0].split("\t")
    plus_cells = lines[1].split("\t") if len(lines) >= 2 else [""]
    idx_cells = lines[2].split("\t") if len(lines) >= 3 else [""]
    memo = lexicon_cells[0] if lexicon_cells else ""
    return NumerationRows(
        memo=memo,
        lexicon_cells=lexicon_cells,
        plus_cells=plus_cells,
        idx_cells=idx_cells,
    )
