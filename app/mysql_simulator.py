# app/mysql_simulator.py
import mysql.connector
import os
from contextlib import contextmanager
import json

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))
DB_NAME = os.getenv("MYSQL_DB", "testdb")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("MYSQL_PASS", "password")

@contextmanager
def get_conn():
    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
    )
    try:
        yield conn
    finally:
        conn.close()

def get_explain_plan(sql: str, conn):
    with conn.cursor(dictionary=True) as cur:
        # MySQL's EXPLAIN format is different; using JSON format is best
        cur.execute("EXPLAIN FORMAT=JSON " + sql)
        result = cur.fetchone()
        # The result is a string that needs to be parsed
        return json.loads(result['EXPLAIN'])

def simulate_add_index_and_explain(table: str, column: str, sql: str):
    idx_name = f"tmp_idx_{table}_{column}".lower()
    create_idx = f"CREATE INDEX {idx_name} ON {table} ({column});"
    drop_idx = f"DROP INDEX {idx_name} ON {table};"
    result = {}
    
    with get_conn() as conn:
        # Get baseline plan
        result['plan_before'] = get_explain_plan(sql, conn)
        
        with conn.cursor() as cur:
            try:
                cur.execute(create_idx)
                cur.execute(f"ANALYZE TABLE {table};")
                # Get plan with the new index
                result['plan_after'] = get_explain_plan(sql, conn)
            finally:
                # Always drop the temporary index
                cur.execute(drop_idx)
                
    return result
