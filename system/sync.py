from datetime import datetime
from decimal import Decimal

from db import engine
from db_local import local_engine
from utils.encoding import fix_row


def to_float(value):
    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    return value


def sync_product():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT,
                base_category TEXT,
                pick_category TEXT,
                barcode TEXT,
                box_barcode TEXT,
                ipsu REAL,
                weight REAL,
                synced_at TEXT
            )
            """
        )

        conn.exec_driver_sql(
            """
            CREATE INDEX IF NOT EXISTS idx_product_code
            ON product(code)
            """
        )

    with engine.connect() as source_conn:
        result = source_conn.exec_driver_sql(
            """
            SELECT
                P_CODE      AS code,
                P_NAME      AS name,
                P_DIV_BAS   AS base_category,
                P_DIV_PICK  AS pick_category,
                P_BARCODE   AS barcode,
                P_BARCODE2  AS box_barcode,
                P_IPSU      AS ipsu,
                P_KG        AS weight
            FROM t_product
            """
        )

        rows = [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

    synced_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with local_engine.begin() as local_conn:
        local_conn.exec_driver_sql("DELETE FROM product")

        for row in rows:
            local_conn.exec_driver_sql(
                """
                INSERT INTO product (
                    code,
                    name,
                    base_category,
                    pick_category,
                    barcode,
                    box_barcode,
                    ipsu,
                    weight,
                    synced_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("code"),
                    row.get("name"),
                    row.get("base_category"),
                    row.get("pick_category"),
                    row.get("barcode"),
                    row.get("box_barcode"),
                    to_float(row.get("ipsu")),
                    to_float(row.get("weight")),
                    synced_at,
                )
            )
    save_sync_log(
        "product",
        "t_product",
        "product",
        synced_at,
        len(rows)
    )

    return {
        "success": True,
        "message": f"제품 동기화 완료: {len(rows)}건",
        "count": len(rows),
    }

def sync_customer():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT,
                business_no TEXT,
                ceo TEXT,
                address TEXT,
                tel TEXT,
                print_type TEXT,
                das_time TEXT,
                memo TEXT,
                synced_at TEXT
            )
            """
        )

        conn.exec_driver_sql(
            """
            CREATE INDEX IF NOT EXISTS idx_customer_code
            ON customer(code)
            """
        )

    with engine.connect() as source_conn:
        result = source_conn.exec_driver_sql(
            """
            SELECT
                CB_DIV_CUST AS code,
                C_NAME      AS name,
                C_SANO      AS business_no,
                C_CEO       AS ceo,
                C_ADDRESS   AS address,
                C_TEL       AS tel,
                C_PRINT_DIV AS print_type,
                C_DAS_NUM   AS das_time,
                C_MEMO      AS memo
            FROM t_cust
            """
        )

        rows = [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

    synced_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with local_engine.begin() as local_conn:
        local_conn.exec_driver_sql("DELETE FROM customer")

        for row in rows:
            local_conn.exec_driver_sql(
                """
                INSERT INTO customer (
                    code,
                    name,
                    business_no,
                    ceo,
                    address,
                    tel,
                    print_type,
                    das_time,
                    memo,
                    synced_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("code"),
                    row.get("name"),
                    row.get("business_no"),
                    row.get("ceo"),
                    row.get("address"),
                    row.get("tel"),
                    row.get("print_type"),
                    row.get("das_time"),
                    row.get("memo"),
                    synced_at,
                )
            )

    save_sync_log(
        "customer",
        "t_cust",
        "customer",
        synced_at,
        len(rows)
    )
    return {
        "success": True,
        "message": f"고객사 동기화 완료: {len(rows)}건",
        "count": len(rows),
    }

def sync_delivery():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS delivery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT,
                dispatch_name TEXT,
                customer_code TEXT,
                address TEXT,
                phone TEXT,
                mobile TEXT,
                manager TEXT,
                shared_vehicle TEXT,
                memo TEXT,
                synced_at TEXT
            )
            """
        )

        conn.exec_driver_sql(
            """
            CREATE INDEX IF NOT EXISTS idx_delivery_code
            ON delivery(code)
            """
        )

        conn.exec_driver_sql(
            """
            CREATE INDEX IF NOT EXISTS idx_delivery_name
            ON delivery(name)
            """
        )

    with engine.connect() as source_conn:
        result = source_conn.exec_driver_sql(
            """
            SELECT
                CB_CODE     AS code,
                CB_NAME     AS name,
                CB_DRIVER   AS dispatch_name,
                CB_DIV_CUST AS customer_code,
                CB_ADDRESS  AS address,
                CB_PHONE    AS phone,
                CB_HP       AS mobile,
                CB_DAMDANG  AS manager,
                CB_GONG     AS shared_vehicle,
                CB_MEMO     AS memo
            FROM t_cust_bae
            """
        )

        rows = [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

    synced_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with local_engine.begin() as local_conn:
        local_conn.exec_driver_sql("DELETE FROM delivery")

        for row in rows:
            local_conn.exec_driver_sql(
                """
                INSERT INTO delivery (
                    code,
                    name,
                    dispatch_name,
                    customer_code,
                    address,
                    phone,
                    mobile,
                    manager,
                    shared_vehicle,
                    memo,
                    synced_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("code"),
                    row.get("name"),
                    row.get("dispatch_name"),
                    row.get("customer_code"),
                    row.get("address"),
                    row.get("phone"),
                    row.get("mobile"),
                    row.get("manager"),
                    row.get("shared_vehicle"),
                    row.get("memo"),
                    synced_at,
                )
            )
    save_sync_log(
        "delivery",
        "t_cust_bae",
        "delivery",
        synced_at,
        len(rows)
    )

    return {
        "success": True,
        "message": f"거래처 동기화 완료: {len(rows)}건",
        "count": len(rows),
    }

def sync_vehicle():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS vehicle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dock_no TEXT,
                area_name TEXT,
                driver_name TEXT,
                dispatch_name TEXT,
                phone TEXT,
                car_no TEXT,
                capacity_ton REAL,
                skip_invoice_print TEXT,
                skip_route_print TEXT,
                skip_loading_print TEXT,
                das_morning_line TEXT,
                das_morning_no TEXT,
                das_afternoon_line TEXT,
                das_afternoon_no TEXT,
                das_evening_line TEXT,
                das_evening_no TEXT,
                memo TEXT,
                synced_at TEXT
            )
            """
        )

        conn.exec_driver_sql(
            """
            CREATE INDEX IF NOT EXISTS idx_vehicle_dispatch_name
            ON vehicle(dispatch_name)
            """
        )

        conn.exec_driver_sql(
            """
            CREATE INDEX IF NOT EXISTS idx_vehicle_driver_name
            ON vehicle(driver_name)
            """
        )

    with engine.connect() as source_conn:
        result = source_conn.exec_driver_sql(
            """
            SELECT
                CA_DOCKNO   AS dock_no,
                CA_GUN      AS area_name,
                CA_NAME     AS driver_name,
                CB_DRIVER   AS dispatch_name,
                CA_HP       AS phone,
                CA_NO    AS car_no,
                CA_KG       AS capacity_ton,
                CA_NOPRINT  AS skip_invoice_print,
                CA_NOPRINT1 AS skip_route_print,
                CA_NOPRINT2 AS skip_loading_print,
                CA_DAS_NUM_C1 AS das_morning_line,
                CA_DAS_NUM_1  AS das_morning_no,
                CA_DAS_NUM_C2 AS das_afternoon_line,
                CA_DAS_NUM_2  AS das_afternoon_no,
                CA_DAS_NUM_C3 AS das_evening_line,
                CA_DAS_NUM_3  AS das_evening_no,
                CA_MEMO     AS memo
            FROM t_car
            """
        )

        rows = [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

    synced_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with local_engine.begin() as local_conn:
        local_conn.exec_driver_sql("DELETE FROM vehicle")

        for row in rows:
            local_conn.exec_driver_sql(
                """
                INSERT INTO vehicle (
                    dock_no,
                    area_name,
                    driver_name,
                    dispatch_name,
                    phone,
                    car_no,
                    capacity_ton,
                    skip_invoice_print,
                    skip_route_print,
                    skip_loading_print,
                    das_morning_line,
                    das_morning_no,
                    das_afternoon_line,
                    das_afternoon_no,
                    das_evening_line,
                    das_evening_no,
                    memo,
                    synced_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("dock_no"),
                    row.get("area_name"),
                    row.get("driver_name"),
                    row.get("dispatch_name"),
                    row.get("phone"),
                    row.get("car_no"),
                    to_float(row.get("capacity_ton")),
                    row.get("skip_invoice_print"),
                    row.get("skip_route_print"),
                    row.get("skip_loading_print"),
                    row.get("das_morning_line"),
                    row.get("das_morning_no"),
                    row.get("das_afternoon_line"),
                    row.get("das_afternoon_no"),
                    row.get("das_evening_line"),
                    row.get("das_evening_no"),
                    row.get("memo"),
                    synced_at,
                )
            )

    save_sync_log(
        "vehicle",
        "t_car",
        "vehicle",
        synced_at,
        len(rows)
    )
    return {
        "success": True,
        "message": f"차량 동기화 완료: {len(rows)}건",
        "count": len(rows),
    }

def create_sync_log_table():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS sync_log (
                target TEXT PRIMARY KEY,
                source_table TEXT,
                local_table TEXT,
                synced_at TEXT,
                row_count INTEGER
            )
            """
        )


def save_sync_log(target, source_table, local_table, synced_at, row_count):
    create_sync_log_table()

    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            INSERT OR REPLACE INTO sync_log (
                target,
                source_table,
                local_table,
                synced_at,
                row_count
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                target,
                source_table,
                local_table,
                synced_at,
                row_count,
            )
        )


def get_sync_status():
    create_sync_log_table()

    status = {
        "product": None,
        "customer": None,
        "delivery": None,
        "vehicle": None,
    }

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                target,
                synced_at,
                row_count
            FROM sync_log
            """
        )

        for row in result.mappings().all():
            status[row["target"]] = {
                "synced_at": row["synced_at"],
                "row_count": row["row_count"],
            }

    return status