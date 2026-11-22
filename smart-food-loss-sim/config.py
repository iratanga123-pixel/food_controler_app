"""Shared settings: crops, storage sites and file locations."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ---- Branding --------------------------------------------------------------
APP_NAME = "Hunika"
APP_TAGLINE = "Smart storage, zero loss."
LOGO_SVG = str(BASE_DIR / "assets" / "hunika-logo.svg")   # shown at the top of the sidebar
ICON_PNG = str(BASE_DIR / "assets" / "hunika-icon.png")   # browser tab icon
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "readings.db"          # sensor readings from the virtual nodes
MODEL_PATH = DATA_DIR / "spoilage_model.joblib"
DATASET_PATH = DATA_DIR / "training_data.csv"
SMS_OUTBOX = DATA_DIR / "sms_outbox.log"     # simulated SMS messages

# Safe storage moisture (%) and base safe storage days at ideal conditions.
CROPS = {
    "maize":   {"label": "Maize",      "rw": "ibigori",    "m_safe": 13.5, "base_days": 180},
    "rice":    {"label": "Paddy rice", "rw": "umuceri",    "m_safe": 14.0, "base_days": 180},
    "sorghum": {"label": "Sorghum",    "rw": "amasaka",    "m_safe": 13.0, "base_days": 200},
    "beans":   {"label": "Dry beans",  "rw": "ibishyimbo", "m_safe": 14.0, "base_days": 240},
}

# Virtual storage sites. Each one becomes a simulated sensor node.
# start_*: conditions when the simulation starts. scenario: what happens over time.
STORES = [
    {"id": "NYG01", "name": "Nyagatare Maize Store",  "district": "Nyagatare", "crop": "maize",
     "tonnes": 42, "phone": "+250780000001", "start_T": 25.0, "start_RH": 72, "start_m": 14.2,
     "scenario": "rainy_season"},
    {"id": "RWM01", "name": "Rwamagana Rice Store",   "district": "Rwamagana", "crop": "rice",
     "tonnes": 65, "phone": "+250780000002", "start_T": 26.5, "start_RH": 82, "start_m": 16.5,
     "scenario": "wet_harvest"},
    {"id": "BGS01", "name": "Bugesera Sorghum Store", "district": "Bugesera",  "crop": "sorghum",
     "tonnes": 18, "phone": "+250780000003", "start_T": 29.0, "start_RH": 58, "start_m": 13.0,
     "scenario": "hot_dry"},
    {"id": "MSZ01", "name": "Musanze Bean Store",     "district": "Musanze",   "crop": "beans",
     "tonnes": 24, "phone": "+250780000004", "start_T": 17.5, "start_RH": 62, "start_m": 12.6,
     "scenario": "normal"},
]

RISK_LEVELS = ["Good", "Watch", "Act now"]   # model output classes 0, 1, 2

# ---- Admin area ------------------------------------------------------------
ADMIN_DB = DATA_DIR / "admin.db"            # registered food and crop storage limits

# Starting storage limits per crop. The admin can change them on the Admin page.
# temp_* = grain temperature (°C), rh_* = air relative humidity (%), moisture_* = grain moisture (%).
# Below moisture_min the grain is over-dried: it cracks, breaks in handling and loses weight.
DEFAULT_LIMITS = {
    "maize":   {"temp_min": 10, "temp_max": 25, "rh_min": 40, "rh_max": 70, "moisture_min": 11.0, "moisture_max": 13.5},
    "rice":    {"temp_min": 10, "temp_max": 25, "rh_min": 40, "rh_max": 70, "moisture_min": 11.0, "moisture_max": 14.0},
    "sorghum": {"temp_min": 10, "temp_max": 27, "rh_min": 40, "rh_max": 70, "moisture_min": 10.0, "moisture_max": 13.0},
    "beans":   {"temp_min": 10, "temp_max": 25, "rh_min": 40, "rh_max": 65, "moisture_min": 10.0, "moisture_max": 14.0},
}

# Login accounts. Change the passwords with environment variables before a real deployment:
#   $env:SFLP_ADMIN_PASSWORD = "..." ; $env:SFLP_MANAGER_PASSWORD = "..."
USERS = {
    "admin":   {"name": "System administrator", "role": "Admin",
                "password": os.getenv("SFLP_ADMIN_PASSWORD", "admin123")},
    "manager": {"name": "Warehouse manager", "role": "Warehouse manager",
                "password": os.getenv("SFLP_MANAGER_PASSWORD", "manager123")},
}
