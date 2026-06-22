from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify

from services.balju_service import (
    get_dispatch_summary_by_date,
    get_customer_list_by_driver,
    get_dispatch_total,
    get_customer_orders,
)

dispatch_bp = Blueprint(
    "dispatch",
    __name__
)


@dispatch_bp.route("/")
def index():
    return dispatch()


@dispatch_bp.route("/dispatch")
def dispatch():
    selected_date = request.args.get("date", "2026-06-12")
    selected_driver = request.args.get("driver")

    dispatch_list = get_dispatch_summary_by_date(selected_date)
    dispatch_total = get_dispatch_total(dispatch_list)
    customers = get_customer_list_by_driver(
        selected_date,
        selected_driver
    )

    total_data = get_dispatch_total(dispatch_list)

    return render_template(
        "dispatch.html",
        dispatch_list=dispatch_list,
        customers=customers,
        dispatch_total=dispatch_total,
        selected_date=selected_date,
        selected_driver=selected_driver
    )

@dispatch_bp.route("/api/customer-orders")
def api_customer_orders():
    selected_date = request.args.get("date")
    driver = request.args.get("driver")
    customer_name = request.args.get("customer_name")
    customer_address = request.args.get("customer_address")

    orders = get_customer_orders(
        selected_date,
        driver,
        customer_name,
        customer_address
    )

    return jsonify(orders)
