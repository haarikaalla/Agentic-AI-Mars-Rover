import pytest

from rover import AutonomousRover, GridWorld, Position
from rover.planner import NoSafePath, a_star


def test_energy_aware_planner_avoids_expensive_shortcut():
    world = GridWorld.from_text("R9B\n...")
    path = a_star(world, Position(0, 0), Position(0, 2))
    assert path == [Position(0, 0), Position(1, 0), Position(1, 1), Position(1, 2), Position(0, 2)]


def test_rover_collects_sample_and_returns_to_base():
    world = GridWorld.from_text("R.S\n.#.\n..B")
    report = AutonomousRover(world, energy_budget=20, reserve=2).run()
    assert report.success is True
    assert report.samples_collected == 1
    assert report.route[-1] == Position(2, 2)


def test_rover_aborts_science_but_returns_safely():
    world = GridWorld.from_text("R...B\n.###.\nS....")
    report = AutonomousRover(world, energy_budget=7, reserve=2).run()
    assert report.success is False
    assert report.samples_collected == 0
    assert report.route[-1] == Position(0, 4)


def test_unreachable_goal_is_reported():
    world = GridWorld.from_text("R#B\n###\nS..")
    with pytest.raises(NoSafePath):
        a_star(world, Position(0, 0), Position(0, 2))


def test_world_validation():
    with pytest.raises(ValueError):
        GridWorld.from_text("R..\n..")
