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