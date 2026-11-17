from datetime import date, timedelta, timezone

from app.timeutil import local_day_bounds_utc, utcnow


def test_utcnow_is_timezone_aware_utc():
    assert utcnow().tzinfo is not None and utcnow().utcoffset() == timedelta(0)


def test_lagos_day_starts_one_hour_before_utc_midnight():
    start, end = local_day_bounds_utc(date(2026, 11, 14))
    assert (start.year, start.month, start.day, start.hour) == (2026, 11, 13, 23)
    assert start.tzinfo == timezone.utc
    assert end - start == timedelta(hours=24)