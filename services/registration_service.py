"""Event registrations and saved (bookmarked) events."""
from datetime import datetime

from database.db_connection import execute, fetch_all, fetch_one
from services import event_service


# --------------------------------------------------------------- registrations
def register_for_event(student_id: int, event_id: int) -> tuple:
    event = event_service.get_event(event_id)
    if not event or not event["is_active"]:
        return False, "This event is no longer available."
    now = datetime.now()
    if event["event_date"] < now:
        return False, "This event has already taken place."
    if event["registration_deadline"] < now:
        return False, "Registration for this event is closed."
    existing = fetch_one(
        "SELECT id, status FROM registrations WHERE student_id=%s AND event_id=%s", (student_id, event_id)
    )
    if existing and existing["status"] in ("Registered", "Attended"):
        return False, "You are already registered for this event."
    if event["seats_left"] <= 0:
        return False, "Sorry, this event is full."
    if existing:
        execute(
            "UPDATE registrations SET status='Registered', registered_at=NOW() WHERE id=%s", (existing["id"],)
        )
    else:
        execute("INSERT INTO registrations (student_id, event_id) VALUES (%s, %s)", (student_id, event_id))
    return True, f"Registered for “{event['title']}”."


def cancel_registration(student_id: int, event_id: int) -> tuple:
    _, affected = execute(
        "UPDATE registrations SET status='Cancelled' WHERE student_id=%s AND event_id=%s AND status='Registered'",
        (student_id, event_id),
    )
    if affected:
        return True, "Registration cancelled."
    return False, "No active registration found to cancel."


def get_registered_ids(student_id: int) -> set:
    rows = fetch_all(
        "SELECT event_id FROM registrations WHERE student_id=%s AND status IN ('Registered','Attended')",
        (student_id,),
    )
    return {r["event_id"] for r in rows}


def list_student_registrations(student_id: int) -> list:
    rows = fetch_all(
        """SELECT r.id AS registration_id, r.status, r.registered_at, e.id AS event_id, e.title,
                  e.category, e.organizer, e.venue, e.mode, e.event_date, e.fee, e.registration_deadline
           FROM registrations r JOIN events e ON e.id = r.event_id
           WHERE r.student_id = %s ORDER BY e.event_date ASC""",
        (student_id,),
    )
    for r in rows:
        r["fee"] = float(r["fee"] or 0)
    return rows


# ---------------------------------------------------------------- saved events
def save_event(student_id: int, event_id: int) -> tuple:
    execute("INSERT IGNORE INTO saved_events (student_id, event_id) VALUES (%s, %s)", (student_id, event_id))
    return True, "Event saved."


def unsave_event(student_id: int, event_id: int) -> tuple:
    execute("DELETE FROM saved_events WHERE student_id=%s AND event_id=%s", (student_id, event_id))
    return True, "Removed from saved events."


def get_saved_ids(student_id: int) -> set:
    rows = fetch_all("SELECT event_id FROM saved_events WHERE student_id=%s", (student_id,))
    return {r["event_id"] for r in rows}


def list_saved_events(student_id: int) -> list:
    return event_service.list_events(ids=get_saved_ids(student_id), upcoming_only=False)


# ----------------------------------------------------------------------- admin
def list_event_registrations(event_id: int) -> list:
    return fetch_all(
        """SELECT r.id AS registration_id, s.full_name, s.email, s.college_name, s.course,
                  s.academic_year, r.status, r.registered_at
           FROM registrations r JOIN students s ON s.id = r.student_id
           WHERE r.event_id = %s ORDER BY r.registered_at""",
        (event_id,),
    )


def update_registration_status(registration_id: int, status: str) -> None:
    execute("UPDATE registrations SET status=%s WHERE id=%s", (status, registration_id))
