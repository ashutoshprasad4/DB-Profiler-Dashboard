# app/parser.py
import sqlparse
import hashlib

def normalize_sql(sql_text: str) -> str:
    # Use sqlparse to canonicalize formatting, remove literals
    parsed = sqlparse.format(sql_text, reindent=False, keyword_case='upper', strip_comments=True)
    # naive literal removal: replace numbers and strings with placeholder
    import re
    parsed = re.sub(r"\'[^\']*\'", "'?'", parsed)
    parsed = re.sub(r"\b\d+\b", "?", parsed)
    return parsed.strip()

def fingerprint(sql_text: str) -> str:
    n = normalize_sql(sql_text)
    h = hashlib.md5(n.encode()).hexdigest()
    return h

if __name__ == "__main__":
    s = "select * from users where id = 123"
    print(normalize_sql(s), fingerprint(s))
