# app/generator.py
import random
import time
import csv
from datetime import datetime, timedelta

QUERIES = [
    ("SELECT * FROM users WHERE id = %s", ["int"]),
    ("SELECT name FROM users WHERE email = %s", ["text"]),
    ("SELECT * FROM orders WHERE created_at >= %s", ["date"]),
    ("SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id WHERE o.total > %s", ["float"]),
    ("SELECT COUNT(*) FROM big_table WHERE status = %s", ["text"])
]

def generate_row(qid):
    qtpl, _ = random.choice(QUERIES)
    qtext = qtpl % (random.randint(1, 1000) if "%s" in qtpl else "")
    # simulate execution time in ms and rows_examined
    base = random.uniform(5, 200)
    if "big_table" in qtext or "orders" in qtext and random.random() < 0.3:
        base *= 10
    rows = int(base * random.uniform(1, 10))
    ts = (datetime.utcnow() - timedelta(seconds=random.randint(0, 3600))).isoformat()
    return {
        "query_id": f"Q{qid}",
        "query": qtext,
        "timestamp": ts,
        "exec_time_ms": round(base + random.uniform(-base*0.2, base*0.2), 2),
        "rows_examined": rows
    }

def generate_csv(path="examples/sample_logs.csv", n=500):
    rows = [generate_row(i) for i in range(n)]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["query_id","query","timestamp","exec_time_ms","rows_examined"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

if __name__ == "__main__":
    generate_csv()
    print("Generated examples/sample_logs.csv")
