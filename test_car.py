from db import engine

with engine.connect() as conn:

    result = conn.exec_driver_sql(
        """
        SELECT
            CA_NAME,
            CB_DRIVER
        FROM t_car
        LIMIT 3
        """
    )

    rows = result.fetchall()

    for row in rows:
        print(row)
        print(type(row[0]))