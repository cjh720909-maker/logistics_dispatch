def blank_zero(value):
    if value in (0, 0.0, None):
        return ""
    return value


def number_format(value):
    if value is None:
        return ""
    return f"{value:,}"


def blank_none(value):
    return "" if value is None else value