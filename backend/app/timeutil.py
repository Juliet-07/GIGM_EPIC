from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

OPERATOR_TZ = ZoneInfo("Africa/Lagos")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def local_day_bounds_utc(day: date) -> tuple[datetime, datetime]:
    """[start, end) of a calendar day in Nigerian local time, expressed in UTC."""
    start_local = datetime.combine(day, time.min, tzinfo=OPERATOR_TZ)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)