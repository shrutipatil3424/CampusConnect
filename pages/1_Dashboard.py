"""Dashboard: stats, top recommendations and upcoming registered events."""
from datetime import datetime

import pandas as pd
import streamlit as st

from services import event_service, registration_service
from utils.ui_helpers import event_card, fmt_dt, hero, load_recommendations, setup_page
from utils.validators import split_list

user = setup_page("Dashboard", icon="📊")
hero("Dashboard", f"Hi {user['full_name'].split()[0]}, here is what is happening for you.")

registrations = [r for r in registration_service.list_student_registrations(user["id"])
                 if r["status"] != "Cancelled"]
upcoming_regs = [r for r in registrations if r["event_date"] >= datetime.now()]
registered_ids = registration_service.get_registered_ids(user["id"])
saved_ids = registration_service.get_saved_ids(user["id"])
all_upcoming = event_service.list_events()

profile_fields = [user["technical_interests"], user["skills"], user["preferred_categories"],
                  user["career_interests"]]
completeness = int(100 * sum(1 for f in profile_fields if split_list(f)) / len(profile_fields))

m1, m2, m3, m4 = st.columns(4)
m1.metric("Upcoming events", len(all_upcoming))
m2.metric("My registrations", len(upcoming_regs))
m3.metric("Saved events", len(saved_ids))
m4.metric("Profile completeness", f"{completeness}%")

st.subheader("🎯 Top picks for you")
recs = load_recommendations(user, top_n=3)
if not recs:
    st.info("No open events to recommend right now. Check back soon!")
for event, score, reasons in recs:
    event_card(event, user, "dash", registered_ids, saved_ids, score=score, reasons=reasons)
st.page_link("pages/2_Discover_Events.py", label="See all recommendations", icon="🔍")

left, right = st.columns(2, gap="large")
with left:
    st.subheader("🗓️ My next events")
    if not upcoming_regs:
        st.info("You have not registered for any upcoming event yet.")
    for r in upcoming_regs[:5]:
        with st.container(border=True):
            st.markdown(f"**{r['title']}**")
            st.caption(f"{fmt_dt(r['event_date'])} · {r['mode']} · {r['venue']}")
with right:
    st.subheader("📈 Upcoming events by category")
    if all_upcoming:
        counts = pd.Series([e["category"] for e in all_upcoming]).value_counts()
        st.bar_chart(counts, color="#4f46e5")
    else:
        st.info("No upcoming events yet.")
