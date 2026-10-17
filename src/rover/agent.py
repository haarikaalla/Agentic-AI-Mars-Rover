from __future__ import annotations

from dataclasses import dataclass, field

from .planner import NoSafePath, a_star
from .world import GridWorld, Position


@dataclass
class MissionReport:
    success: bool
    reason: str
    energy_used: int
    steps: int
    samples_collected: int
    route: list[Position] = field(default_factory=list)


class AutonomousRover:
    """Goal-driven rover with an explicit safety reserve and auditable route."""

    def __init__(self, world: GridWorld, energy_budget: int = 100, reserve: int = 5):
        starts = world.find("R")
        bases = world.find("B")
        if len(starts) != 1 or len(bases) != 1:
            raise ValueError("World must contain exactly one rover and one base")
        self.world = world
        self.start = starts[0]
        self.base = bases[0]
        self.energy_budget = energy_budget
        self.reserve = reserve

    def _path_cost(self, path: list[Position]) -> int:
        return sum(self.world.energy_cost(position) for position in path[1:])

    def run(self) -> MissionReport:
        targets = set(self.world.find("S"))
        position = self.start
        energy = self.energy_budget
        route = [position]
        samples = 0

        try:
            while targets:
                candidates = []
                for target in targets:
                    outward = a_star(self.world, position, target)
                    home = a_star(self.world, target, self.base)
                    cost = self._path_cost(outward) + self._path_cost(home)
                    candidates.append((cost, target, outward))
                _, target, path = min(candidates, key=lambda item: (item[0], item[1]))
                return_path = a_star(self.world, target, self.base)
                required = self._path_cost(path) + self._path_cost(return_path) + self.reserve
                if required > energy:
                    break
                for step in path[1:]:
                    energy -= self.world.energy_cost(step)
                    position = step
                    route.append(step)
                targets.remove(target)
                samples += 1

            home = a_star(self.world, position, self.base)
            home_cost = self._path_cost(home)
            if home_cost + self.reserve > energy:
                return MissionReport(False, "energy reserve would be violated", self.energy_budget - energy, len(route) - 1, samples, route)
            for step in home[1:]:
                energy -= self.world.energy_cost(step)
                route.append(step)
            success = not targets
            reason = "all science targets collected and rover returned to base" if success else "returned safely before energy reserve was violated"
            return MissionReport(success, reason, self.energy_budget - energy, len(route) - 1, samples, route)
        except NoSafePath as exc:
            return MissionReport(False, str(exc), self.energy_budget - energy, len(route) - 1, samples, route)
