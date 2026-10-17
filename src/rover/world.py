from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Position:
    row: int
    col: int

    def manhattan(self, other: Position) -> int:
        return abs(self.row - other.row) + abs(self.col - other.col)


class GridWorld:
    """Deterministic terrain model used for repeatable autonomy experiments.

    Symbols: `.` traversable, `R` start, `S` science target, `B` base,
    `#` impassable terrain and digits 1–9 terrain energy cost.
    """

    def __init__(self, rows: tuple[str, ...]):
        if not rows or len({len(row) for row in rows}) != 1:
            raise ValueError("World must be a non-empty rectangular grid")
        allowed = set(".RSB#123456789")
        if any(set(row) - allowed for row in rows):
            raise ValueError("World contains an unsupported terrain symbol")
        self.rows = rows

    @classmethod
    def from_text(cls, text: str) -> GridWorld:
        return cls(tuple(line.strip() for line in text.splitlines() if line.strip()))

    def find(self, symbol: str) -> list[Position]:
        return [
            Position(row, col)
            for row, line in enumerate(self.rows)
            for col, value in enumerate(line)
            if value == symbol
        ]

    def symbol(self, position: Position) -> str:
        return self.rows[position.row][position.col]

    def traversable(self, position: Position) -> bool:
        return (
            0 <= position.row < len(self.rows)
            and 0 <= position.col < len(self.rows[0])
            and self.symbol(position) != "#"
        )

    def energy_cost(self, position: Position) -> int:
        value = self.symbol(position)
        return int(value) if value.isdigit() else 1

    def neighbors(self, position: Position) -> list[Position]:
        candidates = (
            Position(position.row - 1, position.col),
            Position(position.row + 1, position.col),
            Position(position.row, position.col - 1),
            Position(position.row, position.col + 1),
        )
        return [candidate for candidate in candidates if self.traversable(candidate)]
