"""Creates a training dataset by simulating many storage situations.

For each simulated store we record noisy sensor readings (what the AI is allowed to see)
and the true storage conditions (hidden). The label is the worst risk level the grain
reaches during the NEXT 72 hours, so the model learns to warn before spoilage, not after.

Usage:  python make_dataset.py --stores 800
"""
import argparse
import random
from datetime import datetime, timedelta

import pandas as pd

from config import CROPS, DATASET_PATH
from features import WINDOW, build_features
from simulator import SCENARIOS, VirtualNode
from spoilage import risk_level, safe_days

HORIZON = 72        # hours ahead the label looks
SAMPLE_EVERY = 12   # take one training example every 12 simulated hours


def random_store(rng: random.Random, i: int) -> dict:
    crop = rng.choice(list(CROPS))
    return {
        "id": f"SIM{i:04d}", "crop": crop,
        "start_T": rng.uniform(15, 32),
        "start_RH": rng.uniform(50, 88),
        "start_m": CROPS[crop]["m_safe"] + rng.uniform(-2.0, 4.0),
        "scenario": rng.choice(list(SCENARIOS)),
    }


def simulate(store: dict, seed: int, hours: int):
    rng = random.Random(seed)
    node = VirtualNode(store, seed)
    # Every situation is a little different.
    node.drift_T = rng.uniform(-0.01, 0.03)
    node.drift_RH = rng.uniform(-0.05, 0.08)
    node.p_rain = rng.uniform(0.0, 0.07)
    event_hour = rng.randint(30, hours - 30) if rng.random() < 0.3 else None
    event = rng.choice(["dry_grain", "ventilate", "rain"])

    ts = datetime(2026, 1, 1, rng.randint(0, 23))
    rows, truth = [], []
    for h in range(hours):
        if h == event_hour:
            _quiet_event(node, event)
        rows.append(node.step(ts + timedelta(hours=h)))
        truth.append(node.true_state)
    return pd.DataFrame(rows), truth


def _quiet_event(node, event):
    """Same as node.apply_event but without printing."""
    if event == "rain":
        node.rain_left = 24
    elif event == "dry_grain":
        node.m = max(11.5, node.m - 2.5)
    elif event == "ventilate":
        node.base_RH = max(50, node.base_RH - 10)
        node.drift_RH = min(node.drift_RH, 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stores", type=int, default=800, help="number of simulated storage situations")
    args = ap.parse_args()

    rng = random.Random(42)
    hours = WINDOW + HORIZON + 96
    examples = []
    for i in range(args.stores):
        store = random_store(rng, i)
        readings, truth = simulate(store, seed=1000 + i, hours=hours)
        for t in range(WINDOW, hours - HORIZON, SAMPLE_EVERY):
            f = build_features(readings.iloc[t - WINDOW:t], store["crop"])
            future = truth[t - 1: t - 1 + HORIZON]
            worst_days = min(safe_days(store["crop"], T, RH, m) for T, RH, m in future)
            f["label"] = risk_level(worst_days)
            f["group"] = i   # keeps examples from one store together when splitting train/test
            f["crop"] = store["crop"]
            examples.append(f)
        if (i + 1) % 100 == 0:
            print(f"  simulated {i + 1}/{args.stores} stores")

    df = pd.DataFrame(examples)
    df.to_csv(DATASET_PATH, index=False)
    print(f"Saved {len(df)} examples -> {DATASET_PATH.name}")
    print("Examples per risk level:", df["label"].value_counts().sort_index().to_dict(),
          "(0 = Good, 1 = Watch, 2 = Act now)")


if __name__ == "__main__":
    main()
