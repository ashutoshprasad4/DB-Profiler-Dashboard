# app/simulator.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager

DB_HOST = os.getenv("PG_HOST","localhost")
DB_PORT = int(os.getenv("PG_PORT", 5432))
DB_NAME = os.getenv("PG_DB","postgres")
DB_USER = os.getenv("PG_USER","postgres")
DB_PASS = os.getenv("PG_PASS","postgres")

@contextmanager
def get_conn():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    try:
        yield conn
    finally:
        conn.close()

def explain_query(sql: str) -> dict:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # run EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql)
        res = cur.fetchone()
        return res

def simulate_add_index_and_explain(table: str, column: str, sql: str):
    idx_name = f"tmp_idx_{table}_{column}".lower().replace('.','_')
    create_idx = f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx_name} ON {table} ({column});"
    drop_idx = f"DROP INDEX IF EXISTS {idx_name};"
    result = {}
    with get_conn() as conn:
        conn.autocommit = True
        cur = conn.cursor()
        try:
            cur.execute(create_idx)
            # Let DB update planner stats; optionally run ANALYZE table
            cur.execute(f"ANALYZE {table};")
            cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql)
            plan_with_idx = cur.fetchone()[0]
            result['with_index'] = plan_with_idx
        finally:
            cur.execute(drop_idx)
    return result
