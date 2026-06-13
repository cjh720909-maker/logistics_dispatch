from db import engine


def main():
    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                B_DATE,
                CB_DRIVER,
                B_C_NAME,
                B_P_NAME,
                B_QTY,
                B_KG
            FROM t_balju
            ORDER BY B_DATE DESC
            LIMIT 20
            """
        )

        rows = result.mappings().all()

        for row in rows:
            print(row)


if __name__ == "__main__":
    main()