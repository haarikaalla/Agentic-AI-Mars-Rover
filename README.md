# Ares Rover — autonomous mission planning benchmark

This repository now contains a tested autonomy core rather than only a notebook.
The rover performs energy-aware A* planning, selects science targets, preserves a
configurable return-to-base reserve and emits a fully auditable mission route.

```bash
python -m pip install -e '.[dev]'
ares-rover examples/mission.map --energy 40 --reserve 5
pytest
```

The ASCII simulator makes every experiment deterministic and CI-friendly. Terrain
costs, hazards, unreachable objectives and low-energy abort behavior are covered by
tests. The original notebook and Mars datasets remain as research inputs; the next
step is an adapter for ROS 2/Gazebo and learned perception.

## Legacy research statement
This project presents an Agentic AI framework for an autonomous Mars Rover, designed to operate in unknown and dynamic extraterrestrial environments. The rover uses goal-driven, self-reasoning AI agents to perceive surroundings, plan actions, adapt to obstacles, and make decisions with minimal human intervention.

The work focuses on research-oriented agent architecture, combining perception, planning, memory, and execution into a unified autonomous system inspired by real planetary exploration missions.
