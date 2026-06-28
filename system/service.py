import re
import os

from datetime import datetime
from db import engine
from utils.encoding import fix_row
from db_local import local_engine
from decimal import Decimal


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

def to_float(value):
    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    return value

def run_local_sql(sql_text):
    sql = (sql_text or "").strip()

    if not sql:
        return [], [], "", "SQL을 입력하세요."

    with local_engine.begin() as conn:

        result = conn.exec_driver_sql(sql)

        if not result.returns_rows:
            return [], [], sql, "실행 완료"

        rows = [
            dict(row)
            for row in result.mappings().all()
        ]

        columns = list(rows[0].keys()) if rows else []

        return columns, rows, sql, ""

def get_local_db_info():
    db_path = "data/local.db"

    file_size = 0
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)

    table_counts = {}

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        )

        tables = [row["name"] for row in result.mappings().all()]

        for table in tables:
            count_result = conn.exec_driver_sql(
                f"SELECT COUNT(*) AS count FROM {table}"
            ).mappings().first()

            table_counts[table] = count_result["count"]

    return {
        "db_path": db_path,
        "file_size_mb": round(file_size / 1024 / 1024, 2),
        "table_counts": table_counts,
    }        