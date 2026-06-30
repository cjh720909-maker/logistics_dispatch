from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

from master.service import (
    get_product_130_list,
    get_vehicle_driver_140_list,
    get_delivery_customer_120_list,
    get_customer_110_list,
    get_product_name_rules,
    get_upload_delivery_rules,
    create_upload_delivery_rule,
    create_virtual_delivery_from_existing,
    get_product_base_categories,
    search_delivery_for_virtual,
    get_upload_delivery_merge_rules,
    create_upload_delivery_merge_rule,
    create_product_name_rule,
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

@master_bp.route("/rule_150", methods=["GET", "POST"])
def rule_150():
    if request.method == "POST":
        before_name = request.form.get("before_name")
        after_name = request.form.get("after_name")
        memo = request.form.get("memo")

        create_product_name_rule(
            before_name,
            after_name,
            memo
        )

        return redirect(
            url_for("master.rule_150")
        )

    rows = get_product_name_rules()

    return render_template(
        "rule.html",
        rows=rows,
    )
    
@master_bp.route("/upload_rule_151", methods=["GET", "POST"])
def upload_rule_151():
    if request.method == "POST":
        create_upload_delivery_rule(
            request.form.get("rule_type"),
            request.form.get("before_code"),
            request.form.get("before_name"),
            ",".join(request.form.getlist("base_category")),
            request.form.get("after_code"),
            request.form.get("after_name"),
            request.form.get("memo"),
        )

        return redirect(
            url_for("master.upload_rule_151")
        )

    rows = get_upload_delivery_rules()
    base_categories = get_product_base_categories()

    return render_template(
        "upload_rule.html",
        rows=rows,
        base_categories=base_categories,
    )
    
@master_bp.route("/delivery_customer_120/create_virtual", methods=["POST"])
def delivery_customer_120_create_virtual():
    source_code = request.form.get("source_code")
    new_code = request.form.get("new_code")
    new_name = request.form.get("new_name")

    result = create_virtual_delivery_from_existing(
        source_code,
        new_code,
        new_name
    )

    return redirect(
        url_for(
            "master.delivery_customer_120",
            integrated=new_name
        )
    )

@master_bp.route("/delivery_customer_120/virtual", methods=["GET", "POST"])
def delivery_customer_120_virtual():
    keyword = request.args.get("keyword", "")
    rows = search_delivery_for_virtual(keyword)
    result_message = ""

    if request.method == "POST":
        source_code = request.form.get("source_code")
        new_name = request.form.get("new_name")

        result = create_virtual_delivery_from_existing(
            source_code,
            new_name,
            new_name
        )

        result_message = result.get("message", "")

        return redirect(
            url_for(
                "master.delivery_customer_120",
                integrated=new_name
            )
        )

    return render_template(
        "delivery_virtual.html",
        keyword=keyword,
        rows=rows,
        result_message=result_message,
    )

@master_bp.route("/upload_merge_rule_152", methods=["GET", "POST"])
def upload_merge_rule_152():
    if request.method == "POST":
        create_upload_delivery_merge_rule(
            request.form.get("group_name"),
            request.form.get("source_code"),
            request.form.get("source_name"),
            request.form.get("target_code"),
            request.form.get("target_name"),
            request.form.get("memo"),
        )

        return redirect(
            url_for("master.upload_merge_rule_152")
        )

    rows = get_upload_delivery_merge_rules()

    return render_template(
        "upload_merge_rule.html",
        rows=rows,
    )