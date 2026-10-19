"""Explainable perception fusion and risk memory for mission decisions."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "moderate", "high"]
MissionAction = Literal["proceed", "proceed_cautiously", "hold_and_replan"]


@dataclass(frozen=True)
class PerceptionFrame:
    camera_name: str
    obstacle_probability: float
    temperature_kelvin: float | None
    pitch_degrees: float | None
    roll_degrees: float | None

    def __post_init__(self) -> None:
        if not self.camera_name.strip():
            raise ValueError("camera_name cannot be empty")
        if not 0.0 <= self.obstacle_probability <= 1.0:
            raise ValueError("obstacle_probability must be between 0 and 1")


@dataclass(frozen=True)
class RiskPolicy:
    minimum_temperature_kelvin: float = 180.0
    maximum_temperature_kelvin: float = 280.0
    maximum_tilt_degrees: float = 15.0
    caution_threshold: float = 0.35
    hold_threshold: float = 0.65

    def __post_init__(self) -> None:
        if self.minimum_temperature_kelvin >= self.maximum_temperature_kelvin:
            raise ValueError("minimum temperature must be below maximum temperature")
        if self.maximum_tilt_degrees <= 0:
            raise ValueError("maximum tilt must be positive")
        if not 0 <= self.caution_threshold < self.hold_threshold <= 1:
            raise ValueError("risk thresholds must satisfy 0 <= caution < hold <= 1")


@dataclass(frozen=True)
class RiskAssessment:
    score: float
    level: RiskLevel
    action: MissionAction
    reasons: tuple[str, ...]
    frame: PerceptionFrame


class DataFusionAgent:
    """Fuse camera confidence and MEDA context into an explainable action gate."""

    def __init__(self, policy: RiskPolicy | None = None, memory_size: int = 20):
        if memory_size <= 0:
            raise ValueError("memory_size must be positive")
        self.policy = policy or RiskPolicy()
        self._memory: deque[RiskAssessment] = deque(maxlen=memory_size)

    @property
    def memory(self) -> tuple[RiskAssessment, ...]:
        return tuple(self._memory)

    def assess(self, frame: PerceptionFrame) -> RiskAssessment:
        reasons: list[str] = []
        score = frame.obstacle_probability * 0.70
        if frame.obstacle_probability >= 0.5:
            reasons.append("camera model reports elevated obstacle probability")

        if frame.temperature_kelvin is None:
            score += 0.1
            reasons.append("temperature channel is unavailable")
        elif not (
            self.policy.minimum_temperature_kelvin
            <= frame.temperature_kelvin
            <= self.policy.maximum_temperature_kelvin
        ):
            score += 0.2
            reasons.append("temperature is outside the configured operating envelope")

        if frame.pitch_degrees is None or frame.roll_degrees is None:
            score += 0.1
            reasons.append("tilt telemetry is incomplete")
        else:
            tilt = math.hypot(frame.pitch_degrees, frame.roll_degrees)
            score += min(tilt / self.policy.maximum_tilt_degrees, 1.0) * 0.25
            if tilt >= self.policy.maximum_tilt_degrees:
                reasons.append("combined pitch and roll exceed the configured tilt limit")

        score = round(min(score, 1.0), 4)
        if score >= self.policy.hold_threshold:
            level: RiskLevel = "high"
            action: MissionAction = "hold_and_replan"
        elif score >= self.policy.caution_threshold:
            level = "moderate"
            action = "proceed_cautiously"
        else:
            level = "low"
            action = "proceed"
        if not reasons:
            reasons.append("all supplied perception signals are inside the configured envelope")

        assessment = RiskAssessment(score, level, action, tuple(reasons), frame)
        self._memory.append(assessment)
        return assessment
