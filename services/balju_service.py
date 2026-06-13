import base64
from decimal import Decimal

from db import engine
from utils.encoding import fix_encoding, fix_row


def make_vehicle_key(raw_gun, raw_name):
    value = f"{raw_gun or ''}||{raw_name or ''}"
    return base64.urlsafe_b64encode(
        value.encode("latin1")
    ).decode("ascii")


def read_vehicle_key(vehicle_key):
    if not vehicle_key:
        return None, None

    value = base64.urlsafe_b64decode(
        vehicle_key.encode("ascii")
    ).decode("latin1")

    raw_gun, raw_name = value.split("||", 1)

    return raw_gun, raw_name


def to_float(value):
    if value is None:
        return 0

    if isinstance(value, Decimal):
        return float(value)

    return float(value)


def get_dispatch_summary_by_date(selected_date):
    if not selected_date:
        return []

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.CB_DRIVER,
                c.CA_GUN,
                c.CA_NAME,
                c.CA_DOCKNO,
                c.CA_KG,
                COUNT(DISTINCT b.B_C_CODE) AS customer_count,
                COUNT(*) AS item_count,
                SUM(b.B_QTY) AS total_qty,
                SUM(b.B_KG) AS total_kg
            FROM t_balju b
            LEFT JOIN t_car c
                ON b.CB_DRIVER = c.CB_DRIVER
            WHERE b.B_DATE = %s
            GROUP BY
                b.CB_DRIVER,
                c.CA_GUN,
                c.CA_NAME,
                c.CA_DOCKNO,
                c.CA_KG
            LIMIT 300
            """,
            (selected_date,)
        )

        rows = result.mappings().all()

        fixed_rows = []
        vehicle_total_map = {}

        for row in rows:
            row = dict(row)

            raw_gun = row["CA_GUN"]
            raw_name = row["CA_NAME"]

            vehicle_key = f"{raw_gun or ''}||{raw_name or ''}"

            vehicle_total_map[vehicle_key] = (
                vehicle_total_map.get(vehicle_key, 0)
                + to_float(row["total_kg"])
            )

        for row in rows:
            row = dict(row)

            raw_driver = row["CB_DRIVER"]
            raw_gun = row["CA_GUN"]
            raw_name = row["CA_NAME"]

            net_kg = to_float(row["total_kg"])

            vehicle_key_value = f"{raw_gun or ''}||{raw_name or ''}"
            total_kg = vehicle_total_map.get(vehicle_key_value, 0)

            net_kg = round(net_kg)
            total_kg = round(total_kg)

            car_ton = to_float(row["CA_KG"])
            capacity_kg = car_ton * 1000
            capacity_kg = round(capacity_kg)

            if capacity_kg > 0:
                load_rate = int(round(
                    (total_kg / capacity_kg) * 100
                ))
            else:
                load_rate = 0

            fixed_rows.append({
                "vehicle_key": make_vehicle_key(raw_gun, raw_name),
                "CB_DRIVER": fix_encoding(raw_driver),
                "CA_GUN": fix_encoding(raw_gun),
                "CA_NAME": fix_encoding(raw_name),
                "CA_DOCKNO": row["CA_DOCKNO"],
                "CA_KG": car_ton,
                "capacity_kg": capacity_kg,
                "customer_count": row["customer_count"],
                "item_count": row["item_count"],
                "total_qty": row["total_qty"],
                "net_kg": net_kg,
                "total_kg": total_kg,
                "load_rate": load_rate,
            })

        fixed_rows.sort(
            key=lambda row: (
                row["CA_GUN"] or "",
                row["CA_NAME"] or "",
                0 if row["CB_DRIVER"] == row["CA_NAME"] else 1,
                row["CB_DRIVER"] or "",
            )
        )
        shown_vehicle_keys = set()

        for row in fixed_rows:
            key = row["vehicle_key"]

            if key in shown_vehicle_keys:
                row["show_vehicle_total"] = False
            else:
                row["show_vehicle_total"] = True
                shown_vehicle_keys.add(key)

        return fixed_rows


def get_customer_list_by_vehicle_key(selected_date, vehicle_key):
    if not selected_date or not vehicle_key:
        return []

    raw_gun, raw_name = read_vehicle_key(vehicle_key)

    with engine.connect() as conn:
        result = conn.exec_driver_sql(
            """
            SELECT
                b.B_C_CODE,
                b.B_C_NAME,
                b.B_C_PAN_NAME,
                b.CB_ADDRESS,
                COUNT(*) AS item_count,
                SUM(b.B_QTY) AS total_qty,
                SUM(b.B_KG) AS total_kg
            FROM t_balju b
            LEFT JOIN t_car c
                ON b.CB_DRIVER = c.CB_DRIVER
            WHERE b.B_DATE = %s
              AND c.CA_GUN = %s
              AND c.CA_NAME = %s
            GROUP BY
                b.B_C_CODE,
                b.B_C_NAME,
                b.B_C_PAN_NAME,
                b.CB_ADDRESS
            ORDER BY b.B_C_NAME
            LIMIT 300
            """,
            (selected_date, raw_gun, raw_name)
        )

        rows = result.mappings().all()

        return [
            fix_row(dict(row))
            for row in rows
        ]

def get_dispatch_total(dispatch_list):
    total_kg = 0
    total_capacity_kg = 0

    for row in dispatch_list:
        total_kg += row.get("total_kg", 0) or 0
        total_capacity_kg += row.get("capacity_kg", 0) or 0

    if total_capacity_kg > 0:
        total_load_rate = round((total_kg / total_capacity_kg) * 100, 1)
    else:
        total_load_rate = 0

    return {
        "total_kg": round(total_kg),
        "total_capacity_kg": round(total_capacity_kg),
        "total_load_rate": round(total_load_rate),
    }