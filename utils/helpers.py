from datetime import datetime


def minutes_to_hm_text(total_minutes: int) -> str:
 
    if total_minutes is None:
        total_minutes = 0
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours and minutes:
        return f"{hours} hours and {minutes} minutes"
    elif hours:
        return f"{hours} hours"
    elif minutes:
        return f"{minutes} minutes"
    else:
        return "0 minutes"


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