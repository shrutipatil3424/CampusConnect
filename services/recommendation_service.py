"""Content-based event recommendation using TF-IDF and cosine similarity.

This module is pure (no database or Streamlit imports) so it is easy to test.

Final score for an event (0..1):
    0.70 * text similarity  (TF-IDF cosine between student profile and event text)
  + 0.20 * category match   (event category is one of the student's preferred categories)
  + 0.10 * course fit       (event targets the student's course, or targets everyone)

Raw cosine similarity between a short profile and a long description is naturally small,
so it is scaled so that a similarity of TEXT_SIM_SATURATION counts as a perfect text match.
"""
from __future__ import annotations

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TEXT_SIM_SATURATION = 0.35
W_TEXT, W_CATEGORY, W_COURSE = 0.70, 0.20, 0.10


def _split(value) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, float) and pd.isna(value):
        return []
    return [p.strip() for p in str(value).replace("\n", ",").split(",") if p.strip()]


def build_student_text(student: dict) -> str:
    """Turn a student profile into weighted text (important fields repeated)."""
    parts = []
    parts += _split(student.get("technical_interests")) * 3
    parts += _split(student.get("skills")) * 2
    parts += _split(student.get("career_interests")) * 2
    parts += _split(student.get("preferred_categories")) * 2
    parts += _split(student.get("course"))
    return " ".join(parts)


def build_event_text(event) -> str:
    """Turn an event record into weighted text."""
    get = event.get if hasattr(event, "get") else (lambda k, d=None: d)
    title = str(get("title", "") or "")
    category = str(get("category", "") or "")
    tags = " ".join(_split(get("tags", "")))
    description = str(get("description", "") or "")
    courses = " ".join(_split(get("target_courses", "")))
    difficulty = str(get("difficulty", "") or "")
    return " ".join([title, title, category, category, tags, tags, description, courses, difficulty])


def _vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)


def _with_result_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["score"] = pd.Series(dtype=float)
    out["match_percent"] = pd.Series(dtype=int)
    out["reasons"] = pd.Series(dtype=object)
    return out


def _top_terms(student_vec: list, event_vec: list, names, limit: int = 3) -> list:
    """Shared TF-IDF terms that contribute most to the match, preferring phrases."""
    products = [(s * e, i) for i, (s, e) in enumerate(zip(student_vec, event_vec)) if s > 0 and e > 0]
    products.sort(reverse=True)
    chosen = []
    for _, idx in products[:10]:
        term = names[idx]
        if any(term in c or c in term for c in chosen):
            if not any(term in c for c in chosen) and any(c in term for c in chosen):
                chosen = [c for c in chosen if c not in term] + [term]
            continue
        chosen.append(term)
    return chosen[:limit]


def recommend(student: dict, events_df: pd.DataFrame, top_n: int = 10, exclude_ids=None) -> pd.DataFrame:
    """Rank events for a student. Returns events plus score, match_percent and reasons."""
    if events_df is None or events_df.empty:
        return _with_result_columns(events_df if events_df is not None else pd.DataFrame(columns=["id"]))

    df = events_df.copy().reset_index(drop=True)
    if exclude_ids:
        df = df[~df["id"].isin(list(exclude_ids))].reset_index(drop=True)
    if df.empty:
        return _with_result_columns(df)

    records = df.to_dict("records")
    event_texts = [build_event_text(r) for r in records]
    student_text = build_student_text(student)

    sims = [0.0] * len(df)
    student_vec, event_matrix, names = None, None, []
    try:
        vec = _vectorizer()
        matrix = vec.fit_transform(event_texts + [student_text])
        names = vec.get_feature_names_out()
        event_matrix, student_vec = matrix[:-1], matrix[-1]
        sims = cosine_similarity(student_vec, event_matrix).ravel().tolist()
    except ValueError:  # empty vocabulary
        pass

    preferred = {c.lower() for c in _split(student.get("preferred_categories"))}
    course = str(student.get("course") or "").strip().lower()

    scores, reasons_col = [], []
    student_dense = student_vec.toarray().ravel().tolist() if student_vec is not None else []
    for i, rec in enumerate(records):
        category = str(rec.get("category") or "")
        cat_match = 1.0 if category.lower() in preferred else 0.0
        targets = [t.lower() for t in _split(rec.get("target_courses"))]
        if not targets or "all" in targets:
            course_fit = 0.5
        else:
            course_fit = 1.0 if course in targets else 0.0
        text_part = min(1.0, sims[i] / TEXT_SIM_SATURATION)
        score = W_TEXT * text_part + W_CATEGORY * cat_match + W_COURSE * course_fit
        scores.append(round(min(1.0, max(0.0, score)), 4))

        reasons = []
        if student_dense and event_matrix is not None and sims[i] > 0:
            terms = _top_terms(student_dense, event_matrix[i].toarray().ravel().tolist(), names)
            if terms:
                reasons.append("Matches your profile: " + ", ".join(terms))
        if cat_match:
            reasons.append(f"{category} is one of your preferred categories")
        if course_fit == 1.0:
            reasons.append(f"Designed for {student.get('course')} students")
        reasons_col.append(reasons)

    df["score"] = scores
    df["match_percent"] = [int(round(s * 100)) for s in scores]
    df["reasons"] = reasons_col
    sort_cols, ascending = ["score"], [False]
    if "event_date" in df.columns:
        sort_cols.append("event_date")
        ascending.append(True)
    df = df.sort_values(sort_cols, ascending=ascending, kind="stable").reset_index(drop=True)
    return df.head(top_n)


def similar_events(event_id: int, events_df: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    """Events most similar to the given one (TF-IDF cosine similarity)."""
    if events_df is None or events_df.empty or event_id not in set(events_df["id"]):
        return _with_result_columns(events_df if events_df is not None else pd.DataFrame(columns=["id"]))
    df = events_df.reset_index(drop=True)
    matrix = _vectorizer().fit_transform([build_event_text(r) for r in df.to_dict("records")])
    pos = int(df.index[df["id"] == event_id][0])
    sims = cosine_similarity(matrix[pos], matrix).ravel()
    out = df.copy()
    out["score"] = sims
    out["match_percent"] = (sims * 100).round().astype(int)
    out["reasons"] = [[] for _ in range(len(out))]
    out = out[out["id"] != event_id]
    return out.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)


def search_events(query: str, events_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Semantic keyword search: TF-IDF cosine similarity between a query and events."""
    if events_df is None or events_df.empty or not (query or "").strip():
        return _with_result_columns(events_df if events_df is not None else pd.DataFrame(columns=["id"]))
    df = events_df.reset_index(drop=True)
    texts = [build_event_text(r) for r in df.to_dict("records")]
    try:
        matrix = _vectorizer().fit_transform(texts + [query])
    except ValueError:
        return _with_result_columns(df.iloc[0:0])
    sims = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    out = df.copy()
    out["score"] = sims
    out["match_percent"] = (sims * 100).round().astype(int)
    out["reasons"] = [[] for _ in range(len(out))]
    out = out[out["score"] > 0]
    return out.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)
