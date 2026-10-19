"""Mission orchestration that gates route execution with fused risk evidence."""

from __future__ import annotations

from dataclasses import dataclass

from .agent import AutonomousRover, MissionReport
from .intelligence import DataFusionAgent, PerceptionFrame, RiskAssessment
from .world import GridWorld


@dataclass(frozen=True)
class IntegratedMissionReport:
    risk: RiskAssessment
    mission: MissionReport | None

    @property
    def executed(self) -> bool:
        return self.mission is not None


class AutonomousMissionController:
    """Apply a perception safety gate before deterministic route execution."""

    def __init__(self, intelligence: DataFusionAgent | None = None):
        self.intelligence = intelligence or DataFusionAgent()

    def run(
        self,
        world: GridWorld,
        frame: PerceptionFrame,
        energy_budget: int = 100,
        reserve: int = 5,
    ) -> IntegratedMissionReport:
        risk = self.intelligence.assess(frame)
        if risk.action == "hold_and_replan":
            return IntegratedMissionReport(risk=risk, mission=None)
        mission = AutonomousRover(world, energy_budget=energy_budget, reserve=reserve).run()
        return IntegratedMissionReport(risk=risk, mission=mission)
