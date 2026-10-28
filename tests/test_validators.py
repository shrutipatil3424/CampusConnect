from datetime import datetime, timedelta

from utils.validators import (
    is_valid_email, is_valid_name, join_list, merge_lists, parse_list,
    validate_event, validate_password, validate_registration,
)


def valid_registration():
    return {
        "full_name": "Asha Patil", "email": "asha@example.com",
        "password": "Strong@123", "confirm_password": "Strong@123",
        "college_name": "ABC Institute", "course": "MCA", "academic_year": "2nd Year",
        "technical_interests": ["Machine Learning"], "skills": ["Python"],
        "preferred_categories": ["Hackathon"], "career_interests": ["Data Scientist"],
    }


def test_email_validation():
    assert is_valid_email("a.b+c@college.edu.in")
    assert not is_valid_email("no-at-sign.com")
    assert not is_valid_email("a@b")
    assert not is_valid_email("")


def test_password_rules():
    assert validate_password("Strong@123") == []
    assert validate_password("short1A")
    assert validate_password("alllowercase1")
    assert validate_password("NoDigitsHere")


def test_name_validation():
    assert is_valid_name("Mary-Anne O'Neil")
    assert not is_valid_name("X")
    assert not is_valid_name("R2D2")


def test_list_helpers():
    assert parse_list("Python, python ,SQL;\nJava") == ["Python", "SQL", "Java"]
    assert merge_lists(["A", "b"], ["B", "c"]) == ["A", "b", "c"]
    assert join_list(["x", "X", "y"]) == "x, y"
    assert parse_list(None) == []


def test_valid_registration_has_no_errors():
    assert validate_registration(valid_registration()) == []


def test_registration_catches_problems():
    data = valid_registration()
    data.update(email="bad", confirm_password="other", course="MBA", skills=[])
    errors = validate_registration(data)
    assert len(errors) >= 4


def test_event_validation():
    now = datetime.now()
    event = {
        "title": "AI Workshop", "description": "A hands-on workshop about machine learning.",
        "category": "Workshop", "organizer": "CS Dept", "venue": "Lab 2", "mode": "Offline",
        "difficulty": "Beginner", "event_date": now + timedelta(days=10),
        "registration_deadline": now + timedelta(days=8), "capacity": 50, "fee": 0,
    }
    assert validate_event(event) == []
    event["registration_deadline"] = now + timedelta(days=11)
    assert validate_event(event)


def test_date_filter_before_and_ranges():
    from datetime import date, datetime
    from utils.date_filter import parse_date_range
    today = date(2026, 10, 14)
    start, end, label = parse_date_range("give me upcoming events before 30 October", today)
    assert start == datetime(2026, 10, 14) and end == datetime(2026, 10, 30)
    assert parse_date_range("events by Oct 30", today)[1] == datetime(2026, 10, 31)
    assert parse_date_range("events after 5 november", today)[0] == datetime(2026, 11, 5)
    assert parse_date_range("hackathons this week", today)[1] == datetime(2026, 10, 19)
    assert parse_date_range("any python workshops", today) == (None, None, "")
