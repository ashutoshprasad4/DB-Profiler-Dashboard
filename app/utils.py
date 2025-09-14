# app/utils.py
import pandas as pd
from pathlib import Path

def read_csv_file(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{path} not found")
    return pd.read_csv(path)
