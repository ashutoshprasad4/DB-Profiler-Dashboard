# app/dashboard.py
import streamlit as st
import pandas as pd
import requests
import json
import re
from io import StringIO

API_URL = "http://localhost:8000"

st.set_page_config(page_title="DB Profiler Dashboard", layout="wide")
st.title("📊 DB Profiler Dashboard")

# Initialize analyzed data in session_state
if "analyzed_df" not in st.session_state:
    st.session_state.analyzed_df = None

# --- Sidebar Actions ---
st.sidebar.header("Configuration")
csv_path = st.sidebar.text_input("CSV Path", "examples/sample_logs.csv")

# --- NEW: Database Dialect Selector ---
db_dialect = st.sidebar.selectbox(
    "Select Database Dialect",
    ("PostgreSQL", "MySQL"),
    help="Select the SQL dialect your logs are from. This helps the AI provide accurate recommendations."
)

st.sidebar.header("Actions")
if st.sidebar.button("▶️ Run Full Analysis", type="primary"):
    with st.spinner("Running analysis... this may take a moment."):
        try:
            resp = requests.post(f"{API_URL}/analyze", json={"csv_path": csv_path})
            if resp.status_code == 200:
                st.session_state.analyzed_df = pd.read_json(StringIO(resp.text))
                st.toast(f"✅ Analysis complete for {len(st.session_state.analyzed_df)} rows")
            else:
                st.error(f"❌ API error: {resp.status_code} {resp.text}")
                st.session_state.analyzed_df = None
        except Exception as e:
            st.error(f"Failed to call API: {e}")
            st.session_state.analyzed_df = None

# --- Main Display Area (Largely unchanged) ---
if st.session_state.analyzed_df is not None:
    df = st.session_state.analyzed_df
    # ... (The entire middle section of your dashboard remains the same)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    st.header("📋 Analysis Report")
    time_col = "execution_time"
    st.subheader("Performance Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Avg. Query Speed (ms)", round(df[time_col].mean(), 2), help="This is the average time a query takes to complete. Lower is better.")
        st.metric("Slowest Query Time (ms)", round(df[time_col].max(), 2), help="This is the time taken by the single slowest query in the log.")
    with col2:
        st.metric("Avg. Rows Scanned", f"{round(df['rows_examined'].mean()):,}", help="On average, this is how many database rows a query has to look at. A high number can indicate inefficiency.")
        st.metric("Max. Rows Scanned", f"{round(df['rows_examined'].max()):,}", help="This is the highest number of rows any single query had to scan. Very high numbers often point to a problem.")
    st.subheader("How Quickly Queries are Responding")
    st.bar_chart(df, x="query_id", y=time_col)
    st.subheader("Queries Requiring Attention")
    def translate_reason_to_plain_english(reasons_list):
        if not reasons_list: return "This query appears to be running efficiently."
        translations = {"Large rows examined + high exec time -> possible missing index or full scan": "This query is slow because it has to search through a huge number of database rows, like looking for a name in a phone book without an index.", "Expensive join detected — check join keys and indexes": "This query combines data from multiple large tables inefficiently. This can often be fixed by improving how the tables are linked."}
        plain_english_reasons = [translations.get(r, r) for r in reasons_list]
        return " ".join(plain_english_reasons)
    slowest = df.sort_values(time_col, ascending=False).head(10).copy()
    slowest['Initial Diagnosis'] = slowest['reasons'].apply(translate_reason_to_plain_english)
    st.table(slowest[["query_id", "query", time_col, "Initial Diagnosis"]])
    st.markdown("---")
    st.header("🔍 Deeper Analysis")
    st.subheader("Query Efficiency: Speed vs. Work Done")
    st.write("This chart helps find inefficient queries. A query in the top-right corner is both slow and scans a lot of data, making it a primary target for optimization.")
    if 'anomaly' in df.columns:
        df['color'] = df['anomaly'].apply(lambda x: '#FF4B4B' if x else '#0068C9')
        st.scatter_chart(df, x='rows_examined', y=time_col, color='color')
    else:
        st.scatter_chart(df, x='rows_examined', y=time_col)
    st.subheader("Performance Trends Over Time")
    st.write("This chart shows when your queries are running and can help you spot performance issues that happen at specific times of the day.")
    time_series_df = df.sort_values(by='timestamp')
    st.line_chart(time_series_df, x='timestamp', y=time_col)
    st.subheader("Analysis by Query Type")
    st.write("Understanding which types of queries are most common or slowest can guide optimization efforts.")
    def classify_query(row):
        if row.get('is_join', False): return 'JOIN Query'
        elif row.get('is_select', False): return 'Simple SELECT'
        return 'Other'
    if 'is_join' in df.columns and 'is_select' in df.columns:
        df['query_type'] = df.apply(classify_query, axis=1)
        type_analysis = df.groupby('query_type').agg(count=('query_id', 'count'), avg_speed_ms=(time_col, 'mean'), avg_rows_scanned=('rows_examined', 'mean')).reset_index()
        st.table(type_analysis.style.format({"avg_speed_ms": "{:.2f}", "avg_rows_scanned": "{:,.0f}"}))

# --- Interactive AI Assistant ---
st.markdown("---")
st.header("🤖 Interactive AI Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"Hi! I'm ready to help you analyze your {db_dialect} queries. How can I assist?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # --- NEW: Check for a simulation trigger in the AI's response ---
        if message["role"] == "assistant":
            sim_match = re.search(r"SIMULATE_INDEX:\s*({.*})", message["content"])
            if sim_match:
                sim_data = json.loads(sim_match.group(1))
                query_id = sim_data.get("query_id")
                table = sim_data.get("table")
                column = sim_data.get("column")
                if st.button(f"Simulate Index on `{table}.{column}` for Query {query_id}", key=f"sim_{query_id}"):
                    with st.spinner("Running simulation..."):
                        sim_payload = {"db_dialect": db_dialect, "query_id": query_id, "table": table, "column": column, "csv_path": csv_path}
                        try:
                            resp = requests.post(f"{API_URL}/simulate-recommendation", json=sim_payload)
                            if resp.status_code == 200:
                                st.success("Simulation successful!")
                                st.json(resp.json())
                            else:
                                st.error(f"Simulation API Error: {resp.status_code} - {resp.text}")
                        except Exception as e:
                            st.error(f"Failed to call simulation API: {e}")

if st.session_state.analyzed_df is not None:
    df = st.session_state.analyzed_df
    if prompt := st.chat_input("Ask about your queries..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                context_df = pd.DataFrame()
                match = re.search(r'Q(\d+)', prompt, re.IGNORECASE)
                if match:
                    query_id = f"Q{match.group(1)}"
                    context_df = df[df['query_id'] == query_id]
                elif "slowest" in prompt.lower():
                    context_df = df.sort_values("execution_time", ascending=False).head(1)
                else:
                    summary_df = df.sort_values("execution_time", ascending=False).head(5)
                    context_df = summary_df[['query_id', 'query', 'execution_time', 'rows_examined', 'reasons']]
                context_json = context_df.to_json(orient='records') if not context_df.empty else "{}"
                
                # --- Pass the selected DB dialect to the chat API ---
                payload = {"history": st.session_state.messages[:-1], "question": prompt, "context_data": context_json, "db_dialect": db_dialect}
                
                try:
                    resp = requests.post(f"{API_URL}/chat-with-assistant", json=payload)
                    if resp.status_code == 200:
                        response_data = resp.json()
                        response_content = response_data.get("content", "Sorry, I couldn't get a response.")
                    else:
                        response_content = f"API Error: {resp.status_code} - {resp.text}"
                except Exception as e:
                    response_content = f"Failed to call API: {e}"
                
                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})
else:
    st.info("Run an analysis to activate the interactive AI assistant.")

