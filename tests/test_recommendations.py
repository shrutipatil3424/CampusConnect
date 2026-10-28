from datetime import datetime, timedelta

import pandas as pd

from services.recommendation_service import (
    build_student_text, recommend, search_events, similar_events,
)


def sample_events():
    base = datetime(2026, 11, 1, 10, 0)
    rows = [
        (1, "Machine Learning Bootcamp", "Hands-on machine learning with python and scikit-learn.",
         "Workshop", "machine learning, python, data science", "MCA, BCA"),
        (2, "Ethical Hacking Seminar", "Learn penetration testing and network security basics.",
         "Seminar", "cyber security, networking", "All"),
        (3, "AI Hackathon", "24 hour hackathon building artificial intelligence products.",
         "Hackathon", "artificial intelligence, python, innovation", "All"),
        (4, "Android App Workshop", "Build mobile apps with kotlin and java.",
         "Workshop", "mobile app development, android, kotlin", "BE/BTech"),
    ]
    return pd.DataFrame([
        {"id": i, "title": t, "description": d, "category": c, "tags": tg,
         "target_courses": tc, "difficulty": "Beginner", "event_date": base + timedelta(days=i)}
        for i, t, d, c, tg, tc in rows
    ])


def ml_student():
    return {
        "course": "MCA", "technical_interests": "Machine Learning, Artificial Intelligence",
        "skills": "Python, Pandas", "preferred_categories": "Hackathon, Workshop",
        "career_interests": "Data Scientist",
    }


def test_relevant_events_rank_first():
    recs = recommend(ml_student(), sample_events(), top_n=4)
    assert list(recs["id"][:2]) == [1, 3] or set(recs["id"][:2]) == {1, 3}
    assert recs.iloc[-1]["id"] in (2, 4)


def test_scores_are_bounded_and_sorted():
    recs = recommend(ml_student(), sample_events())
    assert recs["score"].between(0, 1).all()
    assert recs["score"].is_monotonic_decreasing
    assert (recs["match_percent"] == (recs["score"] * 100).round().astype(int)).all()


def test_reasons_are_provided_for_top_match():
    recs = recommend(ml_student(), sample_events())
    assert len(recs.iloc[0]["reasons"]) >= 1


def test_exclude_ids():
    recs = recommend(ml_student(), sample_events(), exclude_ids=[1])
    assert 1 not in set(recs["id"])


def test_empty_profile_does_not_crash():
    recs = recommend({}, sample_events())
    assert len(recs) == 4


def test_empty_events():
    recs = recommend(ml_student(), pd.DataFrame())
    assert recs.empty


def test_build_student_text_contains_profile_terms():
    text = build_student_text(ml_student()).lower()
    assert "machine learning" in text and "python" in text and "mca" in text


def test_similar_events_excludes_self():
    sim = similar_events(1, sample_events(), top_n=3)
    assert 1 not in set(sim["id"])
    scores = dict(zip(sim["id"], sim["score"]))
    assert scores[3] > scores[2]  # python/AI event is closer to the ML bootcamp than security


def test_search_events():
    found = search_events("network security", sample_events())
    assert not found.empty and found.iloc[0]["id"] == 2
    assert search_events("zzzzqqq", sample_events()).empty


def test_non_technical_interests_get_non_technical_events():
    """A student with only non-technical interests must be recommended non-technical events first."""
    from database.seed_data import non_technical_events, sample_events
    events = pd.DataFrame([{**e, "id": i + 1} for i, e in enumerate(sample_events() + non_technical_events())])
    cases = {
        "Public Speaking, Debate, Communication Skills": "Public Speaking",
        "Photography, Video Editing, Social Media": "Photography",
        "Volunteering, Leadership, Event Management": "Volunteering",
        "Music, Dance, Drama and Theatre": "Cultural Fest",
    }
    for interests, expected in cases.items():
        student = {"course": "BCA", "technical_interests": interests, "skills": "Communication",
                   "preferred_categories": "Soft Skills, Cultural & Creative", "career_interests": "Entrepreneur"}
        top3 = list(recommend(student, events, top_n=3)["title"])
        assert any(expected in t for t in top3), (interests, top3)
