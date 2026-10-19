"""Reproducible profiling for the Mars imagery and MEDA datasets in the repository."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path


def _percentage(part: int, total: int) -> float:
    return round((part / total) * 100, 2) if total else 0.0


def _require_columns(
    fieldnames: Iterable[str] | None, required: set[str], dataset_name: str
) -> None:
    available = set(fieldnames or ())
    missing = sorted(required - available)
    if missing:
        raise ValueError(f"{dataset_name} is missing required columns: {', '.join(missing)}")


def _number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


@dataclass
class RunningNumbers:
    count: int = 0
    total: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    def add(self, value: float | None) -> None:
        if value is None:
            return
        self.count += 1
        self.total += value
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)

    def summary(self, rows: int) -> NumericProfile:
        return NumericProfile(
            values=self.count,
            coverage_pct=_percentage(self.count, rows),
            minimum=self.minimum,
            maximum=self.maximum,
            mean=round(self.total / self.count, 4) if self.count else None,
        )


@dataclass(frozen=True)
class NumericProfile:
    values: int
    coverage_pct: float
    minimum: float | None
    maximum: float | None
    mean: float | None


@dataclass(frozen=True)
class ImageCatalogProfile:
    rows: int
    key_metadata_complete_rows: int
    key_metadata_coverage_pct: float
    cameras: dict[str, int]
    unique_sols: int
    sol_range: tuple[int, int] | None
    earth_date_range: tuple[str, str] | None


@dataclass(frozen=True)
class NavigationTelemetryProfile:
    rows: int
    core_fields_complete_rows: int
    core_fields_coverage_pct: float
    unique_positions: int
    stationary_observations_pct: float
    pitch_degrees: NumericProfile
    roll_degrees: NumericProfile


@dataclass(frozen=True)
class WeatherTelemetryProfile:
    rows: int
    local_temperature_kelvin: NumericProfile
    relative_humidity: NumericProfile
    volume_mixing_ratio: NumericProfile


@dataclass(frozen=True)
class EvidenceReport:
    total_rows_profiled: int
    parsed_rows_pct: float
    image_catalog: ImageCatalogProfile
    navigation_telemetry: NavigationTelemetryProfile
    weather_telemetry: WeatherTelemetryProfile
    interpretation: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


IMAGE_KEYS = {"id", "sol", "camera_name", "earth_date", "rover_name", "rover_status"}
NAVIGATION_KEYS = {
    "SCLK",
    "LMST",
    "LTST",
    "SOLAR_LONGITUDE_ANGLE",
    "SOLAR_ZENITHAL_ANGLE",
    "ROVER_POSITION_X",
    "ROVER_POSITION_Y",
    "ROVER_POSITION_Z",
    "ROVER_VELOCITY",
    "ROVER_PITCH",
    "ROVER_YAW",
    "ROVER_ROLL",
}
WEATHER_KEYS = {
    "HUMIDITY_LOCAL_TEMP",
    "LOCAL_RELATIVE_HUMIDITY",
    "VOLUME_MIXING_RATIO",
}


def profile_image_catalog(path: Path) -> ImageCatalogProfile:
    rows = complete = 0
    cameras: Counter[str] = Counter()
    sols: set[int] = set()
    dates: set[str] = set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, IMAGE_KEYS, "image catalog")
        for row in reader:
            rows += 1
            complete += int(all((row.get(key) or "").strip() for key in IMAGE_KEYS))
            cameras[(row.get("camera_name") or "unknown").strip() or "unknown"] += 1
            try:
                sols.add(int(row["sol"]))
            except (KeyError, TypeError, ValueError):
                pass
            if row.get("earth_date"):
                dates.add(row["earth_date"].strip())
    return ImageCatalogProfile(
        rows=rows,
        key_metadata_complete_rows=complete,
        key_metadata_coverage_pct=_percentage(complete, rows),
        cameras=dict(sorted(cameras.items())),
        unique_sols=len(sols),
        sol_range=(min(sols), max(sols)) if sols else None,
        earth_date_range=(min(dates), max(dates)) if dates else None,
    )


def profile_navigation_telemetry(path: Path) -> NavigationTelemetryProfile:
    rows = complete = stationary = 0
    positions: set[tuple[float, float, float]] = set()
    pitch = RunningNumbers()
    roll = RunningNumbers()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, NAVIGATION_KEYS, "navigation telemetry")
        for row in reader:
            rows += 1
            complete += int(all((row.get(key) or "").strip() for key in NAVIGATION_KEYS))
            velocity = _number(row.get("ROVER_VELOCITY"))
            stationary += int(velocity == 0.0)
            x = _number(row.get("ROVER_POSITION_X"))
            y = _number(row.get("ROVER_POSITION_Y"))
            z = _number(row.get("ROVER_POSITION_Z"))
            if x is not None and y is not None and z is not None:
                positions.add((x, y, z))
            pitch.add(_number(row.get("ROVER_PITCH")))
            roll.add(_number(row.get("ROVER_ROLL")))
    return NavigationTelemetryProfile(
        rows=rows,
        core_fields_complete_rows=complete,
        core_fields_coverage_pct=_percentage(complete, rows),
        unique_positions=len(positions),
        stationary_observations_pct=_percentage(stationary, rows),
        pitch_degrees=pitch.summary(rows),
        roll_degrees=roll.summary(rows),
    )


def profile_weather_telemetry(path: Path) -> WeatherTelemetryProfile:
    rows = 0
    temperature = RunningNumbers()
    humidity = RunningNumbers()
    mixing_ratio = RunningNumbers()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, WEATHER_KEYS, "weather telemetry")
        for row in reader:
            rows += 1
            temperature.add(_number(row.get("HUMIDITY_LOCAL_TEMP")))
            humidity.add(_number(row.get("LOCAL_RELATIVE_HUMIDITY")))
            mixing_ratio.add(_number(row.get("VOLUME_MIXING_RATIO")))
    return WeatherTelemetryProfile(
        rows=rows,
        local_temperature_kelvin=temperature.summary(rows),
        relative_humidity=humidity.summary(rows),
        volume_mixing_ratio=mixing_ratio.summary(rows),
    )


def profile_repository(root: Path) -> EvidenceReport:
    image = profile_image_catalog(root / "mars_rover_dataset.csv")
    navigation = profile_navigation_telemetry(root / "meda dataset.csv")
    weather = profile_weather_telemetry(
        root / "sol_0017_WE__0017___________DER_RHS_________________P03.CSV"
    )
    total = image.rows + navigation.rows + weather.rows
    interpretation = (
        "Image records are suitable for camera-distribution and metadata analysis.",
        "The MEDA extract is a stationary observation window, not a driving trajectory.",
        "Local temperature is available, while humidity and mixing ratio require another source.",
        "Coverage percentages describe data completeness, not flight or model accuracy.",
    )
    return EvidenceReport(
        total_rows_profiled=total,
        parsed_rows_pct=100.0 if total else 0.0,
        image_catalog=image,
        navigation_telemetry=navigation,
        weather_telemetry=weather,
        interpretation=interpretation,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile the committed Mars datasets")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(profile_repository(args.root).to_dict(), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
