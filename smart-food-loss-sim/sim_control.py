"""Link between the Simulation control page and the running simulator (simulator.py --live).

  data/control.json     written by the page: run/pause and the test scenario per store
  data/commands/*.json  one-off commands (set or reset sensor values); the simulator deletes each once applied
  data/sim_status.json  written by the simulator: heartbeat, simulated time, which sensors are online

Each file has a single writer, so the page and the simulator never overwrite each other.
"""
import json
import os
import subprocess
import sys
import time
import uuid

from config import BASE_DIR, DATA_DIR

CONTROL_FILE = DATA_DIR / "control.json"
STATUS_FILE = DATA_DIR / "sim_status.json"
COMMANDS_DIR = DATA_DIR / "commands"
SIM_LOG = DATA_DIR / "simulator.log"

# Test scenarios that can be switched on per store (texts in i18n: sc_<key> and scd_<key>).
SCENARIOS = ["normal", "high_temperature", "high_humidity", "high_moisture",
             "poor_ventilation", "sensor_disconnection", "power_failure"]
OFFLINE_SCENARIOS = ("sensor_disconnection", "power_failure")   # the sensor node sends nothing

DEFAULT_STORE = {"scenario": "normal"}


def _read_json(path, default):
    for _ in range(10):      # on Windows a read fails for a moment while the other side swaps the file in
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except PermissionError:
            time.sleep(0.05)
        except (OSError, json.JSONDecodeError):
            return default
    return default


def _write_json(path, data):
    """Write to a temporary file and swap it in, so a reader never sees half a file."""
    tmp = path.with_name(f"{path.stem}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    for _ in range(10):          # on Windows the swap fails while the other side has the file open
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05)
    tmp.unlink(missing_ok=True)
    raise PermissionError(f"Could not write {path.name}")


# ---- Control (written by the page) -------------------------------------------

def read_control() -> dict:
    c = _read_json(CONTROL_FILE, {})
    c.setdefault("running", True)
    c.setdefault("stores", {})
    return c


def store_control(control: dict, store_id: str) -> dict:
    return {**DEFAULT_STORE, **control["stores"].get(store_id, {})}


def update_store(store_id: str, **changes):
    c = read_control()
    c["stores"].setdefault(store_id, {}).update(changes)
    _write_json(CONTROL_FILE, c)


def set_running(running: bool):
    c = read_control()
    c["running"] = running
    _write_json(CONTROL_FILE, c)


def send_command(store_id: str, cmd: str, **args):
    COMMANDS_DIR.mkdir(exist_ok=True)
    _write_json(COMMANDS_DIR / f"{time.time_ns()}_{uuid.uuid4().hex[:6]}.json",
                {"store_id": store_id, "cmd": cmd, **args})


# ---- Automatic warehouse control ---------------------------------------------

# Every store is controlled automatically: there is no manual switching.
#   above a limit -> cooling fan, ventilation, dehumidifier
#   below a limit -> heater, humidifier
EQUIPMENT = ["cooling_fan", "ventilation", "dehumidifier", "heater", "humidifier"]
TARGETS = ["dehumidifier_target", "humidifier_target", "heater_target"]
RH_BAND = 5.0      # % humidity back inside the limit before equipment switches off again
T_BAND = 1.0       # °C back inside the limit before the fan or heater switches off again
M_BAND = 0.2       # % grain moisture back inside the limit before drying or re-wetting stops


def initial_equipment(lim: dict | None = None) -> dict:
    eq = {name: False for name in EQUIPMENT}
    eq.update(targets(lim) if lim else {"dehumidifier_target": 60, "humidifier_target": 55, "heater_target": 15})
    return eq


def targets(lim: dict) -> dict:
    """Where the machines push the store: toward the middle of the crop's allowed band."""
    return {"dehumidifier_target": round(max(lim["rh_min"] + RH_BAND, lim["rh_max"] - 2 * RH_BAND)),
            "humidifier_target": round(min(lim["rh_max"] - RH_BAND, lim["rh_min"] + 2 * RH_BAND)),
            "heater_target": lim["temp_min"] + 3 * T_BAND}


def auto_decide(eq: dict, temp: float, rh: float, moisture: float, lim: dict) -> tuple[dict, list[dict]]:
    """Automatic controller for one store, run every simulated hour on the sensor readings
    (grain temperature, air humidity, grain moisture) against the crop's limits.

    Switches ON when a reading goes past a limit (above or below), and OFF only once it is back
    inside by a margin, so the equipment does not flick on and off with the daily cycle. Returns the
    new equipment state and log entries {eq, on, why, v, lim}; `why` is a text key in i18n (b_* or ar_ok).
    """
    hot, cold = temp > lim["temp_max"], temp < lim["temp_min"]
    humid, dry_air = rh > lim["rh_max"], rh < lim["rh_min"]
    wet, over_dried = moisture > lim["moisture_max"], moisture < lim["moisture_min"]
    cool_ok = temp < lim["temp_max"] - T_BAND
    warm_ok = temp > lim["temp_min"] + T_BAND
    air_ok = rh < lim["rh_max"] - RH_BAND
    air_moist_ok = rh > lim["rh_min"] + RH_BAND
    grain_ok = moisture < lim["moisture_max"] - M_BAND
    grain_moist_ok = moisture > lim["moisture_min"] + M_BAND

    # (switch on?, reason) and (switch off?, reason) per piece of equipment
    reason_hot = ("b_temp_high", temp, lim["temp_max"])
    reason_cold = ("b_temp_low", temp, lim["temp_min"])
    reason_humid = ("b_rh_high", rh, lim["rh_max"])
    reason_dry = ("b_rh_low", rh, lim["rh_min"])
    reason_wet = ("b_m_high", moisture, lim["moisture_max"])
    reason_over_dried = ("b_m_low", moisture, lim["moisture_min"])
    ok = ("ar_ok", None, None)
    rules = {
        "cooling_fan": (hot and reason_hot,
                        (cold and reason_cold) or (cool_ok and ok)),
        "ventilation": (not dry_air and ((humid and reason_humid) or (hot and reason_hot) or (wet and reason_wet)),
                        (dry_air and reason_dry) or (air_ok and cool_ok and grain_ok and ok)),
        "dehumidifier": (not dry_air and ((humid and reason_humid) or (wet and reason_wet)),
                         (dry_air and reason_dry) or (air_ok and grain_ok and ok)),
        "heater": (cold and reason_cold,
                   (hot and reason_hot) or (warm_ok and ok)),
        "humidifier": (not humid and ((dry_air and reason_dry) or (over_dried and reason_over_dried)),
                       (humid and reason_humid) or (air_moist_ok and grain_moist_ok and ok)),
    }
    new, log = dict(eq), []
    for name, (turn_on, turn_off) in rules.items():
        if not eq.get(name) and turn_on:
            new[name], why = True, turn_on
        elif eq.get(name) and turn_off:
            new[name], why = False, turn_off
        else:
            continue
        log.append({"eq": name, "on": new[name], "why": why[0], "v": why[1], "lim": why[2]})
    new.update(targets(lim))
    return new, log


# ---- Used by the simulator ---------------------------------------------------

def take_commands() -> list[dict]:
    """Commands in the order they were sent; each is removed once read."""
    if not COMMANDS_DIR.exists():
        return []
    out = []
    for path in sorted(COMMANDS_DIR.glob("*.json")):
        data = _read_json(path, None)
        try:
            path.unlink()
        except OSError:
            continue                    # still being written; pick it up next hour
        if data:
            out.append(data)
    return out


def clear_all():
    """Fresh simulation run: forget old settings, commands and status."""
    for path in (CONTROL_FILE, STATUS_FILE):
        path.unlink(missing_ok=True)
    if COMMANDS_DIR.exists():
        for path in COMMANDS_DIR.glob("*"):
            path.unlink(missing_ok=True)


def write_status(status: dict):
    _write_json(STATUS_FILE, {**status, "heartbeat": time.time()})


def remove_status():
    STATUS_FILE.unlink(missing_ok=True)


# ---- Used by the page --------------------------------------------------------

def read_status() -> dict | None:
    return _read_json(STATUS_FILE, None)


def simulator_alive(status: dict | None = None) -> bool:
    """True when simulator.py --live has reported in recently (it reports every simulated hour)."""
    status = status if status is not None else read_status()
    if not status:
        return False
    return time.time() - status.get("heartbeat", 0) < max(10.0, 3 * status.get("interval", 3.0))


def start_simulator(interval: float = 3.0):
    """Start simulator.py --live: in its own console window on Windows, in the background elsewhere."""
    cmd = [sys.executable, str(BASE_DIR / "simulator.py"), "--live", "--interval", str(interval)]
    if os.name == "nt":
        subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        log = open(SIM_LOG, "a", encoding="utf-8")
        subprocess.Popen(cmd, cwd=BASE_DIR, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
