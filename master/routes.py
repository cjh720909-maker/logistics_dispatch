from flask import Blueprint
from flask import render_template
from flask import request

from master.service import (
    get_product_130_list,
    get_vehicle_driver_140_list,
    get_delivery_customer_120_list,
    get_customer_110_list,
)


master_bp = Blueprint(
    "master",
    __name__,
    template_folder="templates"
)


@master_bp.route("/product_130")
def product_130():
    filters = {
        "product_name": request.args.get("product_name", ""),
        "product_code": request.args.get("product_code", ""),
        "base_category": request.args.get("base_category", ""),
        "picking_category": request.args.get("picking_category", ""),
        "integrated": request.args.get("integrated", ""),
    }

    rows = get_product_130_list(filters)

    return render_template(
        "product.html",
        filters=filters,
        rows=rows,
    )

@master_bp.route("/vehicle_driver_140")
def vehicle_driver_140():
    filters = {
        "driver_name": request.args.get("driver_name", ""),
        "dispatch_name": request.args.get("dispatch_name", ""),
        "area_name": request.args.get("area_name", ""),
        "integrated": request.args.get("integrated", ""),
    }

    rows = get_vehicle_driver_140_list(filters)

    return render_template(
        "vehicle_driver.html",
        filters=filters,
        rows=rows,
    )

@master_bp.route("/delivery_customer_120")
def delivery_customer_120():
    filters = {
        "delivery_name": request.args.get("delivery_name", ""),
        "dispatch_name": request.args.get("dispatch_name", ""),
        "address": request.args.get("address", ""),
        "integrated": request.args.get("integrated", ""),
    }

    rows = get_delivery_customer_120_list(filters)

    return render_template(
        "delivery_customer.html",
        filters=filters,
        rows=rows,
    )
    
@master_bp.route("/customer_110")
def customer_110():
    filters = {
        "customer_name": request.args.get("customer_name", ""),
        "customer_code": request.args.get("customer_code", ""),
        "integrated": request.args.get("integrated", ""),
    }

    rows = get_customer_110_list(filters)

    return render_template(
        "customer.html",
        filters=filters,
        rows=rows,
    )


    