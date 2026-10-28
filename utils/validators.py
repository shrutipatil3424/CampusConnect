"""Input validation and list-parsing helpers (pure Python, no Streamlit/DB)."""
import re
from datetime import datetime

from utils.constants import (
    ACADEMIC_YEARS, COURSES, DIFFICULTY_LEVELS, EVENT_CATEGORIES, EVENT_MODES,
)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


# ---------------------------------------------------------------- list helpers
def parse_list(text) -> list:
    """Split a comma/newline separated string into a de-duplicated list."""
    if not text:
        return []
    items = re.split(r"[,\n;]+", str(text))
    return merge_lists(items)


def merge_lists(*lists) -> list:
    """Merge lists, trimming blanks and removing case-insensitive duplicates."""
    seen, out = set(), []
    for items in lists:
        for item in items or []:
            clean = str(item).strip()
            if clean and clean.lower() not in seen:
                seen.add(clean.lower())
                out.append(clean)
    return out


def join_list(items) -> str:
    return ", ".join(merge_lists(items))


def split_list(text) -> list:
    return parse_list(text)


# ------------------------------------------------------------------ field checks
def is_valid_email(email: str) -> bool:
    return bool(email) and len(email) <= 150 and bool(EMAIL_RE.match(email.strip()))


def validate_password(password: str) -> list:
    errors = []
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
        return errors
    if len(password) > 72:
        errors.append("Password must be at most 72 characters long.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain a lowercase letter.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain an uppercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain a digit.")
    return errors


def is_valid_name(name: str) -> bool:
    name = (name or "").strip()
    if len(name) < 2 or len(name) > 100 or not name[0].isalpha():
        return False
    return all(ch.isalpha() or ch in " .'-" for ch in name)


def validate_profile_fields(data: dict) -> list:
    """Validate the non-credential student fields."""
    errors = []
    if not is_valid_name(data.get("full_name", "")):
        errors.append("Enter a valid full name (letters, spaces, . ' - only; 2-100 characters).")
    college = (data.get("college_name") or "").strip()
    if len(college) < 3 or len(college) > 150:
        errors.append("College name must be between 3 and 150 characters.")
    if data.get("course") not in COURSES:
        errors.append("Select a valid course.")
    if data.get("academic_year") not in ACADEMIC_YEARS:
        errors.append("Select a valid academic year.")
    if not merge_lists(data.get("technical_interests")):
        errors.append("Select or enter at least one interest (technical or non-technical).")
    if not merge_lists(data.get("skills")):
        errors.append("Select or enter at least one current skill.")
    categories = merge_lists(data.get("preferred_categories"))
    if not categories:
        errors.append("Select at least one preferred event category.")
    elif any(c not in EVENT_CATEGORIES for c in categories):
        errors.append("One or more preferred event categories are invalid.")
    if not merge_lists(data.get("career_interests")):
        errors.append("Select or enter at least one career interest.")
    return errors


def validate_registration(data: dict) -> list:
    errors = []
    if not is_valid_email(data.get("email", "")):
        errors.append("Enter a valid email address.")
    errors.extend(validate_password(data.get("password", "")))
    if data.get("password") != data.get("confirm_password"):
        errors.append("Password and confirm password do not match.")
    errors.extend(validate_profile_fields(data))
    return errors


def validate_event(data: dict) -> list:
    errors = []
    title = (data.get("title") or "").strip()
    if len(title) < 3 or len(title) > 200:
        errors.append("Title must be between 3 and 200 characters.")
    if len((data.get("description") or "").strip()) < 20:
        errors.append("Description must be at least 20 characters.")
    if data.get("category") not in EVENT_CATEGORIES:
        errors.append("Select a valid category.")
    if not (data.get("organizer") or "").strip():
        errors.append("Organizer is required.")
    if not (data.get("venue") or "").strip():
        errors.append("Venue (or meeting link) is required.")
    if data.get("mode") not in EVENT_MODES:
        errors.append("Select a valid mode.")
    if data.get("difficulty") not in DIFFICULTY_LEVELS:
        errors.append("Select a valid difficulty level.")
    event_date, deadline = data.get("event_date"), data.get("registration_deadline")
    if not isinstance(event_date, datetime) or not isinstance(deadline, datetime):
        errors.append("Event date and registration deadline are required.")
    elif deadline > event_date:
        errors.append("Registration deadline must be on or before the event date.")
    try:
        if int(data.get("capacity", 0)) < 1:
            errors.append("Capacity must be at least 1.")
    except (TypeError, ValueError):
        errors.append("Capacity must be a whole number.")
    try:
        if float(data.get("fee", 0)) < 0:
            errors.append("Fee cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Fee must be a number.")
    return errors
