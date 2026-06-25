from db import engine
from utils.encoding import fix_row


def encode_kr(value):
    if not value:
        return value
    return value.encode("cp949").decode("latin1")


def get_loading_list(selected_date, driver):
    if not selected_date or not driver:
        return []

    raw_driver = encode_kr(driver)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.B_C_NAME,
                b.B_P_NO,
                b.B_P_NAME,
                p.P_BARCODE,
                p.P_DIV_BAS,
                ROUND(b.B_IN_QTY, 0) AS B_IN_QTY,
                b.B_QTY,
                CEIL(b.B_QTY / NULLIF(b.B_IN_QTY, 0)) AS box_qty,
                b.B_KG
            FROM t_balju b
            LEFT JOIN t_product p
                ON b.B_P_NO = p.P_CODE
            WHERE b.B_DATE = %s
              AND b.CB_DRIVER = %s
            ORDER BY
                b.B_C_NAME,
                p.P_DIV_BAS,
                b.B_P_NAME
            """,
            (selected_date, raw_driver)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]


def get_loading_summary(selected_date, driver):
    if not selected_date or not driver:
        return []

    raw_driver = encode_kr(driver)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.B_P_NO,
                b.B_P_NAME,
                p.P_BARCODE,
                p.P_DIV_BAS,
                ROUND(MAX(b.B_IN_QTY), 0) AS B_IN_QTY,
                SUM(b.B_QTY) AS total_qty,
                SUM(CEIL(b.B_QTY / NULLIF(b.B_IN_QTY, 0))) AS total_box_qty,
                CEIL(SUM(b.B_KG)) AS total_kg
            FROM t_balju b
            LEFT JOIN t_product p
                ON b.B_P_NO = p.P_CODE
            WHERE b.B_DATE = %s
              AND b.CB_DRIVER = %s
            GROUP BY
                b.B_P_NO,
                b.B_P_NAME,
                p.P_BARCODE,
                p.P_DIV_BAS
            ORDER BY
                p.P_DIV_BAS,
                b.B_P_NAME
            """,
            (selected_date, raw_driver)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]

def get_loading_driver_list(selected_date, no_print_only=False):
    if not selected_date:
        return []

    if no_print_only:
        where_no_print = "AND c.CA_NOPRINT2 = 'Y'"
    else:
        where_no_print = "AND (c.CA_NOPRINT2 IS NULL OR c.CA_NOPRINT2 <> 'Y')"

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                c.CA_DOCKNO,
                b.CB_DRIVER,
                c.CA_NAME,
                CEIL(SUM(b.B_KG)) AS total_kg
            FROM t_balju b
            LEFT JOIN t_car c
                ON b.CB_DRIVER = c.CB_DRIVER
            WHERE b.B_DATE = %s
              {where_no_print}
            GROUP BY
                c.CA_DOCKNO,
                b.CB_DRIVER,
                c.CA_NAME
            ORDER BY
                c.CA_DOCKNO
            """,
            (selected_date,)
        )

        rows = [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

        rows = sorted(
            rows,
            key=lambda x: str(x.get("CA_NAME", ""))
        )

        return rows