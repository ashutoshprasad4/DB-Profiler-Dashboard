# app/api.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv() # Loads variables from .env file

# Import your project modules
from .features import extract_features
from .analyzer import Analyzer
from .generator import generate_csv
from .ai_recommender import get_llm_recommendation_for_query

app = FastAPI()
analyzer = Analyzer()

# --- Pydantic Models for structured requests ---
class AnalyzeRequest(BaseModel):
    csv_path: str

class LLMRequest(BaseModel):
    query: str
    execution_time: float
    rows_examined: int
    reasons: List[str]

# --- API Endpoints ---
@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    Reads a CSV, runs heuristic analysis, and returns the enriched data without modifying the file.
    """
    try:
        df = pd.read_csv(req.csv_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file not found at {req.csv_path}")

    try:
        # 1. Feature Engineering
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = extract_features(df)

        # 2. Standardize column names
        if "exec_time_ms" in df.columns and "execution_time" not in df.columns:
            df = df.rename(columns={"exec_time_ms": "execution_time"})
        
        required_columns = ["execution_time", "rows_examined", "query"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Input CSV is missing the required column: '{col}'")

        # 3. Heuristic Analysis
        analyzer.train_anomaly(df)
        df_with_features = analyzer.detect_anomalies(df)
        df_with_features = analyzer.rule_checks(df_with_features)
        
        if df_with_features is None or not isinstance(df_with_features, pd.DataFrame):
            raise ValueError("Analysis resulted in an invalid DataFrame.")

        # --- FIX: Convert Timestamp objects to JSON-compatible strings ---
        # The .astype(str) method is the correct way to serialize a datetime column.
        df_with_features['timestamp'] = df_with_features['timestamp'].astype(str)

        # Convert DataFrame to a list of dicts and let JSONResponse handle encoding
        json_content = df_with_features.to_dict(orient='records')
        return JSONResponse(content=json_content)

    except Exception as e:
        # If any part of the analysis fails, return a specific HTTP 500 error.
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {e}")


@app.post("/get-llm-recommendation")
def get_llm_recommendation(req: LLMRequest):
    """
    Takes data for a single query and gets a detailed recommendation from an LLM.
    """
    recommendation = get_llm_recommendation_for_query(req.dict())
    return recommendation

@app.post("/generate-sample")
def gen_sample():
    generate_csv()
    return {"detail": "generated examples/sample_logs.csv"}

@app.get("/")
def root():
    return {"message": "Welcome to DB Profiler API"}

