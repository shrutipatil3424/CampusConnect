"""Saved (bookmarked) events."""
import streamlit as st

from services import registration_service
from utils.ui_helpers import event_card, hero, setup_page

user = setup_page("Saved Events", icon="⭐")
hero("Saved Events", "Events you bookmarked to decide on later.")

saved_events = registration_service.list_saved_events(user["id"])
registered_ids = registration_service.get_registered_ids(user["id"])
saved_ids = {e["id"] for e in saved_events}

if not saved_events:
    st.info("You have not saved any events yet. Use the ☆ Save button on any event.")
    st.page_link("pages/2_Discover_Events.py", label="Discover events", icon="🔍")
else:
    st.caption(f"{len(saved_events)} saved event(s)")
    for event in saved_events:
        event_card(event, user, "saved", registered_ids, saved_ids)
