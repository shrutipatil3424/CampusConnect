"""Event queries and admin CRUD."""
from datetime import datetime

import pandas as pd

from database.db_connection import execute, fetch_all, fetch_one
from utils.validators import join_list

_BASE_SELECT = """
SELECT e.*,
       (SELECT COUNT(*) FROM registrations r
         WHERE r.event_id = e.id AND r.status IN ('Registered', 'Attended')) AS registered_count
FROM events e
"""


def normalize_event(row: dict) -> dict:
    row = dict(row)
    row["fee"] = float(row.get("fee") or 0)
    row["capacity"] = int(row.get("capacity") or 0)
    row["registered_count"] = int(row.get("registered_count") or 0)
    row["seats_left"] = max(0, row["capacity"] - row["registered_count"])
    return row


def list_events(search=None, category=None, mode=None, free_only=False, upcoming_only=True,
                include_inactive=False, date_from=None, date_to=None, ids=None) -> list:
    where, params = ["1=1"], []
    if not include_inactive:
        where.append("e.is_active = 1")
    if upcoming_only:
        where.append("e.event_date >= %s")
        params.append(datetime.now())
    if search and search.strip():
        like = f"%{search.strip()}%"
        where.append("(e.title LIKE %s OR e.description LIKE %s OR e.tags LIKE %s OR e.organizer LIKE %s)")
        params += [like, like, like, like]
    if category and category != "All":
        where.append("e.category = %s")
        params.append(category)
    if mode and mode != "All":
        where.append("e.mode = %s")
        params.append(mode)
    if free_only:
        where.append("e.fee = 0")
    if date_from:
        where.append("e.event_date >= %s")
        params.append(datetime.combine(date_from, datetime.min.time()))
    if date_to:
        where.append("e.event_date <= %s")
        params.append(datetime.combine(date_to, datetime.max.time().replace(microsecond=0)))
    if ids is not None:
        ids = list(ids)
        if not ids:
            return []
        where.append("e.id IN (" + ",".join(["%s"] * len(ids)) + ")")
        params += ids
    rows = fetch_all(_BASE_SELECT + " WHERE " + " AND ".join(where) + " ORDER BY e.event_date ASC", params)
    return [normalize_event(r) for r in rows]


def get_event(event_id: int):
    row = fetch_one(_BASE_SELECT + " WHERE e.id = %s", (event_id,))
    return normalize_event(row) if row else None


def get_events_df(open_for_registration: bool = True) -> pd.DataFrame:
    """Upcoming active events as a DataFrame (input for the recommender)."""
    events = list_events(upcoming_only=True)
    if open_for_registration:
        now = datetime.now()
        events = [e for e in events if e["registration_deadline"] >= now and e["seats_left"] > 0]
    return pd.DataFrame(events)


def _params(data: dict) -> tuple:
    return (
        data["title"].strip(), data["description"].strip(), data["category"], data["organizer"].strip(),
        data["venue"].strip(), data["mode"], data["difficulty"], data["event_date"],
        data["registration_deadline"], int(data["capacity"]), float(data["fee"]),
        join_list(data.get("tags", [])), join_list(data.get("target_courses", [])) or "All",
    )


def create_event(data: dict, created_by: int) -> int:
    event_id, _ = execute(
        """INSERT INTO events (title, description, category, organizer, venue, mode, difficulty,
           event_date, registration_deadline, capacity, fee, tags, target_courses, created_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        _params(data) + (created_by,),
    )
    return event_id


def update_event(event_id: int, data: dict) -> None:
    execute(
        """UPDATE events SET title=%s, description=%s, category=%s, organizer=%s, venue=%s, mode=%s,
           difficulty=%s, event_date=%s, registration_deadline=%s, capacity=%s, fee=%s, tags=%s,
           target_courses=%s, ai_summary=NULL WHERE id=%s""",
        _params(data) + (event_id,),
    )


def delete_event(event_id: int) -> None:
    execute("DELETE FROM events WHERE id = %s", (event_id,))


def set_event_active(event_id: int, active: bool) -> None:
    execute("UPDATE events SET is_active=%s WHERE id=%s", (1 if active else 0, event_id))


def save_ai_summary(event_id: int, summary: str) -> None:
    execute("UPDATE events SET ai_summary=%s WHERE id=%s", (summary, event_id))


def get_admin_stats() -> dict:
    totals = fetch_one(
        """SELECT (SELECT COUNT(*) FROM students WHERE role='student') AS students,
                  (SELECT COUNT(*) FROM events) AS events,
                  (SELECT COUNT(*) FROM events WHERE event_date >= NOW() AND is_active=1) AS upcoming,
                  (SELECT COUNT(*) FROM registrations WHERE status <> 'Cancelled') AS registrations"""
    )
    by_category = fetch_all(
        """SELECT e.category, COUNT(DISTINCT e.id) AS events,
                  COUNT(r.id) AS registrations
           FROM events e LEFT JOIN registrations r
             ON r.event_id = e.id AND r.status <> 'Cancelled'
           GROUP BY e.category ORDER BY registrations DESC"""
    )
    top_events = fetch_all(
        """SELECT e.title, COUNT(r.id) AS registrations
           FROM events e LEFT JOIN registrations r
             ON r.event_id = e.id AND r.status <> 'Cancelled'
           GROUP BY e.id, e.title ORDER BY registrations DESC, e.title LIMIT 8"""
    )
    return {"totals": totals, "by_category": by_category, "top_events": top_events}
