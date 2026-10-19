from rover.controller import AutonomousMissionController
from rover.intelligence import DataFusionAgent, PerceptionFrame
from rover.world import GridWorld


def test_low_risk_perception_allows_mission_execution():
    controller = AutonomousMissionController()
    frame = PerceptionFrame("NAVCAM", 0.05, 210.7, 0.10, 0.17)
    result = controller.run(GridWorld.from_text("R.S\n...\n..B"), frame, energy_budget=20)
    assert result.executed is True
    assert result.risk.action == "proceed"
    assert result.mission is not None and result.mission.success is True


def test_high_obstacle_risk_holds_before_route_execution():
    controller = AutonomousMissionController()
    frame = PerceptionFrame("FHAZ", 0.95, 210.7, 0.10, 0.17)
    result = controller.run(GridWorld.from_text("R.S\n...\n..B"), frame, energy_budget=20)
    assert result.executed is False
    assert result.risk.action == "hold_and_replan"
    assert result.mission is None


def test_agent_memory_is_bounded_and_auditable():
    agent = DataFusionAgent(memory_size=2)
    for probability in (0.1, 0.2, 0.3):
        agent.assess(PerceptionFrame("MAST", probability, 210.0, 0.1, 0.2))
    assert len(agent.memory) == 2
    assert agent.memory[-1].frame.obstacle_probability == 0.3


def test_missing_telemetry_increases_uncertainty():
    agent = DataFusionAgent()
    complete = agent.assess(PerceptionFrame("NAVCAM", 0.2, 210.0, 0.1, 0.2))
    incomplete = agent.assess(PerceptionFrame("NAVCAM", 0.2, None, None, None))
    assert incomplete.score > complete.score
    assert "temperature channel is unavailable" in incomplete.reasons
