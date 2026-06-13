import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from db import engine
from utils.encoding import fix_encoding


def main():

    with engine.connect() as conn:

        result = conn.exec_driver_sql(
            """
            SELECT DISTINCT
                P_DIV_PICK
            FROM t_product
            LIMIT 50
            """
        )

        rows = result.fetchall()

        print()
        print("===== P_DIV_PICK 목록 =====")
        print()

        for row in rows:

            value = row[0]

            print(
                fix_encoding(value)
            )


if __name__ == "__main__":
    main()