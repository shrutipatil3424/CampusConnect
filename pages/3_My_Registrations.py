"""My registrations: upcoming, past and cancelled."""
from datetime import datetime

import pandas as pd
import streamlit as st

from services import registration_service
from utils.ui_helpers import fee_label, flash, fmt_dt, hero, setup_page

user = setup_page("My Registrations", icon="🎟️")
hero("My Registrations", "Track every event you have signed up for.")

rows = registration_service.list_student_registrations(user["id"])
now = datetime.now()
upcoming = [r for r in rows if r["status"] == "Registered" and r["event_date"] >= now]
past = [r for r in rows if r["status"] in ("Registered", "Attended") and r["event_date"] < now]
cancelled = [r for r in rows if r["status"] == "Cancelled"]

m1, m2, m3 = st.columns(3)
m1.metric("Upcoming", len(upcoming))
m2.metric("Attended / past", len(past))
m3.metric("Cancelled", len(cancelled))

tab_up, tab_past, tab_cancel = st.tabs(["Upcoming", "Past", "Cancelled"])

with tab_up:
    if not upcoming:
        st.info("No upcoming registrations. Head to **Discover Events** to find something great.")
        st.page_link("pages/2_Discover_Events.py", label="Discover events", icon="🔍")
    for r in upcoming:
        with st.container(border=True):
            a, b = st.columns([4, 1])
            a.markdown(f"**{r['title']}**")
            a.caption(f"{r['category']} · {fmt_dt(r['event_date'])} · {r['mode']} · {r['venue']} · "
                      f"{fee_label(r['fee'])}")
            a.caption(f"Registered on {fmt_dt(r['registered_at'])}")
            if b.button("Cancel", key=f"cancel_{r['registration_id']}", width="stretch"):
                ok, msg = registration_service.cancel_registration(user["id"], r["event_id"])
                flash("success" if ok else "error", msg)
                st.rerun()

with tab_past:
    if not past:
        st.info("No past events yet.")
    for r in past:
        with st.container(border=True):
            st.markdown(f"**{r['title']}** — {r['status']}")
            st.caption(f"{r['category']} · {fmt_dt(r['event_date'])} · {r['venue']}")

with tab_cancel:
    if not cancelled:
        st.info("No cancelled registrations.")
    for r in cancelled:
        with st.container(border=True):
            c, d = st.columns([4, 1])
            c.markdown(f"**{r['title']}**")
            c.caption(f"{fmt_dt(r['event_date'])} · {r['venue']}")
            if r["event_date"] >= now and r["registration_deadline"] >= now:
                if d.button("Re-register", key=f"rereg_{r['registration_id']}", width="stretch"):
                    ok, msg = registration_service.register_for_event(user["id"], r["event_id"])
                    flash("success" if ok else "error", msg)
                    st.rerun()

if rows:
    export = pd.DataFrame([{
        "Event": r["title"], "Category": r["category"], "Date": fmt_dt(r["event_date"]), "Mode": r["mode"],
        "Venue": r["venue"], "Fee": fee_label(r["fee"]), "Status": r["status"],
    } for r in rows])
    st.download_button("⬇️ Download my registrations (CSV)", export.to_csv(index=False).encode("utf-8"),
                       file_name="my_registrations.csv", mime="text/csv")
