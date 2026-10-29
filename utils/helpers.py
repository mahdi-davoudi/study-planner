"""Small date/time helpers shared by the database layer and the UI."""

from __future__ import annotations

from datetime import datetime


def minutes_to_hm_text(total_minutes: int | None) -> str:
    """Format minutes as a compact text: ``1h 10m``, ``2h``, ``45m``, ``0m``."""
    total = int(total_minutes or 0)
    hours, minutes = divmod(total, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def hm_to_minutes(hours_str: str, minutes_str: str) -> int:
    """Convert two free-text fields (hours, minutes) to total minutes."""
    try:
        hours = int(hours_str) if hours_str and hours_str.strip() else 0
    except ValueError:
        hours = 0
    try:
        minutes = int(minutes_str) if minutes_str and minutes_str.strip() else 0
    except ValueError:
        minutes = 0
    return hours * 60 + minutes


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return False
    return True


def now_iso() -> str:
    return datetime.now().isoformat()
