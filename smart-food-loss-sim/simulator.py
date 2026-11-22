"""Virtual IoT sensor nodes.

Each storage site gets a simulated sensor node that measures, once per (simulated) hour:
  air temperature, relative humidity, grain moisture and temperature inside the grain.
Readings are saved to SQLite, the same way a real node would send them to the cloud.

Usage:
  python simulator.py --hours 96             # create 96 hours of history quickly
  python simulator.py --live --interval 3    # history, then keep sending: 1 simulated hour every 3 s
While --live runs, the dashboard can inject events (rain, drying, ventilation), and the
Simulation control page can pause it, set sensor values and switch test scenarios (see sim_control.py).
Each store's equipment (cooling fan, ventilation, dehumidifier, heater, humidifier) is switched
automatically whenever a reading goes above or below the crop's storage limits.
"""
import argparse
import json
import math
import random
import sqlite3
import time
from collections import deque
from datetime import datetime, timedelta

import sim_control
from config import DB_PATH, DATA_DIR, STORES
from spoilage import equilibrium_moisture, safe_days

EVENTS_FILE = DATA_DIR / "events.json"

SCENARIOS = {
    #               air temp drift/h, RH drift/h, chance of a rain shower per hour
    "normal":       (0.000,  0.000, 0.01),
    "rainy_season": (0.000,  0.060, 0.06),
    "wet_harvest":  (0.005,  0.020, 0.04),
    "hot_dry":      (0.020, -0.020, 0.00),
}
RH_RANGE = (40.0, 92.0)      # limits of the store's average humidity (readings swing around it)
LIVE_RH_MIN = 25.0           # lower humidity limit in live mode (lets the page test over-dry air)
T_RANGE = (5.0, 42.0)        # limits of the store's average air temperature


def connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS readings (
        store_id TEXT, ts TEXT, air_temp REAL, humidity REAL,
        grain_moisture REAL, grain_temp REAL)""")
    return con


class VirtualNode:
    def __init__(self, store, seed):
        self.s = store
        self.rng = random.Random(seed)
        self.base_T = store["start_T"]
        self.base_RH = store["start_RH"]
        self.m = store["start_m"]            # true grain moisture
        self.T_grain = store["start_T"]
        self.rain_left = 0                   # hours of rain remaining
        self.drift_T, self.drift_RH, self.p_rain = SCENARIOS[store["scenario"]]
        self.online = True                   # False while the sensor node sends nothing
        # Automatic warehouse control (live mode): equipment state chosen by the controller
        self.auto_eq = sim_control.initial_equipment()
        self.recent = deque(maxlen=3)        # last readings, averaged to smooth sensor noise
        self.auto_log = deque(maxlen=10)     # last switching decisions, shown on the page

    def apply_event(self, event):
        if event == "rain":
            self.rain_left = 24
        elif event == "dry_grain":           # farmers sun-dry the grain
            self.m = max(11.5, self.m - 2.5)
        elif event == "ventilate":           # open vents, add pallets
            self.base_RH = max(50, self.base_RH - 10)
            self.drift_RH = min(self.drift_RH, 0.0)
        print(f"  [event] {self.s['id']}: {event}")

    def set_values(self, temp: float, humidity: float, moisture: float):
        """Put the store at these conditions (from the Simulation control page)."""
        self.base_T = self.T_grain = float(temp)
        self.base_RH = float(humidity)
        self.m = float(moisture)
        print(f"  [control] {self.s['id']}: set to {temp} C, {humidity}% RH, {moisture}% moisture")

    def reset_values(self):
        self.set_values(self.s["start_T"], self.s["start_RH"], self.s["start_m"])

    def _apply_controls(self, ctl: dict) -> bool:
        """Effect of the test scenario and the store's equipment for one hour.
        Returns True when the cooling fan is running. Does nothing when ctl is empty."""
        scenario = ctl.get("scenario", "normal")
        powered = scenario != "power_failure"           # no power: all equipment stops
        vent = powered and ctl.get("ventilation", False)
        fan = powered and ctl.get("cooling_fan", False)
        dehum = powered and ctl.get("dehumidifier", False)
        heater = powered and ctl.get("heater", False)
        humidifier = powered and ctl.get("humidifier", False)

        if scenario == "high_temperature":              # heat wave, store heats up toward 35 C
            self.base_T += (35.0 - self.base_T) * 0.08
        elif scenario == "high_humidity":               # humid weather, air climbs toward 90%
            self.base_RH += (90.0 - self.base_RH) * 0.08
        elif scenario == "high_moisture":               # wet grain loaded into the store
            self.m += (19.0 - self.m) * 0.05
        if scenario in ("poor_ventilation", "power_failure") and not vent:
            self.base_RH += 0.5                         # stale, damp air builds up and warms
            self.base_T += 0.05

        if vent:                                        # fresh air brings humidity down toward 55%
            self.base_RH += (55.0 - self.base_RH) * 0.06
        if fan and self.base_T > 18.0:                  # cooling machine: pulls the store toward 18 C,
            self.base_T += (18.0 - self.base_T) * 0.15  # strong enough to beat a 35 C heat wave
        if dehum:
            target = float(ctl.get("dehumidifier_target", 60))
            if self.base_RH > target:
                self.base_RH += (target - self.base_RH) * 0.10
        if heater:                                      # warms a cold store toward its target
            target = float(ctl.get("heater_target", 15))
            if self.base_T < target:
                self.base_T += (target - self.base_T) * 0.10
        if humidifier:                                  # moistens over-dry air toward its target
            target = float(ctl.get("humidifier_target", 55))
            if self.base_RH < target:
                self.base_RH += (target - self.base_RH) * 0.10
        self.base_T = min(T_RANGE[1], max(T_RANGE[0], self.base_T))
        self.online = scenario not in sim_control.OFFLINE_SCENARIOS
        return fan

    def step(self, ts: datetime, ctl: dict | None = None) -> dict | None:
        """One simulated hour. Returns the sensor reading, or None while the sensor is offline."""
        r = self.rng
        fan = self._apply_controls(ctl) if ctl else False
        self.base_T += self.drift_T
        # Under the page's control the store may be pushed drier than the weather patterns go.
        rh_low = LIVE_RH_MIN if ctl else RH_RANGE[0]
        self.base_RH = min(RH_RANGE[1], max(rh_low, self.base_RH + self.drift_RH))
        if self.rain_left == 0 and r.random() < self.p_rain:
            self.rain_left = r.randint(3, 10)

        cycle = math.cos(2 * math.pi * (ts.hour - 14) / 24)   # warmest at 14:00
        T_air = self.base_T + 3.0 * cycle + r.gauss(0, 0.4)
        RH = self.base_RH - 7.0 * cycle + r.gauss(0, 1.5)
        if self.rain_left > 0:
            RH += 12
            T_air -= 1.5
            self.rain_left -= 1
        RH = min(99.0, max(25.0, RH))

        # Grain slowly absorbs or loses water to the air.
        self.m += (equilibrium_moisture(RH) - self.m) * 0.004
        # Grain temperature lags the air (faster with the cooling fan blowing through it),
        # and rises by itself when mould and insects are active.
        self.T_grain += (T_air - self.T_grain) * (0.12 if fan else 0.05)
        if safe_days(self.s["crop"], self.T_grain, RH, self.m) < 10:
            self.T_grain += 0.04

        self.true_state = (self.T_grain, RH, self.m)   # used only to label training data
        # Real sensors are noisy.
        row = {
            "store_id": self.s["id"],
            "ts": ts.isoformat(timespec="minutes"),
            "air_temp": round(T_air + r.gauss(0, 0.2), 2),
            "humidity": round(RH + r.gauss(0, 1.0), 1),
            "grain_moisture": round(self.m + r.gauss(0, 0.15), 2),
            "grain_temp": round(self.T_grain + r.gauss(0, 0.2), 2),
        }
        return row if self.online else None


def save(con, row):
    con.execute("INSERT INTO readings VALUES (:store_id, :ts, :air_temp, :humidity, :grain_moisture, :grain_temp)", row)


def read_events():
    if not EVENTS_FILE.exists():
        return {}
    try:
        events = json.loads(EVENTS_FILE.read_text())
    except json.JSONDecodeError:
        events = {}
    EVENTS_FILE.unlink(missing_ok=True)
    return events


def apply_command(nodes, cmd):
    node = next((n for n in nodes if n.s["id"] == cmd.get("store_id")), None)
    if node is None:
        return
    if cmd["cmd"] == "set_values":
        node.set_values(cmd["temp"], cmd["humidity"], cmd["moisture"])
    elif cmd["cmd"] == "reset_values":
        node.reset_values()


def store_hour(con, node, ts, scenario_ctl: dict, lim: dict | None) -> dict | None:
    """One simulated hour for one store. Its equipment is always run by the automatic controller."""
    row = node.step(ts, {**scenario_ctl, **node.auto_eq})
    if row is None:
        return None                       # sensor offline: the controller is blind, keeps its last state
    save(con, row)
    node.recent.append(row)
    if lim:
        avg = {k: sum(r[k] for r in node.recent) / len(node.recent)
               for k in ("grain_temp", "humidity", "grain_moisture")}
        node.auto_eq, log = sim_control.auto_decide(node.auto_eq, avg["grain_temp"], avg["humidity"],
                                                    avg["grain_moisture"], lim)
        for entry in log:
            node.auto_log.appendleft({**entry, "ts": row["ts"]})
            print(f"  [auto] {node.s['id']}: {entry['eq']} {'ON' if entry['on'] else 'OFF'} ({entry['why']})")
    return row


def write_status(nodes, ts, running, interval):
    stores = {}
    for n in nodes:
        stores[n.s["id"]] = {
            "online": n.online, "temp": round(n.base_T, 1), "humidity": round(n.base_RH, 1),
            "moisture": round(n.m, 2), "auto_log": list(n.auto_log), "equipment": dict(n.auto_eq),
        }
    sim_control.write_status({"running": running, "interval": interval,
                              "sim_time": ts.isoformat(timespec="minutes"), "stores": stores})


def main():
    ap = argparse.ArgumentParser(description="Run the virtual sensor nodes")
    ap.add_argument("--hours", type=int, default=96, help="hours of history to create")
    ap.add_argument("--live", action="store_true", help="keep sending readings")
    ap.add_argument("--interval", type=float, default=3.0, help="real seconds per simulated hour in live mode")
    args = ap.parse_args()

    if sim_control.simulator_alive():
        raise SystemExit("The simulator is already running (pause it or close its window first).")

    con = connect()
    con.execute("DELETE FROM readings")   # every run starts a fresh history
    EVENTS_FILE.unlink(missing_ok=True)
    (DATA_DIR / "alert_state.json").unlink(missing_ok=True)
    sim_control.clear_all()
    nodes = [VirtualNode(s, seed=i * 7 + 1) for i, s in enumerate(STORES)]

    start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=args.hours)
    for h in range(args.hours):
        ts = start + timedelta(hours=h)
        for n in nodes:
            save(con, n.step(ts))
    con.commit()
    print(f"Created {args.hours} hours of readings for {len(nodes)} stores -> {DB_PATH.name}")

    if not args.live:
        return
    import registry                       # crop storage limits set by the Admin (admin.db)
    ts = start + timedelta(hours=args.hours)
    print("Live mode: press Ctrl+C to stop. Pause and control it from the Simulation control page.")
    print("Warehouse equipment runs automatically from each crop's storage limits.")
    was_running = True
    limits = {}
    try:
        while True:
            control = sim_control.read_control()
            try:                          # the Admin may change the limits at any time
                limits = registry.get_limits()
            except Exception as e:        # database busy: keep last hour's limits
                print("  (crop limits not read:", e, ")")
            for cmd in sim_control.take_commands():
                apply_command(nodes, cmd)
            for store_id, event in read_events().items():
                for n in nodes:
                    if n.s["id"] == store_id:
                        n.apply_event(event)
            if control["running"] != was_running:
                print("  [control] " + ("resumed" if control["running"] else "paused"))
                was_running = control["running"]
            if control["running"]:
                for n in nodes:
                    row = store_hour(con, n, ts, sim_control.store_control(control, n.s["id"]),
                                     limits.get(n.s["crop"]))
                    if row:
                        print("  MQTT publish sflp/" + row["store_id"], json.dumps(row))
                    else:
                        print(f"  {n.s['id']}: sensor offline, no reading")
                con.commit()
                ts += timedelta(hours=1)
            write_status(nodes, ts, control["running"], args.interval)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        sim_control.remove_status()


if __name__ == "__main__":
    main()
