# test_fix.py

from db import engine


def fix_encoding(value):

    if not value:
        return value

    try:
        return value.encode("latin1").decode("cp949")
    except Exception:
        return value


with engine.connect() as conn:

    result = conn.exec_driver_sql(
        """
        SELECT
            CA_NAME,
            CB_DRIVER
        FROM t_car
        LIMIT 5
        """
    )

    rows = result.mappings().all()

    for row in rows:

        print(
            fix_encoding(row["CA_NAME"]),
            fix_encoding(row["CB_DRIVER"])
        )