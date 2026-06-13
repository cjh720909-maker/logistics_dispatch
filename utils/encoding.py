def fix_encoding(value):

    if value is None:
        return value

    if not isinstance(value, str):
        return value

    try:
        return value.encode("latin1").decode("cp949")
    except Exception:
        return value


def fix_row(row):

    fixed = {}

    for key, value in row.items():
        fixed[key] = fix_encoding(value)

    return fixed

def get_pick_type(value):
    text = fix_encoding(value)

    if not text:
        return "기타"

    if "김류" in text:
        return "김류"

    if "냉동" in text:
        return "냉동"

    if "콩나물" in text:
        return "콩나물"

    return "기타"