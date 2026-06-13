from db import engine
from utils.encoding import fix_row

def get_car_list():

    with engine.connect() as conn:

        result = conn.exec_driver_sql(
            """
            SELECT
                CA_IDX,
                CA_NAME,
                CB_DRIVER,
                CA_DOCKNO,
                CA_GUN,
                CA_KG
            FROM t_car
            ORDER BY CA_IDX DESC
            LIMIT 100
            """
        )

    rows = result.mappings().all()

    return [
        fix_row(dict(row))
        for row in rows
    ]