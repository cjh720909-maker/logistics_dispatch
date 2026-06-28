import re

from db import engine
from utils.encoding import fix_row


ALLOWED_SQL_PREFIXES = (
    "select",
    "show",
    "describe",
    "desc",
)


BLOCKED_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
)


def has_limit(sql_lower):
    return re.search(r"\blimit\b", sql_lower) is not None


def run_safe_sql(sql_text, auto_limit=True):
    sql = (sql_text or "").strip()

    if not sql:
        return [], [], "", "SQL을 입력하세요."

    sql_lower = sql.lower()

    if not sql_lower.startswith(ALLOWED_SQL_PREFIXES):
        return [], [], sql, "SELECT, SHOW, DESCRIBE, DESC만 실행할 수 있습니다."

    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", sql_lower):
            return [], [], sql, f"금지된 SQL 키워드가 포함되어 있습니다: {keyword}"

    executed_sql = sql

    if auto_limit and sql_lower.startswith("select") and not has_limit(sql_lower):
        executed_sql = sql.rstrip(";") + " LIMIT 500"

    with engine.connect() as conn:
        result = conn.exec_driver_sql(executed_sql)

        rows = [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

        columns = list(rows[0].keys()) if rows else []

        return columns, rows, executed_sql, ""