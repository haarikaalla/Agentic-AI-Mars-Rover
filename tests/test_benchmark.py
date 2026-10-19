import pytest

from rover.benchmark import run_energy_benchmark
from rover.world import GridWorld


def test_energy_sweep_reports_safety_and_science_rates():
    world = GridWorld.from_text("R..2..S\n.##2...\n...3.#.\n.###...\nS..1..B")
    result = run_energy_benchmark(world, (15, 20, 25, 30, 40, 50), reserve=5)
    assert result.safe_return_rate_pct == 100.0
    assert result.reserve_compliance_rate_pct == 100.0
    assert result.full_science_completion_rate_pct == pytest.approx(66.67)
    assert len(result.scenarios) == 6


def test_benchmark_rejects_invalid_budgets():
    world = GridWorld.from_text("R.B")
    with pytest.raises(ValueError, match="positive"):
        run_energy_benchmark(world, (0,), reserve=1)
