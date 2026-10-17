import argparse
import json
from pathlib import Path

from .agent import AutonomousRover
from .world import GridWorld


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an Ares rover mission")
    parser.add_argument("map", type=Path, help="ASCII mission map")
    parser.add_argument("--energy", type=int, default=100)
    parser.add_argument("--reserve", type=int, default=5)
    args = parser.parse_args()

    report = AutonomousRover(
        GridWorld.from_text(args.map.read_text()),
        energy_budget=args.energy,
        reserve=args.reserve,
    ).run()
    print(json.dumps({
        "success": report.success,
        "reason": report.reason,
        "energy_used": report.energy_used,
        "steps": report.steps,
        "samples_collected": report.samples_collected,
        "route": [[point.row, point.col] for point in report.route],
    }, indent=2))
