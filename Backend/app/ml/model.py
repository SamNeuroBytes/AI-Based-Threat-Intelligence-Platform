"""
ML layer for the threat intelligence platform.

Two components:
  1. Feature extraction from raw indicator values (URLs/domains/IPs)
     - lexical features: length, digit ratio, entropy, special-char count,
       suspicious keyword presence, subdomain depth, TLD risk.
  2. IsolationForest anomaly detector trained on these features + confidence,
     used to assign an `ml_score` (anomaly score) and `ml_label`
     ("anomalous" / "normal") to every indicator.

This gives the project a genuine, explainable ML component (not a black box)
that can be retrained as new data arrives.
"""

import math
import re
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest.joblib")

SUSPICIOUS_KEYWORDS = [
    "login", "verify", "secure", "account", "update", "confirm",
    "bank", "wallet", "free", "bonus", "click", "urgent", "payment",
]

HIGH_RISK_TLDS = {"xyz", "top", "tk", "ml", "ga", "cf", "click", "loan", "work"}


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def extract_features(value: str, confidence: float = 0.0) -> dict:
    """Turn a raw indicator string (URL/domain/IP/hash) into numeric features."""
    value = value or ""
    length = len(value)
    digit_count = sum(c.isdigit() for c in value)
    digit_ratio = digit_count / length if length else 0
    special_count = len(re.findall(r"[^a-zA-Z0-9.]", value))
    entropy = _shannon_entropy(value)
    subdomain_depth = value.count(".")
    has_keyword = int(any(kw in value.lower() for kw in SUSPICIOUS_KEYWORDS))

    tld = value.split(".")[-1].lower() if "." in value else ""
    tld = re.sub(r"[/?#].*", "", tld)
    risky_tld = int(tld in HIGH_RISK_TLDS)

    return {
        "length": length,
        "digit_ratio": digit_ratio,
        "special_count": special_count,
        "entropy": entropy,
        "subdomain_depth": subdomain_depth,
        "has_keyword": has_keyword,
        "risky_tld": risky_tld,
        "confidence": confidence,
    }


FEATURE_COLUMNS = [
    "length", "digit_ratio", "special_count", "entropy",
    "subdomain_depth", "has_keyword", "risky_tld", "confidence",
]


def build_feature_dataframe(indicators) -> pd.DataFrame:
    rows = [extract_features(ind.value, ind.confidence or 0) for ind in indicators]
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS)


def train_model(indicators):
    """Train (or retrain) the IsolationForest on current indicator set."""
    if len(indicators) < 10:
        return None  # not enough data yet
    df = build_feature_dataframe(indicators)
    model = IsolationForest(
        n_estimators=150,
        contamination=0.15,
        random_state=42,
    )
    model.fit(df)
    joblib.dump(model, MODEL_PATH)
    return model


def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def score_indicators(indicators, model=None):
    """
    Return list of (ml_score, ml_label) for each indicator.
    ml_score: higher = more anomalous (rescaled to 0-100).
    ml_label: 'anomalous' or 'normal'.
    """
    if model is None:
        model = load_model()
    if model is None or len(indicators) == 0:
        return [(None, None) for _ in indicators]

    df = build_feature_dataframe(indicators)
    raw_scores = model.decision_function(df)  # higher = more normal
    predictions = model.predict(df)  # 1 = normal, -1 = anomaly

    # Rescale: invert and normalize to 0-100 so higher = more anomalous
    min_s, max_s = raw_scores.min(), raw_scores.max()
    span = (max_s - min_s) or 1.0
    anomaly_scores = [round((1 - (s - min_s) / span) * 100, 2) for s in raw_scores]

    labels = ["anomalous" if p == -1 else "normal" for p in predictions]
    return list(zip(anomaly_scores, labels))


def retrain_and_score(db_session, Indicator):
    """Full pipeline: train on all data, then score every indicator and save."""
    indicators = db_session.query(Indicator).all()
    model = train_model(indicators)
    if model is None:
        return 0
    scores = score_indicators(indicators, model)
    for ind, (score, label) in zip(indicators, scores):
        ind.ml_score = score
        ind.ml_label = label
    db_session.commit()
    return len(indicators)
