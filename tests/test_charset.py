from db import engine

with engine.connect() as conn:

    result = conn.exec_driver_sql(
        "SHOW VARIABLES"
    )

    for row in result:
        if "character" in row[0]:
            print(row)