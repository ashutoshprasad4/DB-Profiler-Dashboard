# app/api.py
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
from .collector import collect_from_csv
from .features import extract_features
from .analyzer import Analyzer
from .recommender import recommend
from .generator import generate_csv

app = FastAPI()

analyzer = Analyzer()

class AnalyzeRequest(BaseModel):
    csv_path: str

@app.post("/generate-sample")
def gen_sample():
    generate_csv()
    return {"detail": "generated examples/sample_logs.csv"}

@app.post("/analyze")
def analyze(csv_path: str = "examples/sample_logs.csv"):
    df = pd.read_csv(csv_path)

    # ✅ Normalize column names for consistency
    if "exec_time_ms" in df.columns and "execution_time" not in df.columns:
        df = df.rename(columns={"exec_time_ms": "execution_time"})

    has_exec_time = "execution_time" in df.columns
    has_query = "query" in df.columns

    # Pick correct time column
    time_col = "exec_time_ms" if "exec_time_ms" in df.columns else "execution_time"

    def make_recommendation(row):
        if row[time_col] > 100:
            return "Query is slow; consider adding an index."
        elif "SELECT *" in row["query"]:
            return "Avoid SELECT *; specify required columns."
        else:
            return "Query performance is acceptable."

    df["recommendations"] = df.apply(make_recommendation, axis=1)

    # Save normalized data back (with execution_time column)
    df.to_csv(csv_path, index=False)

    return {
        "status": "success",
        "message": "Analysis complete. Recommendations added.",
        "rows_analyzed": len(df),
        "columns": list(df.columns)  # for debugging
    }



@app.get("/why/{query_id}")
def why_is_query_slow(query_id: str, csv_path: str = Query(...)):
    try:
        df = pd.read_csv(csv_path)

        # Normalize column names if needed
        if "exec_time_ms" in df.columns:
            time_col = "exec_time_ms"
        elif "execution_time" in df.columns:
            time_col = "execution_time"
        else:
            return JSONResponse(
                status_code=400,
                content={"reason": "CSV missing exec_time_ms or execution_time column"}
            )

        # Check if query_id exists
        row = df[df["query_id"] == query_id]
        if row.empty:
            return {"reason": f"Query ID {query_id} not found in logs."}

        exec_time = row.iloc[0][time_col]
        rows_examined = row.iloc[0]["rows_examined"]
        query_text = row.iloc[0]["query"]

        # Basic heuristic explanation
        if exec_time > 1000 or rows_examined > 5000:
            reason = "Query is slow; consider adding an index."
        else:
            reason = "Query performance is acceptable."

        return {
            "query_id": query_id,
            "query": query_text,
            "exec_time": float(exec_time),
            "rows_examined": int(rows_examined),
            "reason": reason,
        }

    except Exception as e:
        # Always return JSON error instead of crashing
        return JSONResponse(
            status_code=500,
            content={"reason": f"Internal error: {str(e)}"}
        )

@app.get("/")
def root():
    return {"message": "Welcome to AI-Powered DB Profiler API"}

@app.get("/favicon.ico")
def favicon():
    return {}
