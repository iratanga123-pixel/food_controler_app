"""Admin data stored in SQLite (data/admin.db):
  - crop_limits:  the temperature, humidity and moisture range each crop must stay within
  - food_batches: food registered by the admin or warehouse manager when it enters a store
  - inspections:  manual inspections recorded on the Simulation control page
"""
import sqlite3
from datetime import datetime

import pandas as pd

from config import ADMIN_DB, CROPS, DEFAULT_LIMITS
from i18n import tr

LIMIT_FIELDS = ["temp_min", "temp_max", "rh_min", "rh_max", "moisture_min", "moisture_max"]


def _default_moisture_min(crop: str, moisture_max: float) -> float:
    return DEFAULT_LIMITS[crop]["moisture_min"] if crop in DEFAULT_LIMITS else round(moisture_max - 3.0, 1)


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(ADMIN_DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS crop_limits (
        crop TEXT PRIMARY KEY, label TEXT NOT NULL,
        temp_min REAL NOT NULL, temp_max REAL NOT NULL,
        rh_min REAL NOT NULL, rh_max REAL NOT NULL, moisture_max REAL NOT NULL,
        updated_by TEXT, updated_at TEXT, moisture_min REAL)""")
    # Databases made before the minimum moisture existed: add it with sensible values.
    if "moisture_min" not in [r["name"] for r in con.execute("PRAGMA table_info(crop_limits)")]:
        con.execute("ALTER TABLE crop_limits ADD COLUMN moisture_min REAL")
    for r in con.execute("SELECT crop, moisture_max FROM crop_limits WHERE moisture_min IS NULL").fetchall():
        con.execute("UPDATE crop_limits SET moisture_min=? WHERE crop=?",
                    (_default_moisture_min(r["crop"], r["moisture_max"]), r["crop"]))
    con.execute("""CREATE TABLE IF NOT EXISTS food_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id TEXT NOT NULL, crop TEXT NOT NULL,
        quantity_kg REAL NOT NULL, bags INTEGER,
        supplier TEXT NOT NULL, supplier_phone TEXT,
        date_in TEXT NOT NULL, intake_moisture REAL, intake_temp REAL,
        quality TEXT, intake_check TEXT, notes TEXT,
        status TEXT NOT NULL DEFAULT 'In storage', date_out TEXT,
        registered_by TEXT, registered_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id TEXT NOT NULL, inspected_at TEXT NOT NULL, inspector TEXT NOT NULL,
        findings TEXT, moisture REAL, notes TEXT)""")
    if con.execute("SELECT COUNT(*) FROM crop_limits").fetchone()[0] == 0:
        for crop, lim in DEFAULT_LIMITS.items():
            _upsert_limits(con, crop, CROPS[crop]["label"], lim, "system")
    con.commit()
    return con


# ---- Crop limits -----------------------------------------------------------

def get_limits() -> dict[str, dict]:
    with connect() as con:
        return {r["crop"]: dict(r) for r in con.execute("SELECT * FROM crop_limits ORDER BY label")}


def validate_limits(lim: dict) -> list[str]:
    """Error keys (see i18n.STRINGS) for limits that make no sense; empty list = valid."""
    errors = []
    if lim["temp_min"] >= lim["temp_max"]:
        errors.append("e_temp_order")
    if lim["rh_min"] >= lim["rh_max"]:
        errors.append("e_rh_order")
    if not (0 <= lim["rh_min"] <= 100 and 0 <= lim["rh_max"] <= 100):
        errors.append("e_rh_range")
    if not (0 < lim["moisture_min"] < 40 and 0 < lim["moisture_max"] < 40):
        errors.append("e_m_range")
    if lim["moisture_min"] >= lim["moisture_max"]:
        errors.append("e_m_order")
    return errors


def _upsert_limits(con, crop: str, label: str, lim: dict, user: str) -> None:
    cols = ", ".join(LIMIT_FIELDS)
    updates = ", ".join(f"{k}=excluded.{k}" for k in ["label", *LIMIT_FIELDS, "updated_by", "updated_at"])
    con.execute(f"""INSERT INTO crop_limits (crop, label, {cols}, updated_by, updated_at)
        VALUES (?, ?, {", ".join("?" * len(LIMIT_FIELDS))}, ?, ?)
        ON CONFLICT(crop) DO UPDATE SET {updates}""",
                (crop, label, *(float(lim[k]) for k in LIMIT_FIELDS),
                 user, datetime.now().isoformat(timespec="seconds")))


def save_limits(crop: str, label: str, lim: dict, user: str) -> None:
    with connect() as con:
        _upsert_limits(con, crop, label, lim, user)


def limit_breaches(lim: dict, temp: float | None, rh: float | None, moisture: float | None,
                   lang: str = "en") -> list[str]:
    """Plain-language list of readings outside the crop's limits (empty list = all fine)."""
    out = []
    if temp is not None:
        if temp < lim["temp_min"]:
            out.append(tr("b_temp_low", lang, v=temp, lim=lim["temp_min"]))
        elif temp > lim["temp_max"]:
            out.append(tr("b_temp_high", lang, v=temp, lim=lim["temp_max"]))
    if rh is not None:
        if rh < lim["rh_min"]:
            out.append(tr("b_rh_low", lang, v=rh, lim=lim["rh_min"]))
        elif rh > lim["rh_max"]:
            out.append(tr("b_rh_high", lang, v=rh, lim=lim["rh_max"]))
    if moisture is not None:
        if lim.get("moisture_min") is not None and moisture < lim["moisture_min"]:
            out.append(tr("b_m_low", lang, v=moisture, lim=lim["moisture_min"]))
        elif moisture > lim["moisture_max"]:
            out.append(tr("b_m_high", lang, v=moisture, lim=lim["moisture_max"]))
    return out


# ---- Food registration -----------------------------------------------------

def register_batch(b: dict, user: str) -> int:
    with connect() as con:
        cur = con.execute("""INSERT INTO food_batches
            (store_id, crop, quantity_kg, bags, supplier, supplier_phone, date_in, intake_moisture,
             intake_temp, quality, intake_check, notes, registered_by, registered_at)
            VALUES (:store_id, :crop, :quantity_kg, :bags, :supplier, :supplier_phone, :date_in,
             :intake_moisture, :intake_temp, :quality, :intake_check, :notes, :user, :now)""",
                          {**b, "user": user, "now": datetime.now().isoformat(timespec="seconds")})
        return cur.lastrowid


def list_batches() -> pd.DataFrame:
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM food_batches ORDER BY date_in DESC, id DESC", con)


def dispatch_batch(batch_id: int, date_out: str) -> None:
    with connect() as con:
        con.execute("UPDATE food_batches SET status='Dispatched', date_out=? WHERE id=? AND status='In storage'",
                    (date_out, batch_id))


def add_inspection(store_id: str, inspector: str, findings: list[str], moisture: float | None,
                   notes: str | None) -> int:
    """Manual inspection of a store. findings: keys like 'in_insects' (texts in i18n)."""
    with connect() as con:
        cur = con.execute("""INSERT INTO inspections (store_id, inspected_at, inspector, findings, moisture, notes)
            VALUES (?,?,?,?,?,?)""", (store_id, datetime.now().isoformat(timespec="minutes"), inspector,
                                      ";".join(findings), moisture, notes))
        return cur.lastrowid


def list_inspections(store_id: str, limit: int = 10) -> pd.DataFrame:
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM inspections WHERE store_id=? ORDER BY id DESC LIMIT ?",
                                 con, params=(store_id, limit))


def stock_by_store() -> dict[str, float]:
    """Tonnes currently in storage per store, from registered batches."""
    with connect() as con:
        rows = con.execute("""SELECT store_id, SUM(quantity_kg) FROM food_batches
                              WHERE status='In storage' GROUP BY store_id""").fetchall()
    return {sid: kg / 1000 for sid, kg in rows}
