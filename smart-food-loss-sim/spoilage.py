"""Storage physics used by the simulator and to label training data.

Rule of thumb from grain storage literature:
  * safe storage time roughly halves for every 1% moisture above the crop's safe level
  * and for every ~6 degC above 22 degC
  * and mould risk climbs quickly once air humidity passes ~70%
This is NOT the AI model. It plays the role of "reality" in the simulation, so the
AI model has something to learn from.
"""
import math
from config import CROPS


def halvings(crop: str, T: float, RH: float, m: float) -> dict:
    """How many times each condition halves the safe storage time."""
    return {
        "moisture": m - CROPS[crop]["m_safe"],
        "temperature": (T - 22.0) / 6.0,
        "humidity": max(0.0, (RH - 70.0) / 7.5),
    }


def safe_days(crop: str, T: float, RH: float, m: float) -> float:
    h = halvings(crop, T, RH, m)
    days = CROPS[crop]["base_days"] * 0.5 ** (h["moisture"] + h["temperature"] + h["humidity"])
    return max(0.5, min(365.0, days))


def risk_level(days: float) -> int:
    """0 = Good, 1 = Watch, 2 = Act now."""
    if days <= 10:
        return 2
    if days <= 45:
        return 1
    return 0


def equilibrium_moisture(RH: float) -> float:
    """Approximate grain moisture that is in balance with the air humidity.
    Grain slowly absorbs water from humid air and dries in dry air."""
    rh = min(max(RH, 20.0), 98.0) / 100.0
    # Simple curve that gives ~13% at 65% RH and ~17% at 85% RH
    return 6.0 + 6.75 * (-math.log(1 - rh)) ** 0.75
