# app/features.py
import pandas as pd
from .parser import normalize_sql, fingerprint

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['normalized'] = df['query'].apply(normalize_sql)
    df['fingerprint'] = df['normalized'].apply(fingerprint)
    # simple derived features
    df['hour'] = df['timestamp'].dt.hour
    df['is_select'] = df['normalized'].str.upper().str.startswith('SELECT').astype(int)
    df['is_join'] = df['normalized'].str.upper().str.contains(' JOIN ').astype(int)
    # numeric features already present: exec_time_ms, rows_examined
    return df
