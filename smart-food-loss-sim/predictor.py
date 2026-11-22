"""Runs the trained AI model on the latest readings from every store and sends alerts.

Usage:
  python predictor.py            # predict once and print results
  python predictor.py --watch    # repeat every 10 seconds (use with simulator --live)
"""
import argparse
import sqlite3
import time

import joblib
import pandas as pd

from alerts import check_and_send
from config import DB_PATH, MODEL_PATH, RISK_LEVELS, STORES
from features import WINDOW, build_features
from spoilage import halvings, risk_level, safe_days

_bundle = None


def load_model():
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise SystemExit("No model found. Run: python make_dataset.py  then  python train_model.py")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


_history_checked = False


def load_readings(store_id: str, hours: int = 96) -> pd.DataFrame:
    global _history_checked
    if not _history_checked:
        # Fresh install (no readings.db yet): build the starting history so the app has data.
        from simulator import seed_history_if_empty
        seed_history_if_empty()
        _history_checked = True
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM readings WHERE store_id = ? ORDER BY ts DESC LIMIT ?", con, params=(store_id, hours))
    con.close()
    return df.iloc[::-1].reset_index(drop=True)


def predict_store(store: dict) -> dict | None:
    df = load_readings(store["id"])
    if len(df) < WINDOW:
        return None
    b = load_model()
    f = build_features(df, store["crop"])
    X = pd.DataFrame([f])[b["features"]]
    proba = b["model"].predict_proba(X)[0]
    level = int(proba.argmax())
    now_days = safe_days(store["crop"], f["grain_temp"], f["humidity"], f["grain_moisture"])
    return {
        "store": store, "level": level, "level_name": RISK_LEVELS[level],
        "proba": {RISK_LEVELS[int(c)]: float(p) for c, p in zip(b["model"].classes_, proba)},
        "features": f, "safe_days_now": now_days,
        "drivers": halvings(store["crop"], f["grain_temp"], f["humidity"], f["grain_moisture"]),
        "last_ts": df["ts"].iloc[-1],
    }


def predict_all() -> list[dict]:
    return [p for p in (predict_store(s) for s in STORES) if p]


def risk_score(proba: dict) -> float:
    """One spoilage-risk number (0-1) from the model's probabilities: Act now counts fully, Watch half."""
    return min(1.0, proba.get("Act now", 0) + 0.5 * proba.get("Watch", 0))


def assess_store(store: dict) -> dict | None:
    """Like predict_store, but still answers when there is no trained model or under 48 h of readings:
    it then falls back to the storage rule (safe days at the current readings) and gives no percentage.
    Extra keys: model (True when the AI model was used) and risk_pct (0-1, or None)."""
    if MODEL_PATH.exists():
        p = predict_store(store)
        if p:
            return {**p, "model": True, "risk_pct": risk_score(p["proba"])}
    df = load_readings(store["id"], hours=WINDOW)
    if len(df) < 3:
        return None
    f = build_features(df, store["crop"])
    days = safe_days(store["crop"], f["grain_temp"], f["humidity"], f["grain_moisture"])
    level = risk_level(days)
    return {
        "store": store, "level": level, "level_name": RISK_LEVELS[level], "proba": None,
        "features": f, "safe_days_now": days,
        "drivers": halvings(store["crop"], f["grain_temp"], f["humidity"], f["grain_moisture"]),
        "last_ts": df["ts"].iloc[-1], "model": False, "risk_pct": None,
    }


def print_table(preds):
    print(f"\n{'Store':<26}{'Moisture':>9}{'RH':>6}{'Grain T':>9}{'Safe days':>11}   AI risk (next 72 h)")
    for p in preds:
        f = p["features"]
        print(f"{p['store']['name']:<26}{f['grain_moisture']:>8.1f}%{f['humidity']:>5.0f}%"
              f"{f['grain_temp']:>8.1f}C{p['safe_days_now']:>10.0f}   {p['level_name']}"
              f"  ({p['proba'].get(p['level_name'], 0):.0%} sure)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=float, default=10)
    args = ap.parse_args()
    while True:
        preds = predict_all()
        print_table(preds)
        for msg in check_and_send(preds):
            print("  SMS ->", msg)
        if not args.watch:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
