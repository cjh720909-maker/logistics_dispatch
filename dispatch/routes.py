from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from utils.date_helper import get_default_work_date
from flask import redirect
from flask import url_for

from dispatch.service import(
    get_dispatch_summary_by_date,
    get_customer_list_by_driver,
    get_dispatch_total,
    get_customer_orders,
    get_vehicle_dispatch_names,
    change_customer_driver,
)

dispatch_bp = Blueprint(
    "dispatch",
    __name__,
    template_folder="templates"
)

@dispatch_bp.route("/")
def index():
    return dispatch_210()

@dispatch_bp.route("/dispatch_210")
def dispatch_210():
    return render_template(
        "dispatch_upload.html"
    )


@dispatch_bp.route("/dispatch_220")
def dispatch_220():
    return render_template(
        "dispatch_prepare.html"
    )
    
@dispatch_bp.route("/dispatch_230")
def dispatch_230():
    selected_date = request.args.get("date", get_default_work_date())
    selected_driver = request.args.get("driver")

    dispatch_names = get_vehicle_dispatch_names()
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
        dispatch_names=dispatch_names,
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

@dispatch_bp.route("/dispatch_240")
def dispatch_240():
    return render_template(
        "dispatch_status.html"
    )

@dispatch_bp.route("/dispatch_230/change_driver", methods=["POST"])
def dispatch_230_change_driver():
    selected_date = request.form.get("date")
    current_driver = request.form.get("current_driver")
    target_driver = request.form.get("target_driver")
    selected_customers = request.form.getlist("selected_customers")

    change_customer_driver(
        selected_date,
        current_driver,
        target_driver,
        selected_customers
    )

    return redirect(
        url_for(
            "dispatch.dispatch_230",
            date=selected_date,
            driver=target_driver
        )
    )