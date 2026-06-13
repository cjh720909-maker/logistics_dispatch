from db import engine


def main():
    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                COUNT(*) AS total_count
            FROM t_balju
            """
        )

        row = result.mappings().first()

        print("DB 연결 성공")
        print("t_balju 총 건수:", row["total_count"])


if __name__ == "__main__":
    main()