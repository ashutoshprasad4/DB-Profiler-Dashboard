# app/collector.py
import pandas as pd
from pathlib import Path
from .utils import read_csv_file

def collect_from_csv(path: str):
    df = read_csv_file(path)
    # Basic normalization
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Example future extension: collector that reads pg_stat_statements or MySQL performance_schema
