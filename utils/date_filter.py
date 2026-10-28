"""Understand simple date limits in a question, e.g. "events before 30 October" or "this week"."""
import re
from datetime import date, datetime, timedelta

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4, "apr": 4,
    "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9, "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}
_MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))
_DAY_MONTH = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s*(?:of\s+)?({_MONTH_RE})\b(?:\s*,?\s*(\d{{4}}))?")
_MONTH_DAY = re.compile(rf"\b({_MONTH_RE})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b(?:\s*,?\s*(\d{{4}}))?")
_BEFORE = re.compile(r"\b(before|by|until|till|upto|up to|prior to)\b")
_AFTER = re.compile(r"\b(after|from|since)\b")


def _find_date(text: str, today: date):
    for regex, day_first in ((_DAY_MONTH, True), (_MONTH_DAY, False)):
        m = regex.search(text)
        if not m:
            continue
        day, month = (int(m.group(1)), MONTHS[m.group(2)]) if day_first else (int(m.group(2)), MONTHS[m.group(1)])
        year = int(m.group(3)) if m.group(3) else today.year
        try:
            found = date(year, month, day)
        except ValueError:
            continue
        if not m.group(3) and found < today - timedelta(days=30):
            found = date(year + 1, month, day)
        return found, m.start()
    return None, -1


def parse_date_range(question: str, today=None):
    """Return (start_datetime_or_None, end_datetime_or_None, label). Both None if no date limit found.

    "before 30 October" excludes 30 October itself; "by 30 October" and "until 30 October" include it.
    """
    today = today or date.today()
    text = (question or "").lower()
    start_of_today = datetime.combine(today, datetime.min.time())

    if "today" in text:
        return start_of_today, start_of_today + timedelta(days=1), "today"
    if "tomorrow" in text:
        return start_of_today + timedelta(days=1), start_of_today + timedelta(days=2), "tomorrow"
    if "next week" in text:
        monday = today + timedelta(days=7 - today.weekday())
        return (datetime.combine(monday, datetime.min.time()),
                datetime.combine(monday + timedelta(days=7), datetime.min.time()), "next week")
    if "this week" in text or "this weekend" in text:
        return start_of_today, datetime.combine(today + timedelta(days=7 - today.weekday()),
                                                datetime.min.time()), "this week"
    if "this month" in text:
        nxt = date(today.year + (today.month == 12), today.month % 12 + 1, 1)
        return start_of_today, datetime.combine(nxt, datetime.min.time()), "this month"

    found, pos = _find_date(text, today)
    if not found:
        return None, None, ""
    before = text[:pos]
    day_start = datetime.combine(found, datetime.min.time())
    if _BEFORE.search(before[-20:]):
        inclusive = re.search(r"\b(by|until|till|upto|up to)\b", before[-20:]) is not None
        end = day_start + timedelta(days=1 if inclusive else 0)
        return start_of_today, end, f"before {found.strftime('%d %b %Y')}" if not inclusive else \
            f"up to {found.strftime('%d %b %Y')}"
    if _AFTER.search(before[-20:]):
        return day_start, None, f"after {found.strftime('%d %b %Y')}"
    return day_start, day_start + timedelta(days=1), f"on {found.strftime('%d %b %Y')}"
