# app/dashboard.py
import streamlit as st
import pandas as pd
import requests
import json
from io import StringIO # <-- 1. Import StringIO

API_URL = "http://localhost:8000"

st.set_page_config(page_title="DB Profiler Dashboard", layout="wide")
st.title("📊 DB Profiler Dashboard")

# Initialize analyzed data in session_state
if "analyzed_df" not in st.session_state:
    st.session_state.analyzed_df = None

# --- Sidebar Actions ---
st.sidebar.header("Actions")
csv_path = st.sidebar.text_input("CSV Path", "examples/sample_logs.csv")

if st.sidebar.button("▶️ Run Analysis", type="primary"):
    with st.spinner("Running analysis... this may take a moment."):
        try:
            resp = requests.post(f"{API_URL}/analyze", json={"csv_path": csv_path})
            if resp.status_code == 200:
                # --- 2. FIX: Wrap the response text in StringIO to resolve the warning ---
                st.session_state.analyzed_df = pd.read_json(StringIO(resp.text))
                st.toast(f"✅ Analysis complete for {len(st.session_state.analyzed_df)} rows")
            else:
                st.error(f"❌ API error: {resp.status_code} {resp.text}")
                st.session_state.analyzed_df = None
        except Exception as e:
            st.error(f"Failed to call API: {e}")
            st.session_state.analyzed_df = None

# --- Main Display Area ---
if st.session_state.analyzed_df is not None:
    df = st.session_state.analyzed_df
    
    st.header("📋 Analysis Results")
    time_col = "execution_time"

    st.subheader("Summary Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Avg Exec Time (ms)", round(df[time_col].mean(), 2))
        st.metric("Max Exec Time (ms)", round(df[time_col].max(), 2))
    with col2:
        st.metric("Avg Rows Examined", round(df["rows_examined"].mean(), 2))
        st.metric("Max Rows Examined", round(df["rows_examined"].max(), 2))

    st.subheader("Execution Time Distribution")
    st.bar_chart(df, x="query_id", y=time_col)

    st.subheader("Top 10 Slowest Queries & Heuristic Findings")
    slowest = df.sort_values(time_col, ascending=False).head(10).copy()
    
    slowest['Heuristic Findings'] = slowest['reasons'].apply(lambda x: "; ".join(x) if x else "N/A")
    st.table(slowest[["query_id", "query", time_col, "rows_examined", "Heuristic Findings"]])

    # --- On-Demand LLM Recommendation Assistant ---
    st.markdown("---")
    st.header("🤖 AI Recommendation Assistant")
    
    query_id = st.selectbox("Select a Query ID for AI-powered advice:", df["query_id"].unique())
    
    if st.button("Get AI Recommendation", key=f"llm_btn_{query_id}"):
        with st.spinner("Asking the AI for recommendations..."):
            row = df[df["query_id"] == query_id].iloc[0]
            
            payload = {
                "query": row["query"],
                "execution_time": row["execution_time"],
                "rows_examined": int(row["rows_examined"]),
                "reasons": row["reasons"]
            }
            
            try:
                resp = requests.post(f"{API_URL}/get-llm-recommendation", json=payload)
                if resp.status_code == 200:
                    st.info(f"**AI Recommendation for {query_id}:**")
                    st.markdown(resp.json().get("reason", "No recommendation available."))
                else:
                    st.error(f"API Error: {resp.status_code} - {resp.text}")
            except Exception as e:
                st.error(f"Failed to call API: {e}")
else:
    st.info("Click 'Run Analysis' in the sidebar to process your query log file.")

