import csv

import pytest

from rover.evidence import (
    profile_image_catalog,
    profile_navigation_telemetry,
    profile_weather_telemetry,
)


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def test_image_catalog_reports_completeness_and_camera_mix(tmp_path):
    path = tmp_path / "images.csv"
    write_rows(
        path,
        [
            {
                "id": "1",
                "sol": "1000",
                "camera_name": "MAST",
                "earth_date": "2015-05-30",
                "rover_name": "Curiosity",
                "rover_status": "active",
            },
            {
                "id": "2",
                "sol": "1000",
                "camera_name": "NAVCAM",
                "earth_date": "2015-05-30",
                "rover_name": "Curiosity",
                "rover_status": "active",
            },
        ],
    )
    profile = profile_image_catalog(path)
    assert profile.rows == 2
    assert profile.key_metadata_coverage_pct == 100.0
    assert profile.cameras == {"MAST": 1, "NAVCAM": 1}


def test_navigation_profile_detects_stationary_window(tmp_path):
    path = tmp_path / "navigation.csv"
    row = {
        "SCLK": "1",
        "LMST": "00:00",
        "LTST": "00:00",
        "SOLAR_LONGITUDE_ANGLE": "7.6",
        "SOLAR_ZENITHAL_ANGLE": "147.3",
        "ROVER_POSITION_X": "7.4",
        "ROVER_POSITION_Y": "-70.4",
        "ROVER_POSITION_Z": "1.37",
        "ROVER_VELOCITY": "0",
        "ROVER_PITCH": "0.08",
        "ROVER_YAW": "175.2",
        "ROVER_ROLL": "0.17",
    }
    write_rows(path, [row, {**row, "SCLK": "2"}])
    profile = profile_navigation_telemetry(path)
    assert profile.core_fields_coverage_pct == 100.0
    assert profile.stationary_observations_pct == 100.0
    assert profile.unique_positions == 1


def test_weather_profile_exposes_missing_sensor_channels(tmp_path):
    path = tmp_path / "weather.csv"
    write_rows(
        path,
        [
            {
                "HUMIDITY_LOCAL_TEMP": "205.5",
                "LOCAL_RELATIVE_HUMIDITY": "",
                "VOLUME_MIXING_RATIO": "",
            }
        ],
    )
    profile = profile_weather_telemetry(path)
    assert profile.local_temperature_kelvin.coverage_pct == 100.0
    assert profile.relative_humidity.coverage_pct == 0.0
    assert profile.volume_mixing_ratio.coverage_pct == 0.0


def test_missing_required_columns_fail_fast(tmp_path):
    path = tmp_path / "broken.csv"
    write_rows(path, [{"id": "1"}])
    with pytest.raises(ValueError, match="camera_name"):
        profile_image_catalog(path)
