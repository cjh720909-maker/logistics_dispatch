from flask import Blueprint
from flask import render_template
from flask import request

from utils.date_helper import get_default_work_date

from services.menu_300_print_service import (
    get_300_driver_list,
    get_320_customer_list,
    get_320_invoice_items,
    get_320_invoice_list,
    get_350_picking_categories,
    get_350_picking_items,
    get_310_route_driver_list,
    get_310_route_items,
    get_360_pick_groups,
    get_360_pick_group_boxes,
)

print_bp = Blueprint("print_300", __name__)


@print_bp.route("/invoice_320")
def invoice_320():
    selected_date = request.args.get("date", get_default_work_date())
    selected_driver = request.args.get("driver", "")
    selected_customer = request.args.get("customer", "")

    no_print_only = request.args.get("no_print_only") == "1"

    invoice_list = get_320_invoice_list(selected_date, no_print_only)

    invoice_items = get_320_invoice_items(
        selected_date,
        selected_driver,
        selected_customer
    )

    return render_template(
        "300_print/invoice_320.html",
        selected_date=selected_date,
        selected_driver=selected_driver,
        selected_customer=selected_customer,
        invoice_list=invoice_list,
        invoice_items=invoice_items,
        no_print_only=no_print_only,
    )

@print_bp.route("/picking_list_350")
def picking_list_350():
    selected_date = request.args.get("date", get_default_work_date())
    selected_category = request.args.get("category", "")
    selected_customer = request.args.get("customer", "")

    categories = get_350_picking_categories(selected_date)
    rows = get_350_picking_items(selected_date, selected_category)

    return render_template(
        "300_print/picking_list_350.html",
        selected_date=selected_date,
        selected_category=selected_category,
        selected_customer=selected_customer,
        categories=categories,
        rows=rows,
    )

@print_bp.route("/route_daily_310")
def route_daily_310():
    selected_date = request.args.get("date", get_default_work_date())
    selected_driver = request.args.get("driver", "")
    no_print_only = request.args.get("no_print_only") == "1"

    driver_list = get_310_route_driver_list(selected_date, no_print_only)
    rows = get_310_route_items(selected_date, selected_driver)

    return render_template(
        "300_print/route_daily_310.html",
        selected_date=selected_date,
        selected_driver=selected_driver,
        no_print_only=no_print_only,
        driver_list=driver_list,
        rows=rows,
    )

@print_bp.route("/pick_group_boxes_360")
def pick_group_boxes_360():
    selected_date = request.args.get("date", get_default_work_date())
    selected_group = request.args.get("group", "")
    label_count = request.args.get("label_count", "10")

    groups = get_360_pick_groups(selected_date)
    rows = get_360_pick_group_boxes(selected_date, selected_group)

    return render_template(
        "300_print/pick_group_boxes_360.html",
        selected_date=selected_date,
        selected_group=selected_group,
        label_count=label_count,
        groups=groups,
        rows=rows,
    )