from flask import Blueprint
from flask import render_template
from flask import request

from system.service import run_safe_sql


system_bp = Blueprint(
    "system",
    __name__,
    template_folder="templates"
)


@system_bp.route("/sql_query_910", methods=["GET", "POST"])
def sql_query_910():
    sql_text = ""
    executed_sql = ""
    columns = []
    rows = []
    error_message = ""
    auto_limit = True

    if request.method == "POST":
        sql_text = request.form.get("sql_text", "")
        auto_limit = request.form.get("auto_limit") == "1"

        columns, rows, executed_sql, error_message = run_safe_sql(
            sql_text,
            auto_limit
        )

    return render_template(
        "sql_query.html",
        sql_text=sql_text,
        executed_sql=executed_sql,
        columns=columns,
        rows=rows,
        error_message=error_message,
        auto_limit=auto_limit,
    )