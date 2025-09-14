# app/postgres_simulator.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager

DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = int(os.getenv("PG_PORT", 5432))
DB_NAME = os.getenv("PG_DB", "postgres")
DB_USER = os.getenv("PG_USER", "postgres")
DB_PASS = os.getenv("PG_PASS", "postgres")

@contextmanager
def get_conn():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    try:
        yield conn
    finally:
        conn.close()

def get_explain_plan(sql: str, conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql)
        return cur.fetchone()

def simulate_add_index_and_explain(table: str, column: str, sql: str):
    idx_name = f"tmp_idx_{table}_{column}".lower().replace('.', '_')
    # Using format for dynamic SQL is okay here as inputs are controlled
    create_idx = f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx_name} ON {table} ({column});"
    drop_idx = f"DROP INDEX IF EXISTS {idx_name};"
    result = {}
    
    with get_conn() as conn:
        conn.autocommit = True # autocommit for DDL
        # Get baseline plan
        result['plan_before'] = get_explain_plan(sql, conn)
        
        with conn.cursor() as cur:
            try:
                cur.execute(create_idx)
                cur.execute(f"ANALYZE {table};")
                # Get plan with the new index
                result['plan_after'] = get_explain_plan(sql, conn)
            finally:
                # Always drop the temporary index
                cur.execute(drop_idx)
                
    return result
