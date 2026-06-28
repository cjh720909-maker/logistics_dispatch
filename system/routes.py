from flask import Blueprint
from flask import render_template
from flask import request
from system.sync import sync_product
from flask import redirect
from flask import url_for

from system.service import (
    run_safe_sql,
    run_local_sql,
    get_local_db_info,
)

from system.sync import (
    sync_product,
    sync_customer,
    sync_delivery,
    sync_vehicle,
    get_sync_status,
)

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

@system_bp.route("/db_sync_920")
def db_sync_920():
    return render_template(
        "db_sync.html",
        sync_status=get_sync_status(),
    )

@system_bp.route("/sync_product_920", methods=["POST"])
def sync_product_920():
    result = sync_product()

    return render_template(
        "db_sync.html",
        product_sync_result=result,
        sync_status=get_sync_status(),
    )

@system_bp.route("/sync_customer_920", methods=["POST"])
def sync_customer_920():
    result = sync_customer()

    return render_template(
        "db_sync.html",
        customer_sync_result=result,
        sync_status=get_sync_status(),
    )

@system_bp.route("/sync_delivery_920", methods=["POST"])
def sync_delivery_920():
    result = sync_delivery()

    return render_template(
        "db_sync.html",
        delivery_sync_result=result,
        sync_status=get_sync_status(),
    )

@system_bp.route("/sync_vehicle_920", methods=["POST"])
def sync_vehicle_920():
    result = sync_vehicle()

    return render_template(
        "db_sync.html",
        vehicle_sync_result=result,
        sync_status=get_sync_status(),
    )

@system_bp.route("/local_sql_911", methods=["GET", "POST"])
def local_sql_911():
    sql_text = ""
    executed_sql = ""
    columns = []
    rows = []
    error_message = ""

    if request.method == "POST":
        sql_text = request.form.get("sql_text", "")

        try:
            columns, rows, executed_sql, error_message = run_local_sql(sql_text)
        except Exception as e:
            error_message = str(e)

    return render_template(
        "local_sql.html",
        sql_text=sql_text,
        executed_sql=executed_sql,
        columns=columns,
        rows=rows,
        error_message=error_message,
        local_db_info=get_local_db_info(),
    )