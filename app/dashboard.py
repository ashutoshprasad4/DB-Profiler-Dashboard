# app/dashboard.py
import streamlit as st
import pandas as pd
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="DB Profiler Dashboard", layout="wide")
st.title("📊 DB Profiler Dashboard")

# --- CHANGE 1: Initialize df in session_state ---
# This ensures our DataFrame persists across button clicks
if "df" not in st.session_state:
    st.session_state.df = None

# Sidebar: file input
csv_path = st.sidebar.text_input("CSV Path", "examples/sample_logs.csv")

# Button to trigger analysis via API
if st.sidebar.button("Run Analysis"):
    try:
        resp = requests.post(f"{API_URL}/analyze", json={"csv_path": csv_path})
        if resp.status_code == 200:
            data = resp.json()
            st.success(f"✅ Analysis complete: {data['rows_analyzed']} rows processed")
        else:
            st.error(f"❌ API error: {resp.status_code} {resp.text}")
    except Exception as e:
        st.error(f"Failed to call API: {e}")

# Load CSV after analysis
if st.sidebar.button("Load Data"):
    try:
        # --- CHANGE 2: Assign to session_state.df, not a local df ---
        st.session_state.df = pd.read_csv(csv_path)
        df = st.session_state.df # For convenience, you can still use a local var
        
        # Normalize column names
        if "exec_time_ms" in df.columns:
            df.rename(columns={"exec_time_ms": "execution_time"}, inplace=True)
        st.success(f"Loaded {len(df)} rows from {csv_path}")
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.session_state.df = None # Reset on failure

# --- CHANGE 3: Check session_state.df for all subsequent logic ---
if st.session_state.df is not None:
    df = st.session_state.df # Use a local variable for cleaner code
    
    # Check for required time column
    time_col = ""
    if "execution_time" in df.columns:
        time_col = "execution_time"
    elif "exec_time_ms" in df.columns:
        time_col = "exec_time_ms" # Should be renamed but as a fallback
    else:
        st.error("CSV must have either 'exec_time_ms' or 'execution_time' column")
        st.stop() # Stop execution if column is missing

    # Show raw data
    st.subheader("Raw Query Logs")
    st.dataframe(df.head(20))

    # Summary stats
    st.subheader("Summary Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Avg Exec Time (ms)", round(df[time_col].mean(), 2))
        st.metric("Max Exec Time (ms)", round(df[time_col].max(), 2))
    with col2:
        st.metric("Avg Rows Examined", round(df["rows_examined"].mean(), 2))
        st.metric("Max Rows Examined", round(df["rows_examined"].max(), 2))

    # Histogram
    st.subheader("Execution Time Distribution")
    st.bar_chart(df[time_col])

    # Top 10 slowest
    st.subheader("Top 10 Slowest Queries")
    slowest = df.sort_values(time_col, ascending=False).head(10)
    st.table(slowest[["query_id", "query", time_col, "rows_examined", "recommendations"]])

# Conversational panel: Why is query slow?
st.subheader("🤖 Why is query slow?")

# Initialize session_state keys for explanation
if "explanation" not in st.session_state:
    st.session_state.explanation = None
if "query_id_for_explanation" not in st.session_state:
    st.session_state.query_id_for_explanation = None

# Also check session_state.df here
if st.session_state.df is not None:
    df = st.session_state.df # Get the persistent dataframe
    query_id = st.selectbox("Select a Query ID", df["query_id"].unique())

    if st.button("Explain"):
        try:
            resp = requests.get(f"{API_URL}/why/{query_id}", params={"csv_path": csv_path})
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    st.session_state.explanation = data.get("reason", "No explanation available.")
                except Exception as json_err:
                    st.session_state.explanation = f"⚠️ Failed to parse JSON: {json_err}. Raw response: {resp.text}"
            else:
                st.session_state.explanation = f"❌ API error: {resp.status_code}. Response: {resp.text}"
        except Exception as e:
            st.session_state.explanation = f"⚠️ Failed to call API: {e}"
        
        # Always store which query was explained
        st.session_state.query_id_for_explanation = query_id

# Display logic is now outside the main "if df is not None" block
# It relies only on session_state, which is always available.
if st.session_state.explanation:
    st.markdown(f"**Explanation for Query {st.session_state.query_id_for_explanation}:**")
    st.info(st.session_state.explanation)