from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7), "WIB")


def now_utc():
    return datetime.now(timezone.utc)


def now_iso():
    return now_utc().isoformat(timespec="seconds")


def to_utc_iso(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=WIB)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def to_wib(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WIB)


def fmt_wib(value, fmt="%d-%m-%Y %H:%M"):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    return to_wib(dt).strftime(fmt)
