"""Discover events: personalised recommendations and full catalogue with filters."""
import streamlit as st

from services import event_service, registration_service
from utils.constants import EVENT_CATEGORIES, EVENT_MODES
from utils.ui_helpers import event_card, hero, load_recommendations, setup_page

user = setup_page("Discover Events", icon="🔍")
hero("Discover Events", "Recommended for your interests, skills and course — or browse everything.")

registered_ids = registration_service.get_registered_ids(user["id"])
saved_ids = registration_service.get_saved_ids(user["id"])

tab_rec, tab_all = st.tabs(["🎯 Recommended for you", "📚 Browse all events"])

with tab_rec:
    c1, c2 = st.columns([3, 1])
    c1.caption("Ranked with TF-IDF + cosine similarity between your profile and each event, "
               "plus category and course fit.")
    count = c2.slider("How many", 3, 20, 8, key="rec_count")
    recs = load_recommendations(user, top_n=count)
    if not recs:
        st.info("No open events to recommend right now.")
    for event, score, reasons in recs:
        event_card(event, user, "rec", registered_ids, saved_ids, score=score, reasons=reasons)

with tab_all:
    f1, f2, f3 = st.columns([2, 1, 1])
    search = f1.text_input("Search", placeholder="e.g. python, hackathon, resume…", key="browse_search")
    category = f2.selectbox("Category", ["All"] + EVENT_CATEGORIES, key="browse_category")
    mode = f3.selectbox("Mode", ["All"] + EVENT_MODES, key="browse_mode")
    g1, g2, g3 = st.columns([1, 1, 1])
    free_only = g1.checkbox("Free events only", key="browse_free")
    date_from = g2.date_input("From date", value=None, key="browse_from")
    date_to = g3.date_input("To date", value=None, key="browse_to")

    events = event_service.list_events(
        search=search, category=category, mode=mode, free_only=free_only,
        date_from=date_from, date_to=date_to,
    )
    st.caption(f"{len(events)} event(s) found")
    if not events:
        st.info("No events match your filters.")
    for event in events:
        event_card(event, user, "all", registered_ids, saved_ids)
