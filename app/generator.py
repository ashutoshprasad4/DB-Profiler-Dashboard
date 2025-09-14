import random
import time
import csv
from datetime import datetime, timedelta
import argparse

# --- NEW: Separate query templates for different SQL dialects ---

POSTGRES_QUERIES = [
    ("SELECT * FROM users WHERE user_id = %s", ["int"]),
    ("SELECT user_name, email FROM users WHERE email ILIKE %s", ["text"]), # PostgreSQL specific ILIKE
    ("SELECT * FROM orders WHERE order_date >= %s AND status = 'shipped'", ["date"]),
    ("SELECT u.user_name, o.total FROM users u JOIN orders o ON u.user_id = o.user_id WHERE o.total > %s", ["float"]),
    ("SELECT COUNT(*) FROM event_logs WHERE event_type = %s AND timestamp > NOW() - INTERVAL '1 hour'", ["text"]) # PostgreSQL interval syntax
]

MYSQL_QUERIES = [
    ("SELECT * FROM `users` WHERE `id` = %s", ["int"]), # MySQL specific backticks
    ("SELECT `name` FROM `users` WHERE `email` LIKE %s", ["text"]),
    ("SELECT * FROM `orders` WHERE `created_at` >= %s AND `status` = 'completed'", ["date"]),
    ("SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id WHERE o.total > %s", ["float"]),
    ("SELECT COUNT(*) FROM `log_table` WHERE `level` = %s AND `ts` > DATE_SUB(NOW(), INTERVAL 1 HOUR)", ["text"]) # MySQL date function
]

def generate_row(qid, dialect='postgres'):
    """Generates a single log row for a specific SQL dialect."""
    if dialect == 'mysql':
        queries = MYSQL_QUERIES
    else: # Default to PostgreSQL
        queries = POSTGRES_QUERIES

    qtpl, _ = random.choice(queries)
    
    # Use different placeholders for different query types
    if "%s" in qtpl and "ILIKE" in qtpl.upper():
         param = f"'%%{random.choice(['test', 'user', 'prod', 'dev'])}%%'"
    elif "%s" in qtpl:
        param = random.randint(1, 10000)
    else:
        param = ""
        
    qtext = qtpl % param

    # Simulate execution time and rows_examined
    base = random.uniform(5, 200)
    if "JOIN" in qtext or "COUNT" in qtext and random.random() < 0.3:
        base *= 15 # Make joins and counts more expensive
    rows = int(base * random.uniform(1, 20))
    ts = (datetime.utcnow() - timedelta(seconds=random.randint(0, 7200))).isoformat()
    
    return {
        "query_id": f"Q{qid}",
        "query": qtext,
        "timestamp": ts,
        "exec_time_ms": round(base + random.uniform(-base*0.1, base*0.1), 2),
        "rows_examined": rows
    }

def generate_csv(path="examples/sample_logs.csv", n=500, dialect='postgres'):
    """Generates a CSV log file with dialect-specific queries."""
    rows = [generate_row(i, dialect) for i in range(n)]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["query_id", "query", "timestamp", "exec_time_ms", "rows_examined"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

if __name__ == "__main__":
    # --- NEW: Allow choosing dialect from the command line ---
    parser = argparse.ArgumentParser(description="Generate synthetic database query logs.")
    parser.add_argument(
        "--dialect", 
        type=str, 
        default="postgres", 
        choices=["postgres", "mysql"],
        help="The SQL dialect to generate queries for."
    )
    args = parser.parse_args()

    generate_csv(dialect=args.dialect)
    print(f"✅ Generated examples/sample_logs.csv with {args.dialect.capitalize()} queries.")

