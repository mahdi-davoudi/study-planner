from datetime import datetime
from i18n import tr

def minutes_to_hm_text(total_minutes: int | None) -> str:
    hours, minutes = divmod(total_minutes or 0, 60)
    if hours and minutes:
        return tr("time.both", h=hours, m=minutes)
    if hours:
        return tr("time.hours", h=hours)
    return tr("time.minutes", m=minutes)


def hm_to_minutes(hours_str: str, minutes_str: str) -> int:
    try:
        h = int(hours_str) if hours_str and hours_str.strip() else 0
    except ValueError:
        h = 0
    try:
        m = int(minutes_str) if minutes_str and minutes_str.strip() else 0
    except ValueError:
        m = 0
    return h * 60 + m


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def now_iso() -> str:
    return datetime.now().isoformat()