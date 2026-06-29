from datetime import datetime, timedelta
from decimal import Decimal

from db import engine
from db_local import local_engine
from utils.encoding import fix_row


def to_float(value):
    if value is None:
        return 0

    if isinstance(value, Decimal):
        return float(value)

    return value


def sync_dispatch_order(work_date):
    with engine.connect() as source_conn:
        result = source_conn.exec_driver_sql(
            """
            SELECT
                B_IDX,
                CB_IDX,
                CB_IDX_ORI,
                B_DATE,
                B_C_NAME_ORI,
                B_C_NAME,
                B_C_CODE,
                B_C_PAN_NAME_ORI,
                B_C_PAN_NAME,
                B_NAP_DIV_ORI,
                B_NAP_DIV,
                B_P_NO,
                B_P_NAME,
                B_DAN,
                B_VAT_DIV,
                B_KG,
                B_IN_QTY,
                B_QTY,
                B_PKG,
                B_NAP_NO,
                B_ORDER_NO,
                B_MEMO,
                B_EDT_E_NAME,
                C_NAME,
                B_EDT_DATETIME,
                CB_NAME,
                CB_DRIVER,
                CB_DIV_CUST,
                CB_ADDRESS,
                CB_PHONE,
                CB_HP,
                CB_BIND,
                CB_CODE,
                O_IDX,
                B_EX_SEQ,
                O_QTY,
                B_IN_CONFIRM,
                B_PICK_DONE,
                B_GUM_DONE,
                B_GUM_DATE,
                B_GUM_E_NAME,
                B_QTY_DAS_STCOK
            FROM t_balju
            WHERE B_DATE = %s
            """,
            (
                work_date,
            )
        )

        rows = [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

    with local_engine.begin() as local_conn:
        local_conn.exec_driver_sql(
            """
            DELETE FROM dispatch_order
            WHERE B_DATE = ?
            """,
            (
                work_date,
            )
        )

        for row in rows:
            local_conn.exec_driver_sql(
                """
                INSERT INTO dispatch_order (
                    B_IDX,
                    CB_IDX,
                    CB_IDX_ORI,
                    B_DATE,
                    B_C_NAME_ORI,
                    B_C_NAME,
                    B_C_CODE,
                    B_C_PAN_NAME_ORI,
                    B_C_PAN_NAME,
                    B_NAP_DIV_ORI,
                    B_NAP_DIV,
                    B_P_NO,
                    B_P_NAME,
                    B_DAN,
                    B_VAT_DIV,
                    B_KG,
                    B_IN_QTY,
                    B_QTY,
                    B_PKG,
                    B_NAP_NO,
                    B_ORDER_NO,
                    B_MEMO,
                    B_EDT_E_NAME,
                    C_NAME,
                    B_EDT_DATETIME,
                    CB_NAME,
                    CB_DRIVER,
                    CB_DIV_CUST,
                    CB_ADDRESS,
                    CB_PHONE,
                    CB_HP,
                    CB_BIND,
                    CB_CODE,
                    O_IDX,
                    B_EX_SEQ,
                    O_QTY,
                    B_IN_CONFIRM,
                    B_PICK_DONE,
                    B_GUM_DONE,
                    B_GUM_DATE,
                    B_GUM_E_NAME,
                    B_QTY_DAS_STCOK
                )
                VALUES (
                    ?,?,?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,?,?,
                    ?,?
                )
                """,
                (
                    row.get("B_IDX"),
                    row.get("CB_IDX"),
                    row.get("CB_IDX_ORI"),
                    row.get("B_DATE"),
                    row.get("B_C_NAME_ORI"),
                    row.get("B_C_NAME"),
                    row.get("B_C_CODE"),
                    row.get("B_C_PAN_NAME_ORI"),
                    row.get("B_C_PAN_NAME"),
                    row.get("B_NAP_DIV_ORI"),
                    row.get("B_NAP_DIV"),
                    row.get("B_P_NO"),
                    row.get("B_P_NAME"),
                    row.get("B_DAN"),
                    row.get("B_VAT_DIV"),
                    to_float(row.get("B_KG")),
                    to_float(row.get("B_IN_QTY")),
                    row.get("B_QTY"),
                    row.get("B_PKG"),
                    row.get("B_NAP_NO"),
                    row.get("B_ORDER_NO"),
                    row.get("B_MEMO"),
                    row.get("B_EDT_E_NAME"),
                    row.get("C_NAME"),
                    str(row.get("B_EDT_DATETIME")) if row.get("B_EDT_DATETIME") else None,
                    row.get("CB_NAME"),
                    row.get("CB_DRIVER"),
                    row.get("CB_DIV_CUST"),
                    row.get("CB_ADDRESS"),
                    row.get("CB_PHONE"),
                    row.get("CB_HP"),
                    row.get("CB_BIND"),
                    row.get("CB_CODE"),
                    row.get("O_IDX"),
                    row.get("B_EX_SEQ"),
                    row.get("O_QTY"),
                    row.get("B_IN_CONFIRM"),
                    row.get("B_PICK_DONE"),
                    row.get("B_GUM_DONE"),
                    str(row.get("B_GUM_DATE")) if row.get("B_GUM_DATE") else None,
                    row.get("B_GUM_E_NAME"),
                    row.get("B_QTY_DAS_STCOK"),
                )
            )

        cutoff_date = (
            datetime.strptime(work_date, "%Y-%m-%d") - timedelta(days=5)
        ).strftime("%Y-%m-%d")

        local_conn.exec_driver_sql(
            """
            DELETE FROM dispatch_order
            WHERE B_DATE < ?
            """,
            (
                cutoff_date,
            )
        )

    return {
        "success": True,
        "message": f"발주 동기화 완료: {work_date} / {len(rows)}건",
        "count": len(rows),
    }