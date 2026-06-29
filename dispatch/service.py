import base64
import math
from decimal import Decimal
from db import engine
from db_local import local_engine

from utils.encoding import (
    fix_encoding,
    fix_row,
    get_pick_type
)


def make_vehicle_key(raw_gun, raw_name):
    value = f"{raw_gun or ''}||{raw_name or ''}"
    return base64.urlsafe_b64encode(
        value.encode("utf-8")
    ).decode("ascii")

def read_vehicle_key(vehicle_key):
    if not vehicle_key:
        return None, None

    value = base64.urlsafe_b64decode(
        vehicle_key.encode("ascii")
    ).decode("utf-8")

    raw_gun, raw_name = value.split("||", 1)

    return raw_gun, raw_name

def to_float(value):
    if value is None:
        return 0

    if isinstance(value, Decimal):
        return float(value)

    return float(value)


def get_dispatch_summary_by_date(selected_date):
    if not selected_date:
        return []

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.CB_DRIVER,
                c.area_name AS CA_GUN,
                c.driver_name AS CA_NAME,
                c.dock_no AS CA_DOCKNO,
                c.capacity_ton AS CA_KG,
                COUNT(DISTINCT b.B_C_CODE) AS customer_count,
                COUNT(*) AS item_count,
                SUM(b.B_QTY) AS total_qty,
                SUM(b.B_KG) AS total_kg
            FROM dispatch_order b
            LEFT JOIN vehicle c
                ON b.CB_DRIVER = c.dispatch_name
            WHERE b.B_DATE = ?
            GROUP BY
                b.CB_DRIVER,
                c.area_name,
                c.driver_name,
                c.dock_no,
                c.capacity_ton
            """,
            (selected_date,)
        )

        rows = result.mappings().all()
        pick_qty_map = get_pick_qty_map(selected_date)

        fixed_rows = []
        vehicle_total_map = {}

        for row in rows:
            row = dict(row)

            raw_gun = row["CA_GUN"]
            raw_name = row["CA_NAME"]

            vehicle_key = f"{raw_gun or ''}||{raw_name or ''}"

            vehicle_total_map[vehicle_key] = (
                vehicle_total_map.get(vehicle_key, 0)
                + to_float(row["total_kg"])
            )

        for row in rows:
            row = dict(row)

            raw_driver = row["CB_DRIVER"]
            raw_gun = row["CA_GUN"]
            raw_name = row["CA_NAME"]

            net_kg = to_float(row["total_kg"])

            vehicle_key_value = f"{raw_gun or ''}||{raw_name or ''}"
            total_kg = vehicle_total_map.get(vehicle_key_value, 0)

            net_kg = round(net_kg)
            total_kg = round(total_kg)

            car_ton = to_float(row["CA_KG"])
            capacity_kg = car_ton * 1000
            capacity_kg = round(capacity_kg)

            if capacity_kg > 0:
                load_rate = int(round(
                    (total_kg / capacity_kg) * 100
                ))
            else:
                load_rate = 0
            pick_qty = pick_qty_map.get(raw_driver, {
                "kim_qty": 0,
                "frozen_qty": 0,
                "sprout_qty": 0,
            })

            fixed_rows.append({
                "vehicle_key": make_vehicle_key(raw_gun, raw_name),
                "CB_DRIVER": raw_driver,
                "CA_GUN": raw_gun,
                "CA_NAME": raw_name,
                "CA_DOCKNO": row["CA_DOCKNO"],
                "CA_KG": car_ton,
                "capacity_kg": capacity_kg,
                "customer_count": row["customer_count"],
                "item_count": row["item_count"],
                "total_qty": row["total_qty"],
                "net_kg": net_kg,
                "total_kg": total_kg,
                "load_rate": load_rate,
                "kim_qty": math.ceil(pick_qty["kim_qty"]),
                "frozen_qty": math.ceil(pick_qty["frozen_qty"]),
                "sprout_qty": math.ceil(pick_qty["sprout_qty"]),            })

        fixed_rows.sort(
            key=lambda row: (
                row["CA_GUN"] or "",
                row["CA_NAME"] or "",
                0 if row["CB_DRIVER"] == row["CA_NAME"] else 1,
                row["CB_DRIVER"] or "",
            )
        )
        shown_vehicle_keys = set()

        for row in fixed_rows:
            key = row["vehicle_key"]

            if key in shown_vehicle_keys:
                row["show_vehicle_total"] = False
            else:
                row["show_vehicle_total"] = True
                shown_vehicle_keys.add(key)

        return fixed_rows


def get_customer_list_by_driver(selected_date, driver):
    if not selected_date or not driver:
        return []

    raw_kim = "김류"
    raw_frozen = "냉동"
    raw_sprout = "콩나물"

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                MAX(b.B_C_CODE) AS B_C_CODE,
                b.B_C_NAME,
                MAX(b.B_C_PAN_NAME) AS B_C_PAN_NAME,
                b.CB_ADDRESS,
                MAX(c.shared_vehicle) AS CB_GONG,
                MAX(c.memo) AS CB_MEMO,

                SUM(
                    CASE
                        WHEN p.base_category = ?
                        THEN CEIL(
                            b.B_QTY / NULLIF(b.B_IN_QTY, 0)
                        )
                        ELSE 0
                    END
                ) AS kim_qty,

                SUM(
                    CASE
                        WHEN p.base_category = ?
                        THEN CEIL(
                            b.B_QTY / NULLIF(b.B_IN_QTY, 0)
                        )
                        ELSE 0
                    END
                ) AS frozen_qty,

                SUM(
                    CASE
                        WHEN p.base_category = ?
                        THEN CEIL(
                            b.B_QTY / NULLIF(b.B_IN_QTY, 0)
                        )
                        ELSE 0
                    END
                ) AS sprout_qty,

                COUNT(*) AS item_count,
                SUM(b.B_QTY) AS total_qty,
                CEIL(SUM(b.B_KG)) AS total_kg

            FROM dispatch_order b

            LEFT JOIN delivery c
                ON b.CB_CODE = c.code

            LEFT JOIN (
                SELECT
                    code,
                    MAX(base_category) AS base_category
                FROM product
                GROUP BY code
            ) p
                ON b.B_P_NO = p.code

            WHERE b.B_DATE = ?
            AND b.CB_DRIVER = ?

            GROUP BY
                b.B_C_NAME,
                b.CB_ADDRESS

            ORDER BY
                b.CB_ADDRESS,
                b.B_C_NAME
            """,
            (
                raw_kim,
                raw_frozen,
                raw_sprout,
                selected_date,
                driver,
            )
        )

        rows = result.mappings().all()

        return [
            {
                **dict(row),
                "kim_qty": int(row["kim_qty"] or 0),
                "frozen_qty": int(row["frozen_qty"] or 0),
                "sprout_qty": int(row["sprout_qty"] or 0),
                "total_qty": int(row["total_qty"] or 0),
                "total_kg": int(row["total_kg"] or 0),
            }
            for row in rows
        ]

def get_dispatch_total(dispatch_list):
    total_kg = 0
    center_kg = 0
    dispatch_kg = 0
    total_capacity_kg = 0

    for row in dispatch_list:
        net_kg = row.get("net_kg", 0) or 0
        area = row.get("CA_GUN", "")

        total_kg += net_kg

        if area == "Z센터":
            center_kg += net_kg
        else:
            dispatch_kg += net_kg

        if area != "Z센터" and row.get("show_vehicle_total"):
            total_capacity_kg += row.get("capacity_kg", 0) or 0

    if total_capacity_kg > 0:
        total_load_rate = round((dispatch_kg / total_capacity_kg) * 100)
    else:
        total_load_rate = 0

    return {
        "total_kg": round(total_kg),
        "center_kg": round(center_kg),
        "dispatch_kg": round(dispatch_kg),
        "total_capacity_kg": round(total_capacity_kg),
        "total_load_rate": round(total_load_rate),
    }

def get_pick_qty_map(selected_date):
    pick_map = {}

    if not selected_date:
        return pick_map

    product_map = get_product_map()

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.CB_DRIVER,
                b.B_P_NO,
                b.B_QTY
            FROM dispatch_order b
            WHERE b.B_DATE = ?
            """,
            (selected_date,)
        )

        rows = result.mappings().all()

        for row in rows:
            raw_driver = row["CB_DRIVER"]
            p_code = row["B_P_NO"]
            qty = to_float(row["B_QTY"])

            product = product_map.get(p_code)

            if not product:
                continue

            div_pick = product["div_pick"]
            ipsu = product["ipsu"]

            pick_type = get_pick_type(div_pick)

            if ipsu > 0:
                box_qty = qty / ipsu
            else:
                box_qty = qty

            if raw_driver not in pick_map:
                pick_map[raw_driver] = {
                    "kim_qty": 0,
                    "frozen_qty": 0,
                    "sprout_qty": 0,
                }

            if pick_type == "김류":
                pick_map[raw_driver]["kim_qty"] += box_qty

            elif pick_type == "냉동":
                pick_map[raw_driver]["frozen_qty"] += box_qty

            elif pick_type == "콩나물":
                pick_map[raw_driver]["sprout_qty"] += box_qty

    return pick_map

def get_product_map():
    product_map = {}

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                code,
                base_category,
                pick_category,
                ipsu
            FROM product
            """
        )

        rows = result.mappings().all()

        for row in rows:
            p_code = row["code"]

            product_info = {
                "div_pick": row["pick_category"],
                "ipsu": to_float(row["ipsu"])
            }

            if p_code not in product_map:
                product_map[p_code] = product_info

    return product_map

def get_customer_orders(selected_date, driver, customer_name, customer_address):
    if not selected_date or not driver or not customer_name:
        return []

    with local_engine.connect() as conn:

        result = conn.exec_driver_sql(
            """
            SELECT
                b.B_DATE,
                b.B_C_NAME,
                b.B_P_NO,
                b.B_P_NAME,
                b.B_QTY,
                b.B_KG,
                b.B_NAP_NO,
                b.B_ORDER_NO,

                p.base_category AS P_DIV_BAS,

                ROUND(b.B_IN_QTY, 0) AS B_IN_QTY,

                b.B_QTY AS piece_qty

            FROM dispatch_order b

            LEFT JOIN (
                SELECT
                    code,
                    MAX(base_category) AS base_category
                FROM product
                GROUP BY code
            ) p
                ON b.B_P_NO = p.code

            WHERE b.B_DATE = ?
            AND b.CB_DRIVER = ?
            AND b.B_C_NAME = ?
            AND b.CB_ADDRESS = ?

            ORDER BY
                p.base_category,
                b.B_P_NAME
            """,
            (
                selected_date,
                driver,
                customer_name,
                customer_address,
            )
        )

        rows = result.mappings().all()

        return [
            dict(row)
            for row in rows
        ]

def get_vehicle_dispatch_names():
    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT DISTINCT
                dispatch_name
            FROM vehicle
            WHERE dispatch_name IS NOT NULL
            AND dispatch_name != ''
            ORDER BY dispatch_name
            """
        )

        return [
            row["dispatch_name"]
            for row in result.mappings().all()
        ]


def change_customer_driver(selected_date, current_driver, target_driver, selected_customers):
    if not selected_date or not current_driver or not target_driver:
        return 0

    if not selected_customers:
        return 0

    updated_count = 0

    with local_engine.begin() as conn:
        for item in selected_customers:
            customer_name, customer_address = item.split("||", 1)

            result = conn.exec_driver_sql(
                """
                UPDATE dispatch_order
                SET CB_DRIVER = ?
                WHERE B_DATE = ?
                AND CB_DRIVER = ?
                AND B_C_NAME = ?
                AND CB_ADDRESS = ?
                """,
                (
                    target_driver,
                    selected_date,
                    current_driver,
                    customer_name,
                    customer_address,
                )
            )

            updated_count += result.rowcount

    return updated_count

def get_vehicle_dispatch_names():
    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT DISTINCT
                dispatch_name
            FROM vehicle
            WHERE dispatch_name IS NOT NULL
            AND dispatch_name != ''
            ORDER BY dispatch_name
            """
        )

        return [
            row["dispatch_name"]
            for row in result.mappings().all()
        ]


def change_customer_driver(selected_date, current_driver, target_driver, selected_customers):
    if not selected_date or not current_driver or not target_driver:
        return 0

    if not selected_customers:
        return 0

    updated_count = 0

    with local_engine.begin() as conn:
        for item in selected_customers:
            customer_name, customer_address = item.split("||", 1)

            result = conn.exec_driver_sql(
                """
                UPDATE dispatch_order
                SET CB_DRIVER = ?
                WHERE B_DATE = ?
                AND CB_DRIVER = ?
                AND B_C_NAME = ?
                AND CB_ADDRESS = ?
                """,
                (
                    target_driver,
                    selected_date,
                    current_driver,
                    customer_name,
                    customer_address,
                )
            )

            updated_count += result.rowcount

    return updated_count