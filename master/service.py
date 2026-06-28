from db import engine
from utils.encoding import fix_row


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
        where.append("p.P_NAME LIKE %s")
        params.append(f"%{encode_kr(product_name)}%")

    if product_code:
        where.append("p.P_CODE LIKE %s")
        params.append(f"%{product_code}%")

    if base_category:
        where.append("p.P_DIV_BAS LIKE %s")
        params.append(f"%{encode_kr(base_category)}%")

    if picking_category:
        where.append("p.P_DIV_PICK LIKE %s")
        params.append(f"%{encode_kr(picking_category)}%")

    if integrated:
        raw_keyword = encode_kr(integrated)
        where.append(
            """
            (
                p.P_NAME LIKE %s
                OR p.P_CODE LIKE %s
                OR p.P_BARCODE LIKE %s
                OR p.P_BOX_BARCODE LIKE %s
            )
            """
        )
        params.extend([
            f"%{raw_keyword}%",
            f"%{integrated}%",
            f"%{integrated}%",
            f"%{integrated}%",
        ])

    where_sql = ""

    if where:
        where_sql = "WHERE " + " AND ".join(where)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                p.P_CODE,
                p.P_NAME,
                p.P_DIV_BAS,
                p.P_DIV_PICK,
                p.P_IPSU,
                p.P_BARCODE,
                p.P_BARCODE2 AS P_BOX_BARCODE,
                p.P_KG
            FROM t_product p
            {where_sql}
            ORDER BY
                p.P_NAME
            LIMIT 500
            """,
            tuple(params)
        )

        return [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

def get_vehicle_driver_140_list(filters):
    where = []
    params = []

    driver_name = filters.get("driver_name")
    dispatch_name = filters.get("dispatch_name")
    area_name = filters.get("area_name")
    integrated = filters.get("integrated")

    if driver_name:
        where.append("c.CA_NAME LIKE %s")
        params.append(f"%{encode_kr(driver_name)}%")

    if dispatch_name:
        where.append("c.CB_DRIVER LIKE %s")
        params.append(f"%{encode_kr(dispatch_name)}%")

    if area_name:
        where.append("c.CA_GUN LIKE %s")
        params.append(f"%{encode_kr(area_name)}%")

    if integrated:
        raw_keyword = encode_kr(integrated)
        where.append(
            """
            (
                c.CA_NAME LIKE %s
                OR c.CB_DRIVER LIKE %s
                OR c.CA_GUN LIKE %s
                OR c.CA_DOCKNO LIKE %s
            )
            """
        )
        params.extend([
            f"%{raw_keyword}%",
            f"%{raw_keyword}%",
            f"%{raw_keyword}%",
            f"%{integrated}%",
        ])

    where_sql = ""

    if where:
        where_sql = "WHERE " + " AND ".join(where)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                c.CA_IDX       AS CAR_ID,
                c.CA_DOCKNO    AS DOCK_NO,
                c.CA_GUN       AS AREA_NAME,
                c.CA_NAME      AS DRIVER_NAME,
                c.CB_DRIVER    AS DISPATCH_NAME,
                c.CA_KG        AS CAPACITY_TON,
                c.CA_NOPRINT   AS SKIP_INVOICE_PRINT,
                c.CA_NOPRINT1  AS SKIP_ROUTE_PRINT,
                c.CA_NOPRINT2  AS SKIP_LOADING_PRINT
            FROM t_car c
            {where_sql}
            ORDER BY
                c.CA_NAME,
                c.CB_DRIVER
            LIMIT 500
            """,
            tuple(params)
        )

        return [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]

def get_delivery_customer_120_list(filters):
    where = []
    params = []

    delivery_name = filters.get("delivery_name")
    dispatch_name = filters.get("dispatch_name")
    address = filters.get("address")
    integrated = filters.get("integrated")

    if delivery_name:
        where.append("c.CB_NAME LIKE %s")
        params.append(f"%{encode_kr(delivery_name)}%")

    if dispatch_name:
        where.append("c.CB_DRIVER LIKE %s")
        params.append(f"%{encode_kr(dispatch_name)}%")

    if address:
        where.append("c.CB_ADDRESS LIKE %s")
        params.append(f"%{encode_kr(address)}%")

    if integrated:
        keyword = encode_kr(integrated)
        where.append("""
            (
                c.CB_NAME LIKE %s
                OR c.CB_DRIVER LIKE %s
                OR c.CB_DIV_CUST LIKE %s
                OR c.CB_ADDRESS LIKE %s
                OR c.CB_PHONE LIKE %s
                OR c.CB_HP LIKE %s
                OR c.CB_CODE LIKE %s
                OR c.CB_MEMO LIKE %s
            )
        """)
        params.extend([f"%{keyword}%"] * 8)

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                c.CB_IDX       AS DELIVERY_ID,
                c.CB_CODE      AS DELIVERY_CODE,
                c.CB_NAME      AS DELIVERY_NAME,
                c.CB_DRIVER    AS DISPATCH_NAME,
                c.CB_DIV_CUST  AS CUSTOMER_GROUP,
                c.CB_ADDRESS   AS ADDRESS,
                c.CB_PHONE     AS PHONE,
                c.CB_HP        AS MOBILE,
                c.CB_DAMDANG   AS MANAGER,
                c.CB_GONG      AS SHARED_VEHICLE,
                c.CB_MEMO      AS MEMO
            FROM t_cust_bae c
            {where_sql}
            ORDER BY
                c.CB_NAME
            LIMIT 500
            """,
            tuple(params)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]

def get_customer_110_list(filters):
    where = []
    params = []

    customer_name = filters.get("customer_name")
    customer_code = filters.get("customer_code")
    integrated = filters.get("integrated")

    if customer_name:
        where.append("c.C_NAME LIKE %s")
        params.append(f"%{encode_kr(customer_name)}%")

    if customer_code:
        where.append("c.CB_DIV_CUST LIKE %s")
        params.append(f"%{encode_kr(customer_code)}%")

    if integrated:
        raw_keyword = encode_kr(integrated)

        where.append("""
            (
                c.C_NAME LIKE %s
                OR c.CB_DIV_CUST LIKE %s
                OR c.C_ADDRESS LIKE %s
                OR c.C_CEO LIKE %s
                OR c.C_TEL LIKE %s
            )
        """)

        params.extend([
            f"%{raw_keyword}%",
            f"%{raw_keyword}%",
            f"%{raw_keyword}%",
            f"%{raw_keyword}%",
            f"%{raw_keyword}%",
        ])

    where_sql = ""

    if where:
        where_sql = "WHERE " + " AND ".join(where)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            f"""
            SELECT
                c.C_IDX       AS CUSTOMER_ID,
                c.C_NAME      AS CUSTOMER_NAME,
                c.CB_DIV_CUST AS CUSTOMER_CODE,
                c.C_SANO      AS BUSINESS_NO,
                c.C_CEO       AS CEO_NAME,
                c.C_ADDRESS   AS ADDRESS,
                c.C_TEL       AS TEL,
                c.C_PRINT_DIV AS PRINT_TYPE,
                c.C_DAS_NUM   AS DAS_TIME,
                c.C_MEMO      AS MEMO
            FROM t_cust c
            {where_sql}
            ORDER BY
                c.C_NAME
            LIMIT 500
            """,
            tuple(params)
        )

        return [
            fix_row(dict(row))
            for row in result.mappings().all()
        ]