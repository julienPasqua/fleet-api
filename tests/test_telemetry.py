"""Tests du module de télémétrie.

Deux tests vous sont fournis en exemple : ils montrent le style attendu.
Tout le reste est à écrire — voir le TD 1.
"""

import pytest

from fleet_api.models import Position
from fleet_api.telemetry import (
    Reading,
    RobotState,
    average_speed_mps,
    battery_percentage,
    distance_m,
    estimate_runtime_minutes,
    fleet_summary,
    is_low_battery,
    median_voltage_mv,
    path_length_m,
    robot_state,
)

# ---------------------------------------------------------------------------
# Exemple 1 — un test simple, avec un cas nominal et les deux bornes.
# ---------------------------------------------------------------------------


def test_battery_percentage_bornes_et_cas_nominal():
    """La conversion est linéaire et bornée à [0, 100]."""
    assert battery_percentage(12_600) == 100.0
    assert battery_percentage(10_500) == 0.0
    assert battery_percentage(11_550) == 50.0
    # Hors bornes : on sature, on ne dépasse pas.
    assert battery_percentage(13_000) == 100.0
    assert battery_percentage(9_000) == 0.0


# ---------------------------------------------------------------------------
# Exemple 2 — le même test écrit en paramétré, quand les cas se ressemblent.
# On teste aussi que l'erreur attendue est bien levée.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "attendu"),
    [
        (Position(0, 0), Position(3, 4), 5.0),  # triplet pythagoricien
        (Position(0, 0), Position(0, 0), 0.0),  # distance à soi-même
        (Position(1, 1), Position(-2, -3), 5.0),  # coordonnées négatives
        (Position(3, 4), Position(0, 0), 5.0),  # symétrie
    ],
)
def test_distance_m(a, b, attendu):
    """La distance est euclidienne, positive et symétrique."""
    assert distance_m(a, b) == pytest.approx(attendu)


def test_battery_percentage_rejette_des_bornes_incoherentes():
    """Une plage de tension invalide lève une ValueError."""
    with pytest.raises(ValueError, match="strictement supérieur"):
        battery_percentage(11_000, empty_mv=12_000, full_mv=11_000)


# ---------------------------------------------------------------------------
# À vous. Huit fonctions de fleet_api.telemetry n'ont aucun test :
#
#   is_low_battery, path_length_m, average_speed_mps, estimate_runtime_minutes,
#   median_voltage_mv, robot_state, detect_voltage_dropouts, fleet_summary
#
# Écrivez-les en vous appuyant sur les docstrings, qui font foi.
# Trois de ces fonctions ne respectent pas leur spécification.
# ---------------------------------------------------------------------------


def test_is_low_battery():

    assert is_low_battery(10.0) is True
    assert is_low_battery(20.0) is True
    assert is_low_battery(20.1) is False


def test_path_length_m():

    positions = [Position(0, 0), Position(3, 4), Position(6, 0)]
    assert path_length_m(positions) == pytest.approx(10.0)

    positions = [Position(1, 1)]
    assert path_length_m(positions) == pytest.approx(0.0)

    positions = [Position(1, 1), Position(4, 5)]
    assert path_length_m(positions) == pytest.approx(5.0)

    positions = [Position(2, 2), Position(2, 2), Position(2, 2)]
    assert path_length_m(positions) == pytest.approx(0.0)


def test_average_speed_mps():

    assert average_speed_mps(10.0, 5.0) == pytest.approx(2.0)
    assert average_speed_mps(10.0, 0.0) is None
    assert average_speed_mps(10.0, -5.0) is None


def test_estimate_runtime_minutes():

    assert estimate_runtime_minutes(50.0, 5.0) == pytest.approx(10.0)
    assert estimate_runtime_minutes(100.0, 10.0) == pytest.approx(10.0)
    assert estimate_runtime_minutes(0.0, 5.0) == pytest.approx(0.0)
    assert estimate_runtime_minutes(50.0, 0.0) is None
    assert estimate_runtime_minutes(50.0, -5.0) is None


def test_median_voltage_mv():
    readings = [
        Reading("R1", 1.0, 12_000, Position(0, 0)),
        Reading("R1", 2.0, 11_500, Position(0, 0)),
        Reading("R1", 3.0, 12_500, Position(0, 0)),
        Reading("R1", 4.0, 11_000, Position(0, 0)),
        Reading("R1", 5.0, 12_200, Position(0, 0)),
    ]

    assert median_voltage_mv(readings) == pytest.approx(12_000)


def test_robot_state():
    reading = Reading(
        "R1",
        1000.0,
        12_600,
        Position(0, 0),
        False,
    )
    reading_low_battery = Reading(
        "R1",
        1000.0,
        10_500,
        Position(0, 0),
        False,
    )
    reading_charging = Reading(
        "R1",
        1000.0,
        12_600,
        Position(0, 0),
        True,
    )
    reading_offline = Reading(
        "R1",
        1000.0,
        12_600,
        Position(0, 0),
        False,
    )

    assert robot_state(reading, 1050.0) == RobotState.OPERATIONAL
    assert robot_state(reading_low_battery, 1050.0) == RobotState.LOW_BATTERY
    assert robot_state(reading_charging, 1050.0) == RobotState.CHARGING
    assert robot_state(reading_offline, 1121.0) == RobotState.OFFLINE


def test_fleet_summary():
    readings = [
        Reading("R1", 1000.0, 12_600, Position(0, 0), False),
        Reading("R2", 1005.0, 11_500, Position(1, 1), False),
        Reading("R3", 1010.0, 12_200, Position(2, 2), True),
    ]

    result = fleet_summary(readings)

    assert result["robot_count"] == 3
    assert result["average_battery_pct"] == pytest.approx(
        round(
            sum(battery_percentage(r.voltage_mv) for r in readings) / 3,
            1,
        )
    )
