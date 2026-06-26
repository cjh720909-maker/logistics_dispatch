from db import engine
from utils.encoding import fix_row


def encode_kr(value):
    if not value:
        return value
    return value.encode("cp949").decode("latin1")


def get_300_driver_list(selected_date):
    if not selected_date:
        return []

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                c.CA_DOCKNO,
                c.CA_NAME,
                b.CB_DRIVER,
                CEIL(SUM(b.B_KG)) AS total_kg
            FROM t_balju b
            LEFT JOIN t_car c
                ON b.CB_DRIVER = c.CB_DRIVER
            WHERE b.B_DATE = %s
              AND (c.CA_NOPRINT2 IS NULL OR c.CA_NOPRINT2 <> 'Y')
            GROUP BY
                c.CA_DOCKNO,
                c.CA_NAME,
                b.CB_DRIVER
            """,
            (selected_date,)
        )

        rows = [fix_row(dict(row)) for row in result.mappings().all()]
        rows.sort(key=lambda x: str(x.get("CA_NAME", "")).strip())
        return rows


def get_320_customer_list(selected_date, driver):
    if not selected_date or not driver:
        return []

    raw_driver = encode_kr(driver)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.B_C_NAME,
                MAX(b.CB_ADDRESS) AS CB_ADDRESS,
                CEIL(SUM(b.B_KG)) AS total_kg
            FROM t_balju b
            WHERE b.B_DATE = %s
              AND b.CB_DRIVER = %s
            GROUP BY
                b.B_C_NAME
            ORDER BY
                b.B_C_NAME
            """,
            (selected_date, raw_driver)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]


def get_320_invoice_items(selected_date, driver, customer):
    if not selected_date or not driver or not customer:
        return []

    raw_driver = encode_kr(driver)
    raw_customer = encode_kr(customer)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.B_DATE,
                b.B_C_NAME,
                b.B_P_NO,
                b.B_P_NAME,
                b.B_QTY,
                ROUND(b.B_IN_QTY, 0) AS B_IN_QTY,
                b.B_DAN,
                b.B_VAT_DIV,
                (b.B_QTY * b.B_DAN) AS amount
            FROM t_balju b
            WHERE b.B_DATE = %s
              AND b.CB_DRIVER = %s
              AND b.B_C_NAME = %s
            ORDER BY
                b.B_P_NAME
            """,
            (selected_date, raw_driver, raw_customer)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]

def get_320_invoice_list(selected_date, no_print_only=False):
    if not selected_date:
        return []

    if no_print_only:
        where_no_print = "AND c.CA_NOPRINT = 'Y'"
    else:
        where_no_print = "AND (c.CA_NOPRINT IS NULL OR c.CA_NOPRINT <> 'Y')"

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                c.CA_DOCKNO,
                c.CA_NAME,
                b.CB_DRIVER,
                b.B_C_NAME,
                MAX(b.CB_DIV_CUST) AS CB_DIV_CUST,
                CEIL(SUM(b.B_KG)) AS total_kg
            FROM t_balju b
            LEFT JOIN t_car c
                ON b.CB_DRIVER = c.CB_DRIVER
            WHERE b.B_DATE = %s
              {where_no_print}
            GROUP BY
                c.CA_DOCKNO,
                c.CA_NAME,
                b.CB_DRIVER,
                b.B_C_NAME
            """,
            (selected_date,)
        )

        rows = [fix_row(dict(row)) for row in result.mappings().all()]
        rows.sort(
            key=lambda x: (
                str(x.get("CA_NAME", "")).strip(),
                str(x.get("CB_DRIVER", "")).strip(),
                str(x.get("B_C_NAME", "")).strip(),
            )
        )
        return rows

def get_350_picking_categories(selected_date):
    if not selected_date:
        return []

    raw_div = encode_kr("피킹리스트분류")

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT DISTINCT
                cb.C_NAME
            FROM t_balju b
            LEFT JOIN t_product p
                ON b.B_P_NO = p.P_CODE
            LEFT JOIN t_code_basic cb
                ON p.P_DIV_PICK = cb.C_NAME
            WHERE b.B_DATE = %s
              AND cb.C_DIV = %s
              AND p.P_DIV_PICK IS NOT NULL
              AND p.P_DIV_PICK <> ''
            ORDER BY
                cb.C_NAME
            """,
            (selected_date, raw_div)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]

def get_350_picking_items(selected_date, category):
    if not selected_date or not category:
        return []

    raw_category = encode_kr(category)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.B_P_NO,
                b.B_P_NAME,
                c.CA_DOCKNO,
                b.CB_DRIVER,
                ROUND(MAX(b.B_IN_QTY), 0) AS B_IN_QTY,
                SUM(FLOOR(b.B_QTY / NULLIF(b.B_IN_QTY, 0))) AS box_qty,
                CAST(SUM(MOD(b.B_QTY, NULLIF(b.B_IN_QTY, 0))) AS UNSIGNED) AS piece_qty,
                CAST(SUM(b.B_QTY) AS UNSIGNED) AS total_qty
            FROM t_balju b
            LEFT JOIN t_product p
                ON b.B_P_NO = p.P_CODE
            LEFT JOIN t_car c
                ON b.CB_DRIVER = c.CB_DRIVER
            WHERE b.B_DATE = %s
              AND p.P_DIV_PICK = %s
            GROUP BY
                b.B_P_NO,
                b.B_P_NAME,
                c.CA_DOCKNO,
                b.CB_DRIVER
            ORDER BY
                b.B_P_NAME,
                c.CA_DOCKNO,
                b.CB_DRIVER
            """,
            (selected_date, raw_category)
        )

        rows = [fix_row(dict(row)) for row in result.mappings().all()]

        prev_product_key = None
        for row in rows:
            product_key = f"{row.get('B_P_NO')}|{row.get('B_P_NAME')}"
            row["show_product_name"] = product_key != prev_product_key
            prev_product_key = product_key

        return rows

def get_310_route_driver_list(selected_date, no_print_only=False):
    if not selected_date:
        return []

    if no_print_only:
        where_no_print = "AND c.CA_NOPRINT1 = 'Y'"
    else:
        where_no_print = "AND (c.CA_NOPRINT1 IS NULL OR c.CA_NOPRINT1 <> 'Y')"

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                c.CA_DOCKNO,
                c.CA_NAME,
                b.CB_DRIVER,
                CEIL(SUM(b.B_KG)) AS total_kg
            FROM t_balju b
            LEFT JOIN t_car c
                ON b.CB_DRIVER = c.CB_DRIVER
            WHERE b.B_DATE = %s
              {where_no_print}
            GROUP BY
                c.CA_DOCKNO,
                c.CA_NAME,
                b.CB_DRIVER
            ORDER BY
                c.CA_NAME,
                c.CA_DOCKNO
            """,
            (selected_date,)
        )

        rows = [fix_row(dict(row)) for row in result.mappings().all()]
        rows.sort(key=lambda x: str(x.get("CA_NAME", "")).strip())
        return rows


def get_310_route_items(selected_date, driver):
    if not selected_date or not driver:
        return []

    raw_driver = encode_kr(driver)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.B_C_NAME,
                SUM(CASE WHEN p.P_DIV_BAS = '김류' THEN 1 ELSE 0 END) AS kim_qty,
                SUM(CASE WHEN p.P_DIV_BAS = '두부' THEN 1 ELSE 0 END) AS tofu_qty,
                SUM(CASE WHEN p.P_DIV_BAS = '콩나물' THEN 1 ELSE 0 END) AS sprout_qty
            FROM t_balju b
            LEFT JOIN t_product p
                ON b.B_P_NO = p.P_CODE
            WHERE b.B_DATE = %s
              AND b.CB_DRIVER = %s
            GROUP BY
                b.B_C_NAME
            ORDER BY
                b.B_C_NAME
            """,
            (selected_date, raw_driver)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]

def get_360_pick_groups(selected_date):
    if not selected_date:
        return []

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT DISTINCT
                p.P_DIV_BAS
            FROM t_balju b
            LEFT JOIN t_product p
                ON b.B_P_NO = p.P_CODE
            WHERE b.B_DATE = %s
              AND p.P_DIV_BAS IS NOT NULL
              AND p.P_DIV_BAS <> ''
            """,
            (selected_date,)
        )

        rows = [fix_row(dict(row)) for row in result.mappings().all()]
        rows.sort(key=lambda x: str(x.get("P_DIV_BAS", "")).strip())
        return rows


def get_360_pick_group_boxes(selected_date, group):
    if not selected_date or not group:
        return []

    raw_group = encode_kr(group)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                c.CA_DOCKNO,
                b.CB_DRIVER,
                SUM(FLOOR(b.B_QTY / NULLIF(b.B_IN_QTY, 0))) AS box_qty,
                CAST(SUM(MOD(b.B_QTY, NULLIF(b.B_IN_QTY, 0))) AS UNSIGNED) AS piece_qty,
                CAST(SUM(b.B_QTY) AS UNSIGNED) AS total_qty
            FROM t_balju b
            LEFT JOIN t_product p
                ON b.B_P_NO = p.P_CODE
            LEFT JOIN t_car c
                ON b.CB_DRIVER = c.CB_DRIVER
            WHERE b.B_DATE = %s
              AND p.P_DIV_BAS = %s
            GROUP BY
                c.CA_DOCKNO,
                b.CB_DRIVER
            ORDER BY
                c.CA_DOCKNO,
                b.CB_DRIVER
            """,
            (selected_date, raw_group)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]