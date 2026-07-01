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
def search_prepare_orders(filters):
    selected_date = filters.get("date")
    delivery_name = filters.get("delivery_name")
    delivery_code = filters.get("delivery_code")
    product_name = filters.get("product_name")
    product_code = filters.get("product_code")
    order_no = filters.get("order_no")
    nap_no = filters.get("nap_no")
    customer_name = filters.get("customer_name")
    seller_name = filters.get("seller_name")
    ex_seq = filters.get("ex_seq")

    sql = """
        SELECT
            B_IDX,
            B_DATE,
            CB_DRIVER,
            B_C_NAME,
            B_C_PAN_NAME,
            B_C_CODE,
            B_NAP_DIV,
            B_P_NO,
            B_P_NAME,
            B_DAN,
            B_VAT_DIV,
            B_IN_QTY,
            B_QTY,
            B_KG,
            B_ORDER_NO,
            B_NAP_NO,
            B_EX_SEQ,
            B_MEMO,
            CB_ADDRESS
        FROM dispatch_order
        WHERE 1 = 1
    """

    params = []

    if selected_date:
        sql += " AND B_DATE = ?"
        params.append(selected_date)

    if delivery_name:
        sql += " AND B_C_NAME LIKE ?"
        params.append(f"%{delivery_name}%")

    if delivery_code:
        sql += " AND B_C_CODE LIKE ?"
        params.append(f"%{delivery_code}%")

    if product_name:
        sql += " AND B_P_NAME LIKE ?"
        params.append(f"%{product_name}%")

    if product_code:
        sql += " AND B_P_NO LIKE ?"
        params.append(f"%{product_code}%")

    if order_no:
        sql += " AND B_ORDER_NO LIKE ?"
        params.append(f"%{order_no}%")

    if nap_no:
        sql += " AND B_NAP_NO LIKE ?"
        params.append(f"%{nap_no}%")

    if customer_name:
        sql += " AND C_NAME LIKE ?"
        params.append(f"%{customer_name}%")

    if seller_name:
        sql += " AND B_C_PAN_NAME LIKE ?"
        params.append(f"%{seller_name}%")

    if ex_seq:
        sql += " AND B_EX_SEQ LIKE ?"
        params.append(f"%{ex_seq}%")

    has_filter = any([
        delivery_name,
        delivery_code,
        product_name,
        product_code,
        order_no,
        nap_no,
        customer_name,
        seller_name,
        ex_seq,
    ])

    sql += """
        ORDER BY
            CB_DRIVER,
            B_C_NAME,
            B_P_NAME,
            B_IDX
    """

    if has_filter:
        sql += " LIMIT 500"
    else:
        sql += " LIMIT 100"
        
    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(sql, tuple(params))
        return [dict(row) for row in result.mappings().all()]

def apply_emergency_to_orders(order_ids):
    if not order_ids:
        return 0

    updated_count = 0

    with local_engine.begin() as conn:
        for order_id in order_ids:
            result = conn.exec_driver_sql(
                """
                UPDATE dispatch_order
                SET
                    B_C_NAME =
                        CASE
                            WHEN B_C_NAME LIKE '%-긴급'
                            THEN B_C_NAME
                            ELSE B_C_NAME || '-긴급'
                        END,
                    CB_DRIVER = '임시배차',
                    B_MEMO =
                        CASE
                            WHEN B_MEMO IS NULL OR B_MEMO = ''
                            THEN '긴급'
                            WHEN B_MEMO LIKE '%긴급%'
                            THEN B_MEMO
                            ELSE B_MEMO || ' / 긴급'
                        END
                WHERE B_IDX = ?
                """,
                (
                    order_id,
                )
            )

            updated_count += result.rowcount

    return updated_count

def cancel_emergency_orders(order_ids):
    if not order_ids:
        return 0

    updated_count = 0

    with local_engine.begin() as conn:
        for order_id in order_ids:
            row = conn.exec_driver_sql(
                """
                SELECT
                    B_C_NAME,
                    B_C_CODE
                FROM dispatch_order
                WHERE B_IDX = ?
                """,
                (order_id,)
            ).mappings().first()

            if not row:
                continue

            original_name = row["B_C_NAME"].replace("-긴급", "")

            delivery = conn.exec_driver_sql(
                """
                SELECT
                    dispatch_name
                FROM delivery
                WHERE name = ?
                LIMIT 1
                """,
                (original_name,)
            ).mappings().first()

            original_driver = delivery["dispatch_name"] if delivery else row["B_C_NAME"]

            result = conn.exec_driver_sql(
                """
                UPDATE dispatch_order
                SET
                    B_C_NAME = ?,
                    CB_DRIVER = ?,
                    B_MEMO =
                        CASE
                            WHEN B_MEMO = '긴급' THEN ''
                            ELSE REPLACE(REPLACE(B_MEMO, ' / 긴급', ''), '긴급 / ', '')
                        END
                WHERE B_IDX = ?
                """,
                (
                    original_name,
                    original_driver,
                    order_id,
                )
            )

            updated_count += result.rowcount

    return updated_count

def update_product_name_orders(order_ids, new_product_name):
    if not order_ids or not new_product_name:
        return 0

    updated_count = 0

    with local_engine.begin() as conn:
        for order_id in order_ids:
            result = conn.exec_driver_sql(
                """
                UPDATE dispatch_order
                SET B_P_NAME = ?
                WHERE B_IDX = ?
                """,
                (
                    new_product_name,
                    order_id,
                )
            )

            updated_count += result.rowcount

    return updated_count

def get_product_name_rules_for_select():
    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                id,
                before_name,
                after_name
            FROM product_name_rule
            WHERE is_active = 1
            ORDER BY before_name
            """
        )

        return [dict(row) for row in result.mappings().all()]


def apply_product_name_rule(order_ids, rule_id):
    if not order_ids or not rule_id:
        return 0

    with local_engine.connect() as conn:
        rule = conn.exec_driver_sql(
            """
            SELECT
                before_name,
                after_name
            FROM product_name_rule
            WHERE id = ?
            """,
            (rule_id,)
        ).mappings().first()

    if not rule:
        return 0

    updated_count = 0

    with local_engine.begin() as conn:
        for order_id in order_ids:
            result = conn.exec_driver_sql(
                """
                UPDATE dispatch_order
                SET B_P_NAME = ?
                WHERE B_IDX = ?
                """,
                (
                    rule["after_name"],
                    order_id,
                )
            )

            updated_count += result.rowcount

    return updated_count

def apply_storage_orders(order_ids):
    if not order_ids:
        return 0

    updated_count = 0

    with local_engine.begin() as conn:
        for order_id in order_ids:
            row = conn.exec_driver_sql(
                """
                SELECT
                    B_IDX,
                    B_DATE,
                    B_C_NAME,
                    B_P_NO,
                    B_P_NAME,
                    B_QTY,
                    B_KG
                FROM dispatch_order
                WHERE B_IDX = ?
                """,
                (order_id,)
            ).mappings().first()

            if not row:
                continue

            conn.exec_driver_sql(
                """
                INSERT INTO dispatch_storage (
                    dispatch_order_id,
                    storage_date,
                    customer_name,
                    product_code,
                    product_name,
                    qty,
                    weight,
                    status,
                    reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'STORED', ?)
                """,
                (
                    row["B_IDX"],
                    row["B_DATE"],
                    row["B_C_NAME"],
                    row["B_P_NO"],
                    row["B_P_NAME"],
                    row["B_QTY"],
                    row["B_KG"],
                    "보관",
                )
            )

            result = conn.exec_driver_sql(
                """
                UPDATE dispatch_order
                SET
                    CB_DRIVER = '보관',
                    B_MEMO =
                        CASE
                            WHEN B_MEMO IS NULL OR B_MEMO = ''
                            THEN '보관'
                            WHEN B_MEMO LIKE '%보관%'
                            THEN B_MEMO
                            ELSE B_MEMO || ' / 보관'
                        END
                WHERE B_IDX = ?
                """,
                (order_id,)
            )

            updated_count += result.rowcount

    return updated_count

def get_storage_list():
    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                id,
                dispatch_order_id,
                storage_date,
                release_date,
                customer_name,
                product_code,
                product_name,
                qty,
                weight,
                status,
                reason,
                created_at
            FROM dispatch_storage
            ORDER BY
                storage_date DESC,
                id DESC
            """
        )

        return [dict(row) for row in result.mappings().all()]

def create_product_name_rule_table():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS product_name_rule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                before_name TEXT NOT NULL,
                after_name TEXT NOT NULL,
                memo TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_product_name_rules():
    create_product_name_rule_table()

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                id,
                before_name,
                after_name,
                memo,
                is_active,
                created_at
            FROM product_name_rule
            ORDER BY id DESC
            """
        )

        return [dict(row) for row in result.mappings().all()]


def create_product_name_rule(before_name, after_name, memo):
    create_product_name_rule_table()

    if not before_name or not after_name:
        return

    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            INSERT INTO product_name_rule (
                before_name,
                after_name,
                memo
            )
            VALUES (?, ?, ?)
            """,
            (
                before_name,
                after_name,
                memo,
            )
        )

def create_upload_delivery_rule_table():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS upload_delivery_rule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                before_code TEXT,
                before_name TEXT,
                base_category TEXT,
                after_code TEXT,
                after_name TEXT,
                memo TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        columns = conn.exec_driver_sql(
            "PRAGMA table_info(upload_delivery_rule)"
        ).mappings().all()

        column_names = [row["name"] for row in columns]

        if "rule_type" in column_names:
            conn.exec_driver_sql(
                """
                CREATE TABLE upload_delivery_rule_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    before_code TEXT,
                    before_name TEXT,
                    base_category TEXT,
                    after_code TEXT,
                    after_name TEXT,
                    memo TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.exec_driver_sql(
                """
                INSERT INTO upload_delivery_rule_new (
                    id,
                    before_code,
                    before_name,
                    base_category,
                    after_code,
                    after_name,
                    memo,
                    is_active,
                    created_at
                )
                SELECT
                    id,
                    before_code,
                    before_name,
                    base_category,
                    after_code,
                    after_name,
                    memo,
                    is_active,
                    created_at
                FROM upload_delivery_rule
                """
            )

            conn.exec_driver_sql("DROP TABLE upload_delivery_rule")
            conn.exec_driver_sql(
                "ALTER TABLE upload_delivery_rule_new RENAME TO upload_delivery_rule"
            )

def get_upload_delivery_rules():
    create_upload_delivery_rule_table()

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                id,
                before_code,
                before_name,
                base_category,
                after_code,
                after_name,
                memo,
                is_active,
                created_at
            FROM upload_delivery_rule
            ORDER BY id DESC
            """
        )

        return [dict(row) for row in result.mappings().all()]


def create_upload_delivery_rule(
    before_code,
    base_category,
    after_code,
    memo
):
    create_upload_delivery_rule_table()

    before_name = get_delivery_name_by_code(before_code)
    after_name = get_delivery_name_by_code(after_code)

    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            INSERT INTO upload_delivery_rule (
                before_code,
                before_name,
                base_category,
                after_code,
                after_name,
                memo
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                before_code,
                before_name,
                base_category,
                after_code,
                after_name,
                memo,
            )
        )

def get_product_base_categories():
    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT DISTINCT
                base_category
            FROM product
            WHERE base_category IS NOT NULL
            AND base_category != ''
            ORDER BY base_category
            """
        )

        return [
            row["base_category"]
            for row in result.mappings().all()
        ]    

def create_upload_delivery_merge_rule_table():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS upload_delivery_merge_rule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT,
                source_code TEXT,
                source_name TEXT,
                target_code TEXT,
                target_name TEXT,
                memo TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_upload_delivery_merge_rules():
    create_upload_delivery_merge_rule_table()

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                id,
                group_name,
                source_code,
                source_name,
                target_code,
                target_name,
                memo,
                is_active,
                created_at
            FROM upload_delivery_merge_rule
            ORDER BY
                target_name,
                source_name
            """
        )

        return [dict(row) for row in result.mappings().all()]


def create_upload_delivery_merge_rule(
    group_name,
    source_code,
    source_name,
    target_code,
    target_name,
    memo
):
    create_upload_delivery_merge_rule_table()

    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            INSERT INTO upload_delivery_merge_rule (
                group_name,
                source_code,
                source_name,
                target_code,
                target_name,
                memo
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                group_name,
                source_code,
                source_name,
                target_code,
                target_name,
                memo,
            )
        )

def get_delivery_name_by_code(delivery_code):
    if not delivery_code:
        return ""

    with local_engine.connect() as conn:
        row = conn.exec_driver_sql(
            """
            SELECT name
            FROM delivery
            WHERE code = ?
            """,
            (delivery_code,)
        ).mappings().first()

    if not row:
        return ""

    return row["name"]

def delete_upload_delivery_rule(rule_id):
    if not rule_id:
        return 0

    with local_engine.begin() as conn:
        result = conn.exec_driver_sql(
            """
            DELETE FROM upload_delivery_rule
            WHERE id = ?
            """,
            (rule_id,)
        )

    return result.rowcount