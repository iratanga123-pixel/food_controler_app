"""Turns the last 48 hours of sensor readings into the inputs (features) of the AI model.
Used both for training and for live prediction, so both see exactly the same inputs."""
import numpy as np
import pandas as pd

from config import CROPS

WINDOW = 48  # hours of history the model looks at
FEATURES = [
    "crop_maize", "crop_rice", "crop_sorghum", "crop_beans",
    "air_temp", "humidity", "grain_moisture", "grain_temp",
    "moisture_margin", "humidity_mean_24h", "humidity_max_24h",
    "moisture_slope_24h", "humidity_slope_24h", "grain_temp_slope_24h",
    "grain_minus_air_24h",
]


def _slope(values) -> float:
    """Change per hour, from a straight-line fit."""
    y = np.asarray(values, dtype=float)
    x = np.arange(len(y))
    return float(np.polyfit(x, y, 1)[0]) if len(y) > 2 else 0.0


def build_features(window: pd.DataFrame, crop: str) -> dict:
    """window: readings in time order with columns air_temp, humidity, grain_moisture, grain_temp."""
    w = window.tail(WINDOW)
    last24 = w.tail(24)
    now = w.tail(3).mean(numeric_only=True)   # average last 3 h to smooth sensor noise
    f = {f"crop_{c}": int(c == crop) for c in CROPS}
    f.update({
        "air_temp": now["air_temp"],
        "humidity": now["humidity"],
        "grain_moisture": now["grain_moisture"],
        "grain_temp": now["grain_temp"],
        "moisture_margin": now["grain_moisture"] - CROPS[crop]["m_safe"],
        "humidity_mean_24h": last24["humidity"].mean(),
        "humidity_max_24h": last24["humidity"].max(),
        "moisture_slope_24h": _slope(last24["grain_moisture"]),
        "humidity_slope_24h": _slope(last24["humidity"]),
        "grain_temp_slope_24h": _slope(last24["grain_temp"]),
        "grain_minus_air_24h": (last24["grain_temp"] - last24["air_temp"]).mean(),
    })
    return f
