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