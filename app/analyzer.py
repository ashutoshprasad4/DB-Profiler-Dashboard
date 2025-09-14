# app/analyzer.py
import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np

class Analyzer:
    def __init__(self, anomaly_model=None):
        # default anomaly model: IsolationForest on exec_time_ms and rows_examined
        self.model = anomaly_model or IsolationForest(n_estimators=100, contamination=0.02, random_state=42)

    def train_anomaly(self, df: pd.DataFrame):
        X = df[['execution_time','rows_examined']].fillna(0).values
        self.model.fit(X)

    def detect_anomalies(self, df: pd.DataFrame):
    # --- FIX: Use the consistent 'execution_time' column name ---
        X = df[['execution_time','rows_examined']].fillna(0).values
        preds = self.model.predict(X)  # -1 anomaly, 1 normal
        df = df.copy()
        df['anomaly'] = (preds == -1)
        return df

    def rule_checks(self, df: pd.DataFrame):
    # simple rules: full scan (rows_examined > threshold), joins on big tables, heavy sorts
        checks = []
        for _, row in df.iterrows():
            reasons = []
        # --- FIX: Use the consistent 'execution_time' column name ---
            if row['rows_examined'] > 1_000_00 and row['execution_time'] > 200:
                reasons.append("Large rows examined + high exec time -> possible missing index or full scan")
            if row['is_join'] and row['rows_examined'] > 50_000:
                reasons.append("Expensive join detected — check join keys and indexes")
        # add more heuristics as needed
            checks.append(reasons)
        df['reasons'] = checks
        return df
