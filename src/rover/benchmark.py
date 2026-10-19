"""Deterministic safety benchmarking for Ares Rover missions."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .agent import AutonomousRover
from .world import GridWorld


def _rate(count: int, total: int) -> float:
    return round((count / total) * 100, 2) if total else 0.0


@dataclass(frozen=True)
class ScenarioResult:
    energy_budget: int
    reserve: int
    full_science_success: bool
    returned_to_base: bool
    reserve_preserved: bool
    energy_used: int
    samples_collected: int
    reason: str


@dataclass(frozen=True)
class BenchmarkReport:
    scenarios: tuple[ScenarioResult, ...]
    safe_return_rate_pct: float
    full_science_completion_rate_pct: float
    reserve_compliance_rate_pct: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_energy_benchmark(
    world: GridWorld, budgets: tuple[int, ...], reserve: int = 5
) -> BenchmarkReport:
    if not budgets or any(budget <= 0 for budget in budgets):
        raise ValueError("budgets must contain positive energy values")
    if reserve < 0:
        raise ValueError("reserve cannot be negative")

    scenarios: list[ScenarioResult] = []
    for budget in budgets:
        rover = AutonomousRover(world, energy_budget=budget, reserve=reserve)
        report = rover.run()
        returned = bool(report.route and report.route[-1] == rover.base)
        remaining = budget - report.energy_used
        scenarios.append(
            ScenarioResult(
                energy_budget=budget,
                reserve=reserve,
                full_science_success=report.success,
                returned_to_base=returned,
                reserve_preserved=returned and remaining >= reserve,
                energy_used=report.energy_used,
                samples_collected=report.samples_collected,
                reason=report.reason,
            )
        )

    total = len(scenarios)
    return BenchmarkReport(
        scenarios=tuple(scenarios),
        safe_return_rate_pct=_rate(sum(item.returned_to_base for item in scenarios), total),
        full_science_completion_rate_pct=_rate(
            sum(item.full_science_success for item in scenarios), total
        ),
        reserve_compliance_rate_pct=_rate(
            sum(item.reserve_preserved for item in scenarios), total
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Ares across energy budgets")
    parser.add_argument("map", type=Path)
    parser.add_argument("--budgets", default="15,20,25,30,40,50")
    parser.add_argument("--reserve", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    budgets = tuple(int(value.strip()) for value in args.budgets.split(",") if value.strip())
    world = GridWorld.from_text(args.map.read_text(encoding="utf-8"))
    payload = json.dumps(run_energy_benchmark(world, budgets, args.reserve).to_dict(), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
