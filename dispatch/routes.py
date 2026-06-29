from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from utils.date_helper import get_default_work_date
from flask import redirect
from flask import url_for
from dispatch.sync import sync_dispatch_order

from dispatch.service import(
    get_dispatch_summary_by_date,
    get_customer_list_by_driver,
    get_dispatch_total,
    get_customer_orders,
    get_vehicle_dispatch_names,
    change_customer_driver,
    search_prepare_orders,
    apply_emergency_to_orders,
    cancel_emergency_orders,
)

dispatch_bp = Blueprint(
    "dispatch",
    __name__,
    template_folder="templates"
)

@dispatch_bp.route("/")
def index():
    return dispatch_210()

@dispatch_bp.route("/dispatch_210", methods=["GET", "POST"])
def dispatch_210():
    selected_date = request.form.get("date") or request.args.get("date") or get_default_work_date()
    sync_result = None

    if request.method == "POST":
        sync_result = sync_dispatch_order(selected_date)

    return render_template(
        "dispatch_upload.html",
        selected_date=selected_date,
        sync_result=sync_result,
    )

@dispatch_bp.route("/dispatch_220")
def dispatch_220():
    filters = {
        "date": request.args.get("date", get_default_work_date()),
        "delivery_name": request.args.get("delivery_name", ""),
        "delivery_code": request.args.get("delivery_code", ""),
        "product_name": request.args.get("product_name", ""),
        "product_code": request.args.get("product_code", ""),
        "order_no": request.args.get("order_no", ""),
        "nap_no": request.args.get("nap_no", ""),
        "customer_name": request.args.get("customer_name", ""),
        "seller_name": request.args.get("seller_name", ""),
        "ex_seq": request.args.get("ex_seq", ""),
    }

    orders = search_prepare_orders(filters)

    return render_template(
        "dispatch_prepare.html",
        filters=filters,
        orders=orders,
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

@dispatch_bp.route("/dispatch_220/apply_emergency", methods=["POST"])
def dispatch_220_apply_emergency():
    selected_date = request.form.get("date")
    selected_orders = request.form.getlist("selected_orders")

    apply_emergency_to_orders(selected_orders)

    return redirect(
        url_for(
            "dispatch.dispatch_220",
            date=selected_date,
            delivery_name=request.form.get("delivery_name", ""),
            delivery_code=request.form.get("delivery_code", ""),
            product_name=request.form.get("product_name", ""),
            product_code=request.form.get("product_code", ""),
            order_no=request.form.get("order_no", ""),
            nap_no=request.form.get("nap_no", ""),
            customer_name=request.form.get("customer_name", ""),
            seller_name=request.form.get("seller_name", ""),
            ex_seq=request.form.get("ex_seq", ""),
        )
    )

@dispatch_bp.route("/dispatch_220/cancel_emergency", methods=["POST"])
def dispatch_220_cancel_emergency():
    selected_date = request.form.get("date")
    selected_orders = request.form.getlist("selected_orders")

    cancel_emergency_orders(selected_orders)

    return redirect(
        url_for(
            "dispatch.dispatch_220",
            date=selected_date,
            delivery_name=request.form.get("delivery_name", ""),
            delivery_code=request.form.get("delivery_code", ""),
            product_name=request.form.get("product_name", ""),
            product_code=request.form.get("product_code", ""),
            order_no=request.form.get("order_no", ""),
            nap_no=request.form.get("nap_no", ""),
            customer_name=request.form.get("customer_name", ""),
            seller_name=request.form.get("seller_name", ""),
            ex_seq=request.form.get("ex_seq", ""),
        )
    )    