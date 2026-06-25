from datetime import datetime, timedelta


def get_default_work_date():
    now = datetime.now()

    if now.hour >= 18:
        target_date = now + timedelta(days=1)
    else:
        target_date = now

    return target_date.strftime("%Y-%m-%d")