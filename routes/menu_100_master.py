from flask import Blueprint
from flask import render_template
from flask import request

from services.menu_100_master_service import get_130_products


master_bp = Blueprint("master_100", __name__)


@master_bp.route("/130-products")
def products_130():
    filters = {
        "product_name": request.args.get("product_name", ""),
        "product_code": request.args.get("product_code", ""),
        "base_category": request.args.get("base_category", ""),
        "picking_category": request.args.get("picking_category", ""),
        "integrated": request.args.get("integrated", ""),
    }

    rows = get_130_products(filters)

    return render_template(
        "100_master/130_products.html",
        filters=filters,
        rows=rows,
    )