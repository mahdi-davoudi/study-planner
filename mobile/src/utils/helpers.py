from __future__ import annotations

from datetime import datetime

from i18n import tr


def minutes_to_hm_text(total_minutes: int | None) -> str:
    total = int(total_minutes or 0)
    hours, minutes = divmod(total, 60)
    if hours and minutes:
        return tr("time.both", h=hours, m=minutes)
    if hours:
        return tr("time.hours", h=hours)
    return tr("time.minutes", m=minutes)


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now().isoformat()


def parse_hhmm(text: str) -> tuple[int, int] | None:
    """'20:30' -> (20, 30). Returns None for anything invalid."""
    try:
        hour_text, minute_text = text.strip().split(":")
        hour, minute = int(hour_text), int(minute_text)
    except ValueError:
        return None
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    return None


def to_12h(hour24: int) -> tuple[int, str]:
    """0..23 -> (1..12, 'am' | 'pm').  0 -> (12, am), 12 -> (12, pm)."""
    return hour24 % 12 or 12, ("pm" if hour24 >= 12 else "am")


def to_24h(hour12: int, suffix: str) -> int:
    """(1..12, 'am' | 'pm') -> 0..23.  (12, am) -> 0, (12, pm) -> 12."""
    return hour12 % 12 + (12 if suffix == "pm" else 0)
