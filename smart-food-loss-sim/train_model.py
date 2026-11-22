"""Trains the AI model that predicts spoilage risk for the next 72 hours.

Compares it with a simple rule that only looks at today's readings, so you can show
in your report what the AI adds (it sees trends and warns earlier).

Usage:  python train_model.py
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, recall_score
from sklearn.model_selection import GroupShuffleSplit

from config import CROPS, DATASET_PATH, MODEL_PATH, RISK_LEVELS
from features import FEATURES
from spoilage import risk_level, safe_days


def rule_baseline(df: pd.DataFrame) -> np.ndarray:
    """Old way: judge only by current readings, no forecasting."""
    return np.array([
        risk_level(safe_days(r.crop, r.grain_temp, r.humidity, r.grain_moisture))
        for r in df.itertuples()
    ])


def main():
    df = pd.read_csv(DATASET_PATH)
    X, y = df[FEATURES], df["label"]

    # Split by store so the test set contains storage situations the model never saw.
    split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=0)
    train_idx, test_idx = next(split.split(X, y, groups=df["group"]))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    model = RandomForestClassifier(n_estimators=300, min_samples_leaf=3,
                                   class_weight="balanced", random_state=0, n_jobs=-1)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    base = rule_baseline(df.iloc[test_idx])

    print(f"Training examples: {len(X_train)}   Test examples: {len(X_test)}\n")
    print("=== AI model (Random Forest, sees 48 h of history) ===")
    print(classification_report(y_test, pred, target_names=RISK_LEVELS, digits=3))
    print("Confusion matrix (rows = true, columns = predicted):")
    print(pd.DataFrame(confusion_matrix(y_test, pred, labels=[0, 1, 2]),
                       index=RISK_LEVELS, columns=RISK_LEVELS), "\n")

    print("=== Comparison with a rule on current readings only ===")
    rows = []
    for name, p in [("Rule (today only)", base), ("AI model", pred)]:
        rows.append({
            "method": name,
            "accuracy": accuracy_score(y_test, p),
            "recall 'Act now'": recall_score(y_test, p, labels=[2], average="macro", zero_division=0),
            "recall 'Watch'+'Act now'": recall_score(y_test >= 1, p >= 1, zero_division=0),
        })
    print(pd.DataFrame(rows).round(3).to_string(index=False), "\n")
    print("Recall = share of real problems that got an alert. Missing a real problem is the costly error.\n")

    imp = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print("Most important inputs:")
    print(imp.head(8).round(3).to_string(), "\n")

    joblib.dump({"model": model, "features": FEATURES}, MODEL_PATH)
    print(f"Saved model -> {MODEL_PATH.name}")


if __name__ == "__main__":
    main()
