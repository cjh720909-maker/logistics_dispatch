# tests/test_frozen_detail.py

import sys
from pathlib import Path
import math

sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import engine
from utils.encoding import fix_encoding, get_pick_type


selected_date = "2026-06-13"
driver = "배연환"  # 여기 바꿔서 테스트
raw_driver = driver.encode("cp949").decode("latin1")


with engine.connect() as conn:
    result = conn.exec_driver_sql(
        """
        SELECT
            b.CB_DRIVER,
            b.B_P_NO,
            b.B_P_NAME,
            b.B_QTY,
            p.P_DIV_PICK,
            p.P_IPSU
        FROM t_balju b
        LEFT JOIN (
            SELECT
                P_CODE,
                MAX(P_DIV_PICK) AS P_DIV_PICK,
                MAX(P_IPSU) AS P_IPSU
            FROM t_product
            GROUP BY P_CODE
        ) p
            ON b.B_P_NO = p.P_CODE
        WHERE b.B_DATE = %s
          AND b.CB_DRIVER = %s
        """,
        (selected_date, raw_driver)
    )

    rows = result.mappings().all()

    total_box = 0

    for row in rows:
        pick_type = get_pick_type(row["P_DIV_PICK"])

        if pick_type != "냉동":
            continue

        qty = float(row["B_QTY"] or 0)
        ipsu = float(row["P_IPSU"] or 0)

        box = qty / ipsu if ipsu > 0 else qty
        total_box += box

        print(
            "코드:", row["B_P_NO"],
            fix_encoding(row["B_P_NAME"]),
            "수량:", qty,
            "입수:", ipsu,
            "박스:", round(box, 2),
            "분류:", fix_encoding(row["P_DIV_PICK"])
        )

    print("냉동 박스 소수 합:", total_box)
    print("냉동 박스 올림:", math.ceil(total_box))