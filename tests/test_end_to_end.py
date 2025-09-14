# tests/test_end_to_end.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.generator import generate_csv
from app.collector import collect_from_csv
from app.features import extract_features
from app.analyzer import Analyzer

def test_pipeline():
    generate_csv("examples/test_logs.csv", n=100)
    df = collect_from_csv("examples/test_logs.csv")
    df = extract_features(df)
    an = Analyzer()
    an.train_anomaly(df)
    df2 = an.detect_anomalies(df)
    assert 'anomaly' in df2.columns
