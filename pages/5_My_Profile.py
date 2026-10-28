"""Profile editing and password change."""
import streamlit as st

from services import student_service
from utils.constants import (
    ACADEMIC_YEARS, CAREER_INTERESTS, COURSES, EVENT_CATEGORIES, SKILLS, INTERESTS,
)
from utils.ui_helpers import flash, hero, multiselect_with_extra, refresh_user, setup_page
from utils.validators import split_list

user = setup_page("My Profile", icon="👤")
hero("My Profile", "Keep your profile accurate — recommendations are built from it.")

tab_profile, tab_password = st.tabs(["Profile details", "Change password"])

with tab_profile:
    st.text_input("Email (cannot be changed)", value=user["email"], disabled=True)
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Full name", value=user["full_name"])
        college = c2.text_input("College name", value=user["college_name"])
        d1, d2 = st.columns(2)
        course = d1.selectbox("Course", COURSES, index=COURSES.index(user["course"])
                              if user["course"] in COURSES else 0)
        year = d2.selectbox("Academic year", ACADEMIC_YEARS, index=ACADEMIC_YEARS.index(user["academic_year"])
                            if user["academic_year"] in ACADEMIC_YEARS else 0)
        interests = multiselect_with_extra("Interests (technical and non-technical)", INTERESTS, "prof_interests",
                                           default=split_list(user["technical_interests"]))
        skills = multiselect_with_extra("Current skills", SKILLS, "prof_skills",
                                        default=split_list(user["skills"]))
        categories = st.multiselect(
            "Preferred event categories", EVENT_CATEGORIES, key="prof_categories",
            default=[c for c in split_list(user["preferred_categories"]) if c in EVENT_CATEGORIES],
        )
        careers = multiselect_with_extra("Career interests", CAREER_INTERESTS, "prof_careers",
                                         default=split_list(user["career_interests"]))
        saved = st.form_submit_button("Save profile", type="primary", width="stretch")
    if saved:
        ok, messages = student_service.update_profile(user["id"], {
            "full_name": full_name, "college_name": college, "course": course, "academic_year": year,
            "technical_interests": interests, "skills": skills, "preferred_categories": categories,
            "career_interests": careers,
        })
        if ok:
            refresh_user()
            flash("success", "Profile updated. Your recommendations will reflect the changes.")
            st.rerun()
        else:
            for message in messages:
                st.error(message)

with tab_password:
    with st.form("password_form", clear_on_submit=True):
        current = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        changed = st.form_submit_button("Update password", type="primary", width="stretch")
    if changed:
        ok, messages = student_service.change_password(user["id"], current, new, confirm)
        for message in messages:
            (st.success if ok else st.error)(message)
