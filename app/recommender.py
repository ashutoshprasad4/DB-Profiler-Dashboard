# app/recommender.py
from typing import List, Dict
import re

def suggest_index_from_query(normalized_sql: str) -> List[Dict]:
    """
    Basic heuristic:
      - find WHERE clauses and equality conditions to propose indexing those columns.
      - find JOIN ... ON patterns to propose indexes on join columns.
    """
    suggestions = []
    s = normalized_sql.upper()
    # simple find WHERE ... <col> = ?
    where_cols = []
    m = re.search(r"WHERE\s+(.+)", s)
    if m:
        cond = m.group(1)
        # split on AND/OR
        conds = re.split(r"\s+AND\s+|\s+OR\s+", cond)
        for c in conds:
            eq = re.search(r"([A-Z0-9_\.]+)\s*=\s*\?", c)
            if eq:
                col = eq.group(1)
                where_cols.append(col)
    # find JOIN ON col equality
    join_cols = re.findall(r"ON\s+([A-Z0-9_\.]+)\s*=\s*([A-Z0-9_\.]+)", s)
    # Build suggestions
    for c in where_cols:
        suggestions.append({"type": "create_index", "column": c, "reason": "where_filter"})
    for a,b in join_cols:
        suggestions.append({"type": "create_index", "column": a, "reason": "join_key"})
        suggestions.append({"type": "create_index", "column": b, "reason": "join_key"})
    # unique filter: collapse duplicates
    seen = set()
    uniq = []
    for s in suggestions:
        key = (s['type'], s['column'])
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    return uniq

def recommend(df_row) -> Dict:
    # df_row is a pd.Series with normalized/fingerprint data
    recs = []
    # if anomaly or reasons suggest missing index => propose index
    if df_row.get('anomaly', False) or (df_row.get('reasons') and len(df_row['reasons'])>0):
        recs.extend(suggest_index_from_query(df_row['normalized']))
    # propose query rewrite if non-sargable patterns (a simple detection)
    if "LIKE '%" in df_row['normalized'].upper():
        recs.append({"type":"rewrite_query","suggestion":"avoid leading wildcard in LIKE; add trigram index or explicit full text index"})
    return {"query_id": df_row['query_id'], "recs": recs, "explain": df_row.get('reasons', [])}
