# app/api.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
from typing import List, Optional,Dict,Any
from dotenv import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()

# --- Import your project modules ---
from .features import extract_features
from .analyzer import Analyzer
from .generator import generate_csv
from .ai_chatbot import get_chatbot_response

app = FastAPI()
analyzer = Analyzer()

# --- Pydantic Models for structured requests ---
class AnalyzeRequest(BaseModel):
    csv_path: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]
    question: str
    context_data: str

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

        # Convert Timestamp objects to JSON-compatible strings
        df_with_features['timestamp'] = df_with_features['timestamp'].astype(str)

        # Convert DataFrame to a list of dicts for a clean JSON response
        json_content = df_with_features.to_dict(orient='records')
        return JSONResponse(content=json_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {e}")

@app.post("/chat-with-assistant")
def chat_with_assistant(req: ChatRequest):
    """
    Handles a conversational turn with the AI chatbot assistant.
    """
    response_text = get_chatbot_response(
        chat_history=[msg.dict() for msg in req.history],
        question=req.question,
        context_data=req.context_data
    )
    return {"role": "assistant", "content": response_text}

@app.post("/generate-sample")
def gen_sample():
    generate_csv()
    return {"detail": "generated examples/sample_logs.csv"}

@app.get("/")
def root():
    return {"message": "Welcome to DB Profiler API"}

