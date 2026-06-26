from db import engine
from utils.encoding import fix_row


def encode_kr(value):
    if not value:
        return value
    return value.encode("cp949").decode("latin1")


def get_130_products(filters):
    where = []
    params = []

    if filters.get("product_name"):
        where.append("p.P_NAME LIKE %s")
        params.append(f"%{encode_kr(filters['product_name'])}%")

    if filters.get("product_code"):
        where.append("p.P_CODE LIKE %s")
        params.append(f"%{filters['product_code']}%")

    if filters.get("base_category"):
        where.append("p.P_DIV_BAS LIKE %s")
        params.append(f"%{encode_kr(filters['base_category'])}%")

    if filters.get("picking_category"):
        where.append("p.P_DIV_PICK LIKE %s")
        params.append(f"%{encode_kr(filters['picking_category'])}%")

    if filters.get("integrated"):
        keyword = f"%{encode_kr(filters['integrated'])}%"
        where.append("""
            (
                p.P_NAME LIKE %s
                OR p.P_CODE LIKE %s
                OR p.P_BARCODE LIKE %s
                OR p.P_BOX_BARCODE LIKE %s
            )
        """)
        params.extend([
            keyword,
            f"%{filters['integrated']}%",
            f"%{filters['integrated']}%",
            f"%{filters['integrated']}%",
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
                p.P_BARCODE2,
                p.P_KG
            FROM t_product p
            {where_sql}
            ORDER BY
                p.P_NAME
            LIMIT 500
            """,
            tuple(params)
        )

        return [fix_row(dict(row)) for row in result.mappings().all()]