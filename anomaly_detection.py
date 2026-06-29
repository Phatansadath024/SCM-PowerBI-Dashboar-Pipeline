"""Anomaly detection proof of concept for production planning KPIs."""

import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_backlog_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Detect unusual backlog/capacity patterns using Isolation Forest."""
    features = ["Open Quantity", "Required Net Hours", "Required Employee Days"]
    model_df = df.dropna(subset=features).copy()

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
    )
    model_df["Anomaly Flag"] = model.fit_predict(model_df[features])
    model_df["Is Anomaly"] = model_df["Anomaly Flag"].eq(-1)
    model_df["Anomaly Score"] = model.decision_function(model_df[features])
    return model_df
