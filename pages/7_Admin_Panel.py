"""Admin panel: analytics, event management, registrations and students."""
from datetime import datetime, time, timedelta

import pandas as pd
import streamlit as st

from services import event_service, registration_service, student_service
from utils.constants import (
    COURSES, DIFFICULTY_LEVELS, EVENT_CATEGORIES, EVENT_MODES, REGISTRATION_STATUSES,
)
from utils.ui_helpers import flash, fmt_dt, hero, setup_page
from utils.validators import parse_list, split_list, validate_event

user = setup_page("Admin Panel", icon="🛠️", require_admin=True)
hero("Admin Panel", "Manage events, registrations and students.")

tab_overview, tab_events, tab_regs, tab_students = st.tabs(
    ["📊 Overview", "🗂️ Manage events", "🎟️ Registrations", "👥 Students"])


def event_form(prefix: str, event=None) -> dict:
    """Render the event fields; returns the submitted dict values (call inside st.form)."""
    e = event or {}
    default_dt = (datetime.now() + timedelta(days=14)).replace(minute=0, second=0, microsecond=0)
    event_dt = e.get("event_date", default_dt)
    deadline_dt = e.get("registration_deadline", event_dt - timedelta(days=2))
    title = st.text_input("Title", value=e.get("title", ""), key=f"{prefix}_title")
    description = st.text_area("Description", value=e.get("description", ""), height=120, key=f"{prefix}_desc")
    c1, c2, c3 = st.columns(3)
    category = c1.selectbox("Category", EVENT_CATEGORIES, key=f"{prefix}_cat",
                            index=EVENT_CATEGORIES.index(e["category"]) if e.get("category") in EVENT_CATEGORIES else 0)
    mode = c2.selectbox("Mode", EVENT_MODES, key=f"{prefix}_mode",
                        index=EVENT_MODES.index(e["mode"]) if e.get("mode") in EVENT_MODES else 0)
    difficulty = c3.selectbox("Difficulty", DIFFICULTY_LEVELS, key=f"{prefix}_diff",
                              index=DIFFICULTY_LEVELS.index(e["difficulty"]) if e.get("difficulty") in DIFFICULTY_LEVELS else 0)
    o1, o2 = st.columns(2)
    organizer = o1.text_input("Organizer", value=e.get("organizer", ""), key=f"{prefix}_org")
    venue = o2.text_input("Venue / meeting link", value=e.get("venue", ""), key=f"{prefix}_venue")
    d1, d2, d3, d4 = st.columns(4)
    event_date = d1.date_input("Event date", value=event_dt.date(), key=f"{prefix}_date")
    event_time = d2.time_input("Event time", value=event_dt.time(), key=f"{prefix}_time")
    deadline_date = d3.date_input("Registration deadline", value=deadline_dt.date(), key=f"{prefix}_ddate")
    deadline_time = d4.time_input("Deadline time", value=deadline_dt.time(), key=f"{prefix}_dtime")
    n1, n2 = st.columns(2)
    capacity = n1.number_input("Capacity", min_value=1, max_value=100000, value=int(e.get("capacity", 100)),
                               key=f"{prefix}_cap")
    fee = n2.number_input("Fee (₹)", min_value=0.0, value=float(e.get("fee", 0.0)), step=50.0, key=f"{prefix}_fee")
    tags = st.text_input("Tags (comma-separated)", value=", ".join(split_list(e.get("tags"))), key=f"{prefix}_tags",
                         help="Topic keywords drive the recommendation engine, e.g. python, machine learning")
    existing_targets = [c for c in split_list(e.get("target_courses")) if c in COURSES + ["All"]]
    targets = st.multiselect("Target courses", ["All"] + COURSES, default=existing_targets or ["All"],
                             key=f"{prefix}_targets")
    return {
        "title": title, "description": description, "category": category, "mode": mode, "difficulty": difficulty,
        "organizer": organizer, "venue": venue,
        "event_date": datetime.combine(event_date, event_time),
        "registration_deadline": datetime.combine(deadline_date, deadline_time),
        "capacity": capacity, "fee": fee, "tags": parse_list(tags), "target_courses": targets or ["All"],
    }


# ------------------------------------------------------------------- overview
with tab_overview:
    stats = event_service.get_admin_stats()
    t = stats["totals"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Students", t["students"])
    m2.metric("Events", t["events"])
    m3.metric("Upcoming events", t["upcoming"])
    m4.metric("Active registrations", t["registrations"])
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("**Registrations by category**")
        if stats["by_category"]:
            df = pd.DataFrame(stats["by_category"]).set_index("category")[["registrations"]]
            st.bar_chart(df, color="#4f46e5")
    with c2:
        st.markdown("**Most popular events**")
        if stats["top_events"]:
            df = pd.DataFrame(stats["top_events"]).set_index("title")[["registrations"]]
            st.bar_chart(df, color="#0ea5e9", horizontal=True)

# --------------------------------------------------------------- manage events
with tab_events:
    with st.expander("➕ Create a new event", expanded=False):
        with st.form("create_event_form"):
            new_data = event_form("new")
            create = st.form_submit_button("Create event", type="primary", width="stretch")
        if create:
            errors = validate_event(new_data)
            if errors:
                for err in errors:
                    st.error(err)
            else:
                event_service.create_event(new_data, user["id"])
                flash("success", f"Event “{new_data['title']}” created.")
                st.rerun()

    st.markdown("#### Edit or remove an event")
    all_events = event_service.list_events(upcoming_only=False, include_inactive=True)
    if not all_events:
        st.info("No events yet. Create the first one above.")
    else:
        labels = {e["id"]: f"{e['title']} — {fmt_dt(e['event_date'])}" + ("" if e["is_active"] else " (hidden)")
                  for e in all_events}
        selected_id = st.selectbox("Select event", list(labels), format_func=labels.get, key="admin_select_event")
        selected = next(e for e in all_events if e["id"] == selected_id)
        with st.form(f"edit_event_form_{selected_id}"):
            edit_data = event_form(f"edit{selected_id}", selected)
            save = st.form_submit_button("Save changes", type="primary", width="stretch")
        if save:
            errors = validate_event(edit_data)
            if errors:
                for err in errors:
                    st.error(err)
            elif edit_data["capacity"] < selected["registered_count"]:
                st.error(f"Capacity cannot be lower than the {selected['registered_count']} current registrations.")
            else:
                event_service.update_event(selected_id, edit_data)
                flash("success", "Event updated.")
                st.rerun()

        a1, a2 = st.columns(2)
        visible = bool(selected["is_active"])
        if a1.button("Hide from students" if visible else "Show to students", width="stretch"):
            event_service.set_event_active(selected_id, not visible)
            flash("success", "Visibility updated.")
            st.rerun()
        confirm = a2.checkbox("I understand this permanently deletes the event and its registrations",
                              key=f"confirm_delete_{selected_id}")
        if a2.button("🗑️ Delete event", disabled=not confirm, width="stretch"):
            event_service.delete_event(selected_id)
            flash("success", "Event deleted.")
            st.rerun()

# ---------------------------------------------------------------- registrations
with tab_regs:
    events_for_regs = event_service.list_events(upcoming_only=False, include_inactive=True)
    if not events_for_regs:
        st.info("No events available.")
    else:
        labels = {e["id"]: f"{e['title']} — {fmt_dt(e['event_date'])}" for e in events_for_regs}
        reg_event_id = st.selectbox("Event", list(labels), format_func=labels.get, key="admin_reg_event")
        regs = registration_service.list_event_registrations(reg_event_id)
        if not regs:
            st.info("Nobody has registered for this event yet.")
        else:
            df = pd.DataFrame(regs)
            df["registered_at"] = df["registered_at"].apply(fmt_dt)
            edited = st.data_editor(
                df, hide_index=True, width="stretch", key=f"reg_editor_{reg_event_id}",
                disabled=[c for c in df.columns if c != "status"],
                column_config={
                    "registration_id": None,
                    "status": st.column_config.SelectboxColumn("Status", options=REGISTRATION_STATUSES, required=True),
                    "full_name": "Name", "email": "Email", "college_name": "College", "course": "Course",
                    "academic_year": "Year", "registered_at": "Registered at",
                },
            )
            b1, b2 = st.columns(2)
            if b1.button("Save attendance / status changes", type="primary", width="stretch"):
                changed = 0
                for old, new in zip(df.to_dict("records"), edited.to_dict("records")):
                    if old["status"] != new["status"]:
                        registration_service.update_registration_status(old["registration_id"], new["status"])
                        changed += 1
                flash("success", f"{changed} registration(s) updated.")
                st.rerun()
            b2.download_button("⬇️ Export registrations (CSV)",
                               df.drop(columns=["registration_id"]).to_csv(index=False).encode("utf-8"),
                               file_name=f"registrations_event_{reg_event_id}.csv", mime="text/csv",
                               width="stretch")

# --------------------------------------------------------------------- students
with tab_students:
    students = student_service.list_students()
    if students:
        df = pd.DataFrame(students)
        df["created_at"] = df["created_at"].apply(fmt_dt)
        st.dataframe(df, hide_index=True, width="stretch", column_config={
            "id": "ID", "full_name": "Name", "email": "Email", "college_name": "College", "course": "Course",
            "academic_year": "Year", "role": "Role", "created_at": "Joined",
            "active_registrations": "Active registrations",
        })
        st.download_button("⬇️ Export students (CSV)", df.to_csv(index=False).encode("utf-8"),
                           file_name="students.csv", mime="text/csv")
