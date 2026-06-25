from flask import Blueprint
from flask import render_template
from flask import request

from utils.date_helper import get_default_work_date

from services.menu_300_print_service import (
    get_300_driver_list,
    get_320_customer_list,
    get_320_invoice_items,
    get_320_invoice_list,
)

print_bp = Blueprint("print_300", __name__)


@print_bp.route("/320-invoice")
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
        "300_print/320_invoice.html",
        selected_date=selected_date,
        selected_driver=selected_driver,
        selected_customer=selected_customer,
        invoice_list=invoice_list,
        invoice_items=invoice_items,
        no_print_only=no_print_only,
    )