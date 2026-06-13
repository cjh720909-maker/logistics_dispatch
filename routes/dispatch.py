from flask import Blueprint
from flask import render_template
from flask import request

from services.balju_service import (
    get_dispatch_summary_by_date,
    get_customer_list_by_vehicle_key,
    get_dispatch_total,
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
    selected_vehicle_key = request.args.get("vehicle_key")

    dispatch_list = get_dispatch_summary_by_date(selected_date)
    dispatch_total = get_dispatch_total(dispatch_list)
    customers = get_customer_list_by_vehicle_key(
        selected_date,
        selected_vehicle_key
    )

    total_data = get_dispatch_total(dispatch_list)

    return render_template(
        "dispatch.html",
        dispatch_list=dispatch_list,
        customers=customers,
        dispatch_total=dispatch_total,
        selected_date=selected_date,
        selected_vehicle_key=selected_vehicle_key        
    )