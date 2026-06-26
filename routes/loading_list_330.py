from flask import Blueprint
from flask import render_template
from flask import request
from utils.date_helper import get_default_work_date

from services.loading_service import (
    get_loading_driver_list,
    get_loading_list,
    get_loading_summary,
)

loading_bp = Blueprint("loading", __name__)


@loading_bp.route("/loading_list_330")
def loading_list_330():
    selected_date = request.args.get("date", get_default_work_date())
    selected_driver = request.args.get("driver", "")
    no_print_only = request.args.get("no_print_only") == "1"

    driver_list = get_loading_driver_list(selected_date, no_print_only)
    rows = get_loading_list(selected_date, selected_driver)

    return render_template(
        "300_print/loading_list_330.html",
        selected_date=selected_date,
        selected_driver=selected_driver,
        no_print_only=no_print_only,
        driver_list=driver_list,
        rows=rows,
    )


@loading_bp.route("/loading_summary_340")
def loading_summary_340():
    selected_date = request.args.get("date", get_default_work_date())
    selected_driver = request.args.get("driver", "")
    no_print_only = request.args.get("no_print_only") == "1"

    driver_list = get_loading_driver_list(selected_date, no_print_only)
    rows = get_loading_summary(selected_date, selected_driver)

    return render_template(
        "300_print/loading_summary_340.html",
        selected_date=selected_date,
        selected_driver=selected_driver,
        no_print_only=no_print_only,
        driver_list=driver_list,
        rows=rows,
    )