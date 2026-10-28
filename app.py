"""CampusConnect AI — entry point: login, registration and home screen."""
import streamlit as st

from services import auth_service, event_service
from utils.constants import (
    CATEGORY_ICONS,
    ACADEMIC_YEARS, APP_NAME, APP_TAGLINE, CAREER_INTERESTS, COURSES, EVENT_CATEGORIES, INTERESTS, SKILLS,
)
from utils.ui_helpers import hero, multiselect_with_extra, setup_page

user = setup_page("Home", icon="🎓", require_login=False)


def login_tab() -> None:
    st.subheader("Welcome back")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@college.edu")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary", width="stretch")
    if submitted:
        found, message = auth_service.login(email, password)
        if found:
            st.session_state["user"] = found
            st.rerun()
        else:
            st.error(message)
    st.caption("Demo student: demo@campusconnect.ai / Demo@1234")


def register_tab() -> None:
    st.subheader("Create your student account")
    with st.form("register_form"):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Full name")
        email = c2.text_input("Email")
        p1, p2 = st.columns(2)
        password = p1.text_input("Password", type="password",
                                 help="At least 8 characters with uppercase, lowercase and a digit.")
        confirm = p2.text_input("Confirm password", type="password")
        college = st.text_input("College name")
        d1, d2 = st.columns(2)
        course = d1.selectbox("Course", COURSES)
        year = d2.selectbox("Academic year", ACADEMIC_YEARS)
        interests = multiselect_with_extra("Interests (technical and non-technical)", INTERESTS, "reg_interests",
                                         help_text="Pick anything you enjoy: coding, public speaking, photography, leadership…")
        skills = multiselect_with_extra("Current skills", SKILLS, "reg_skills")
        categories = st.multiselect("Preferred event categories", EVENT_CATEGORIES, key="reg_categories")
        careers = multiselect_with_extra("Career interests", CAREER_INTERESTS, "reg_careers")
        submitted = st.form_submit_button("Create account", type="primary", width="stretch")
    if submitted:
        ok, messages = auth_service.register_student({
            "full_name": full_name, "email": email, "password": password, "confirm_password": confirm,
            "college_name": college, "course": course, "academic_year": year,
            "technical_interests": interests, "skills": skills, "preferred_categories": categories,
            "career_interests": careers,
        })
        if ok:
            st.success(messages[0] + " Open the **Log in** tab to continue.")
        else:
            for message in messages:
                st.error(message)


def show_upcoming_panel() -> None:
    """Public left panel: live numbers and the next few upcoming events (no login needed)."""
    try:
        events = event_service.list_events()
    except Exception:
        events = []
    categories = {e["category"] for e in events}
    free = sum(1 for e in events if not e["fee"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Upcoming events", len(events))
    m2.metric("Free events", free)
    m3.metric("Categories", len(categories))

    st.markdown("### 🔥 Coming up soon")
    if not events:
        st.info("No upcoming events yet. Check back soon!")
        return
    for e in events[:4]:
        with st.container(border=True):
            st.markdown(f"**{CATEGORY_ICONS.get(e['category'], '🎯')} {e['title']}**")
            st.caption(f"📅 {e['event_date'].strftime('%d %b, %I:%M %p')} · {e['mode']} · "
                       f"{'Free' if not e['fee'] else '₹' + format(e['fee'], ',.0f')}")
    st.caption("Log in or register to get events matched to your interests and skills.")


if user is None:
    hero(f"🎓 {APP_NAME}", f"{APP_TAGLINE} — find workshops, hackathons and career events that fit you.")
    left, right = st.columns([1, 1.4], gap="large")
    with left:
        show_upcoming_panel()
    with right:
        tab_login, tab_register = st.tabs(["Log in", "Register"])
        with tab_login:
            login_tab()
        with tab_register:
            register_tab()
else:
    hero(f"Welcome, {user['full_name'].split()[0]}! 👋", f"{user['course']} · {user['college_name']}")
    st.markdown("### Where would you like to go?")
    links = [
        ("pages/1_Dashboard.py", "Dashboard", "📊"),
        ("pages/2_Discover_Events.py", "Discover Events", "🔍"),
        ("pages/3_My_Registrations.py", "My Registrations", "🎟️"),
        ("pages/4_Saved_Events.py", "Saved Events", "⭐"),
        ("pages/5_My_Profile.py", "My Profile", "👤"),
        ("pages/6_AI_Event_Assistant.py", "AI Event Assistant", "🤖"),
    ]
    if user["role"] == "admin":
        links.append(("pages/7_Admin_Panel.py", "Admin Panel", "🛠️"))
    cols = st.columns(3)
    for i, (path, label, icon) in enumerate(links):
        with cols[i % 3]:
            with st.container(border=True):
                st.page_link(path, label=label, icon=icon, width="stretch")
