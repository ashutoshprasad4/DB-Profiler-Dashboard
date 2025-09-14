# DB Profiler - Proof of concept

## Setup
1. Create and activate virtualenv
   python -m venv .venv
   source .venv/bin/activate

2. Install deps
   pip install -r requirements.txt

3. Generate synthetic logs
   python -m app.generator

4. Run analyzer API
   uvicorn app.api:app --reload --port 8000

5. Analyze logs (POST /analyze)
   curl -X POST "http://localhost:8000/analyze" -H "Content-Type: application/json" -d '{"csv_path":"examples/sample_logs.csv"}'

6. Query why a specific query is slow (conversational endpoint):
   GET /why/Q1?csv_path=examples/sample_logs.csv

## Postgres simulation
Set environment variables PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASS to point to a sandbox DB.
Use app.simulator.simulate_add_index_and_explain(table, column, sql) to simulate index creation and collect EXPLAIN ANALYZE.

## Next steps / improvements
- Add parser & plan analyzer for Postgres EXPLAIN JSON
- Implement learned cost model (train regressor on observed exec_time / plan features)
- Add non-blocking simulator (run in ephemeral docker DB) for safe testing
- Build dashboard (Grafana/React) that consumes API
- Implement conversational interface with an LLM (pass the explainability data as context)
