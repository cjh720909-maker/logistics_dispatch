from db import engine
from utils.encoding import fix_row
from db_local import local_engine


def encode_kr(value):
    if not value:
        return value

    return value.encode("cp949").decode("latin1")

def get_product_130_list(filters):
    where = []
    params = []

    product_name = filters.get("product_name")
    product_code = filters.get("product_code")
    base_category = filters.get("base_category")
    picking_category = filters.get("picking_category")
    integrated = filters.get("integrated")

    if product_name:
        where.append("name LIKE ?")
        params.append(f"%{product_name}%")

    if product_code:
        where.append("code LIKE ?")
        params.append(f"%{product_code}%")

    if base_category:
        where.append("base_category LIKE ?")
        params.append(f"%{base_category}%")

    if picking_category:
        where.append("pick_category LIKE ?")
        params.append(f"%{picking_category}%")

    if integrated:
        where.append(
            """
            (
                name LIKE ?
                OR code LIKE ?
                OR barcode LIKE ?
                OR box_barcode LIKE ?
            )
            """
        )
        params.extend([
            f"%{integrated}%",
            f"%{integrated}%",
            f"%{integrated}%",
            f"%{integrated}%",
        ])

    where_sql = ""

    if where:
        where_sql = "WHERE " + " AND ".join(where)

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                code          AS PRODUCT_CODE,
                name          AS PRODUCT_NAME,
                base_category AS BASE_CATEGORY,
                pick_category AS PICK_CATEGORY,
                ipsu          AS IPSU,
                barcode       AS BARCODE,
                box_barcode   AS BOX_BARCODE,
                weight        AS WEIGHT
            FROM product
            {where_sql}
            ORDER BY
                name
            LIMIT 500
            """,
            tuple(params)
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

def get_customer_110_list(filters):
    where = []
    params = []

    customer_name = filters.get("customer_name")
    customer_code = filters.get("customer_code")
    integrated = filters.get("integrated")

    if customer_name:
        where.append("name LIKE ?")
        params.append(f"%{customer_name}%")

    if customer_code:
        where.append("code LIKE ?")
        params.append(f"%{customer_code}%")

    if integrated:
        where.append("""
            (
                name LIKE ?
                OR code LIKE ?
                OR business_no LIKE ?
                OR ceo LIKE ?
                OR address LIKE ?
                OR tel LIKE ?
            )
        """)
        params.extend([f"%{integrated}%"] * 6)

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                code        AS CUSTOMER_CODE,
                name        AS CUSTOMER_NAME,
                business_no AS BUSINESS_NO,
                ceo         AS CEO_NAME,
                address     AS ADDRESS,
                tel         AS TEL,
                print_type  AS PRINT_TYPE,
                das_time    AS DAS_TIME,
                memo        AS MEMO
            FROM customer
            {where_sql}
            ORDER BY
                name
            LIMIT 500
            """,
            tuple(params)
        )

        return [dict(row) for row in result.mappings().all()]

def get_delivery_customer_120_list(filters):
    where = []
    params = []

    delivery_name = filters.get("delivery_name")
    dispatch_name = filters.get("dispatch_name")
    address = filters.get("address")
    integrated = filters.get("integrated")

    if delivery_name:
        where.append("name LIKE ?")
        params.append(f"%{delivery_name}%")

    if dispatch_name:
        where.append("dispatch_name LIKE ?")
        params.append(f"%{dispatch_name}%")

    if address:
        where.append("address LIKE ?")
        params.append(f"%{address}%")

    if integrated:
        where.append("""
            (
                code LIKE ?
                OR name LIKE ?
                OR dispatch_name LIKE ?
                OR customer_code LIKE ?
                OR address LIKE ?
                OR phone LIKE ?
                OR mobile LIKE ?
                OR manager LIKE ?
                OR shared_vehicle LIKE ?
                OR memo LIKE ?
            )
        """)
        params.extend([f"%{integrated}%"] * 10)

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                code           AS DELIVERY_CODE,
                name           AS DELIVERY_NAME,
                dispatch_name  AS DISPATCH_NAME,
                customer_code  AS CUSTOMER_GROUP,
                address        AS ADDRESS,
                phone          AS PHONE,
                mobile         AS MOBILE,
                manager        AS MANAGER,
                shared_vehicle AS SHARED_VEHICLE,
                memo           AS MEMO
            FROM delivery
            {where_sql}
            ORDER BY
                name
            LIMIT 500
            """,
            tuple(params)
        )

        return [dict(row) for row in result.mappings().all()]

def get_vehicle_driver_140_list(filters):
    where = []
    params = []

    driver_name = filters.get("driver_name")
    dispatch_name = filters.get("dispatch_name")
    area_name = filters.get("area_name")
    integrated = filters.get("integrated")

    if driver_name:
        where.append("driver_name LIKE ?")
        params.append(f"%{driver_name}%")

    if dispatch_name:
        where.append("dispatch_name LIKE ?")
        params.append(f"%{dispatch_name}%")

    if area_name:
        where.append("area_name LIKE ?")
        params.append(f"%{area_name}%")

    if integrated:
        where.append("""
            (
                dock_no LIKE ?
                OR area_name LIKE ?
                OR driver_name LIKE ?
                OR dispatch_name LIKE ?
                OR phone LIKE ?
                OR car_no LIKE ?
                OR memo LIKE ?
            )
        """)
        params.extend([f"%{integrated}%"] * 7)

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    with local_engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                dock_no            AS DOCK_NO,
                area_name          AS AREA_NAME,
                driver_name        AS DRIVER_NAME,
                dispatch_name      AS DISPATCH_NAME,
                phone              AS PHONE,
                car_no             AS CAR_NO,
                capacity_ton       AS CAPACITY_TON,
                skip_invoice_print AS SKIP_INVOICE_PRINT,
                skip_route_print   AS SKIP_ROUTE_PRINT,
                skip_loading_print AS SKIP_LOADING_PRINT,
                das_morning_line   AS DAS_MORNING_LINE,
                das_morning_no     AS DAS_MORNING_NO,
                das_afternoon_line AS DAS_AFTERNOON_LINE,
                das_afternoon_no   AS DAS_AFTERNOON_NO,
                das_evening_line   AS DAS_EVENING_LINE,
                das_evening_no     AS DAS_EVENING_NO,
                memo               AS MEMO
            FROM vehicle
            {where_sql}
            ORDER BY
                driver_name,
                dispatch_name
            LIMIT 500
            """,
            tuple(params)
        )

        return [dict(row) for row in result.mappings().all()]