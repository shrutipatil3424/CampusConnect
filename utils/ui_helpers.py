"""Shared Streamlit UI helpers: page setup, styling, sidebar, event cards."""
import html
from datetime import datetime
from pathlib import Path

import streamlit as st

from database.db_connection import init_db
from database.seed_data import seed_if_empty, seed_non_technical_events
from services import (
    event_service, gemini_service, recommendation_service, registration_service, student_service,
)
from utils.constants import APP_NAME, APP_TAGLINE, CATEGORY_ICONS
from utils.validators import merge_lists, parse_list, split_list

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
.cc-hero {background: linear-gradient(120deg,#4f46e5 0%,#7c3aed 55%,#0ea5e9 100%); color: #fff;
          padding: 1.5rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;}
.cc-hero h1 {color: #fff; margin: 0; font-size: 2rem; padding: 0;}
.cc-hero p {margin: .35rem 0 0 0; opacity: .93; font-size: 1.02rem;}
.cc-badge {display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .75rem;
           font-weight: 600; margin: 0 6px 6px 0; background: #eef2ff; color: #4338ca;}
.cc-badge.green {background: #dcfce7; color: #166534;}
.cc-badge.amber {background: #fef3c7; color: #92400e;}
.cc-badge.blue {background: #e0f2fe; color: #075985;}
.cc-badge.red {background: #fee2e2; color: #991b1b;}
.cc-meta {color: #6b7280; font-size: .9rem; margin-bottom: .3rem;}
.cc-match {font-weight: 700; color: #4f46e5; text-align: right; font-size: 1.05rem;}
@media (max-width: 768px) {
  .block-container {padding: 1rem .8rem;}
  .cc-hero {padding: 1.1rem 1.1rem;} .cc-hero h1 {font-size: 1.4rem;}
}
</style>
"""


# ------------------------------------------------------------------ page setup
@st.cache_resource(show_spinner="Preparing database…")
def _prepare_database() -> bool:
    init_db()
    seed_if_empty()
    seed_non_technical_events()  # adds the non-technical sample events to older databases
    return True


def ensure_database() -> None:
    try:
        _prepare_database()
    except Exception as exc:
        st.error(
            "Could not connect to MySQL. Make sure MySQL is running and the DB_* values in your `.env` "
            "file are correct."
        )
        st.code(f"{type(exc).__name__}: {exc}")
        st.stop()


def current_user():
    return st.session_state.get("user")


def refresh_user() -> None:
    user = current_user()
    if user:
        fresh = student_service.get_student(user["id"])
        if fresh:
            st.session_state["user"] = fresh


def flash(level: str, message: str) -> None:
    st.session_state["_flash"] = (level, message)


def show_flash() -> None:
    item = st.session_state.pop("_flash", None)
    if item:
        level, message = item
        getattr(st, level, st.info)(message)


def logout() -> None:
    st.session_state.clear()
    st.switch_page("app.py")


def render_sidebar(user: dict) -> None:
    with st.sidebar:
        st.markdown(f"**{html.escape(user['full_name'])}**")
        st.caption(f"{user['course']} · {user['academic_year']}" + (" · Admin" if user["role"] == "admin" else ""))
        if gemini_service.is_configured():
            st.caption(f"✨ Gemini: {gemini_service.get_model_name()}")
        else:
            st.caption("✨ Gemini: offline fallback (no API key)")
        if st.button("Logout", width="stretch", key="sidebar_logout"):
            logout()


def setup_page(title: str, icon: str = "🎓", require_login: bool = True, require_admin: bool = False):
    """Common page bootstrap. Returns the logged-in user (or None on the home page)."""
    st.set_page_config(page_title=f"{title} · {APP_NAME}", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH))
    ensure_database()
    user = current_user()
    if user is None:
        if require_login:
            st.warning("Please log in to continue.")
            st.page_link("app.py", label="Go to login", icon="🔐")
            st.stop()
        return None
    render_sidebar(user)
    if require_admin and user["role"] != "admin":
        st.error("This page is only available to administrators.")
        st.stop()
    show_flash()
    return user


def hero(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"<div class='cc-hero'><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ form pieces
def multiselect_with_extra(label: str, options: list, key: str, default=None, help_text=None) -> list:
    """Multiselect plus a free-text box for additional comma-separated values."""
    canonical = {o.lower(): o for o in options}

    def fix_case(values):
        return merge_lists([canonical.get(v.lower(), v) for v in values])

    default = fix_case(merge_lists(default or []))
    all_options = merge_lists(options, default)
    chosen = st.multiselect(label, all_options, default=default, key=f"{key}_sel", help=help_text)
    extra = st.text_input(f"Other {label.lower()} (comma-separated, optional)", key=f"{key}_extra")
    return fix_case(merge_lists(chosen, parse_list(extra)))


# ------------------------------------------------------------------- formatting
def fmt_dt(value) -> str:
    try:
        return value.strftime("%d %b %Y, %I:%M %p")
    except AttributeError:
        return str(value)


def fee_label(fee: float) -> str:
    return "Free" if not fee else f"₹{fee:,.0f}"


def esc(value) -> str:
    return html.escape(str(value or ""))


# --------------------------------------------------------------- recommendations
def load_recommendations(student: dict, top_n: int = 10, exclude_registered: bool = True) -> list:
    """Return [(event_dict, score, reasons)] ranked for the student."""
    df = event_service.get_events_df(open_for_registration=True)
    if df.empty:
        return []
    exclude = registration_service.get_registered_ids(student["id"]) if exclude_registered else set()
    recs = recommendation_service.recommend(student, df, top_n=top_n, exclude_ids=exclude)
    by_id = {e["id"]: e for e in event_service.list_events(ids=[int(i) for i in recs["id"]])}
    return [
        (by_id[int(r["id"])], float(r["score"]), list(r["reasons"]))
        for _, r in recs.iterrows() if int(r["id"]) in by_id
    ]


# -------------------------------------------------------------------- event card
def event_card(event: dict, student: dict, key_prefix: str, registered_ids: set, saved_ids: set,
               score=None, reasons=None) -> None:
    eid = event["id"]
    k = f"{key_prefix}_{eid}"
    now = datetime.now()
    is_registered = eid in registered_ids
    is_saved = eid in saved_ids
    past = event["event_date"] < now
    closed = event["registration_deadline"] < now
    icon = CATEGORY_ICONS.get(event["category"], "🎯")

    with st.container(border=True):
        left, right = st.columns([4, 1])
        left.markdown(f"#### {icon} {event['title']}")
        if score is not None:
            right.markdown(f"<div class='cc-match'>🎯 {int(round(score * 100))}% match</div>",
                           unsafe_allow_html=True)
        status_badge = ""
        if is_registered:
            status_badge = "<span class='cc-badge green'>✔ Registered</span>"
        elif past:
            status_badge = "<span class='cc-badge red'>Ended</span>"
        elif closed:
            status_badge = "<span class='cc-badge red'>Registration closed</span>"
        elif event["seats_left"] <= 0:
            status_badge = "<span class='cc-badge red'>Full</span>"
        st.markdown(
            f"<span class='cc-badge'>{esc(event['category'])}</span>"
            f"<span class='cc-badge blue'>{esc(event['mode'])}</span>"
            f"<span class='cc-badge amber'>{esc(event['difficulty'])}</span>"
            f"<span class='cc-badge green'>{fee_label(event['fee'])}</span>{status_badge}",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='cc-meta'>📅 {fmt_dt(event['event_date'])} &nbsp;•&nbsp; 📍 {esc(event['venue'])}"
            f" &nbsp;•&nbsp; 🏛️ {esc(event['organizer'])} &nbsp;•&nbsp; 🪑 {event['seats_left']} seats left</div>",
            unsafe_allow_html=True,
        )
        if reasons:
            st.caption("💡 " + " · ".join(reasons))

        with st.expander("Details · AI summary · Prep checklist"):
            st.write(event["description"])
            tags = split_list(event.get("tags"))
            if tags:
                st.caption("Topics: " + ", ".join(tags))
            st.caption(f"Registration closes: {fmt_dt(event['registration_deadline'])} · "
                       f"Suitable for: {event.get('target_courses') or 'All'}")

            c1, c2 = st.columns(2)
            if c1.button("✨ AI summary", key=f"sum_{k}", width="stretch"):
                with st.spinner("Summarising…"):
                    text, used_ai = gemini_service.generate_event_summary(event)
                    if used_ai:
                        event_service.save_ai_summary(eid, text)
                st.session_state[f"summary_{eid}"] = (text, used_ai)
            if c2.button("📝 Preparation checklist", key=f"chk_{k}", width="stretch"):
                with st.spinner("Preparing your checklist…"):
                    st.session_state[f"checklist_{eid}"] = gemini_service.generate_prep_checklist(event, student)

            summary = st.session_state.get(f"summary_{eid}")
            if not summary and event.get("ai_summary"):
                summary = (event["ai_summary"], True)
            if summary:
                st.markdown("**Summary**" + (" (Gemini)" if summary[1] else " (offline)"))
                st.write(summary[0])
            checklist = st.session_state.get(f"checklist_{eid}")
            if checklist:
                st.markdown("**Your checklist**" + (" (Gemini)" if checklist[1] else " (offline)"))
                st.markdown(checklist[0])

        b1, b2, _ = st.columns([1.3, 1, 2])
        if is_registered:
            if not past and b1.button("Cancel registration", key=f"cancel_{k}", width="stretch"):
                ok, msg = registration_service.cancel_registration(student["id"], eid)
                flash("success" if ok else "error", msg)
                st.rerun()
        else:
            disabled = past or closed or event["seats_left"] <= 0
            if b1.button("Register", key=f"reg_{k}", type="primary", disabled=disabled,
                         width="stretch"):
                ok, msg = registration_service.register_for_event(student["id"], eid)
                flash("success" if ok else "error", msg)
                st.rerun()
        if is_saved:
            if b2.button("★ Saved", key=f"unsave_{k}", width="stretch", help="Click to remove"):
                registration_service.unsave_event(student["id"], eid)
                flash("info", "Removed from saved events.")
                st.rerun()
        elif b2.button("☆ Save", key=f"save_{k}", width="stretch"):
            registration_service.save_event(student["id"], eid)
            flash("success", "Event saved.")
            st.rerun()
