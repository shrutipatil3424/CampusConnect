# 🎓 CampusConnect AI — Personalized College Event Discovery System

Students register with their interests, skills, course and career goals. The app recommends campus events
(workshops, seminars, hackathons, coding competitions, technical and career events) using machine learning,
and uses Google Gemini to write event summaries, preparation checklists and chat answers.

**Stack:** Python · Streamlit · MySQL (`mysql-connector-python`) · Scikit-learn (`TfidfVectorizer`,
`cosine_similarity`) · Pandas · Google Gemini (`google-genai`) · `python-dotenv` · Werkzeug password hashing.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # then set DB_PASSWORD (and optionally GEMINI_API_KEY)
streamlit run app.py
```

The database, tables, an admin account, a demo student and 20 sample events are created automatically on
first run (MySQL just needs to be running). To seed manually: `python -m database.seed_data`.

| Account | Email | Password |
|---|---|---|
| Admin | `admin@campusconnect.ai` | `Admin@12345` (change via `.env` before first run) |
| Demo student | `demo@campusconnect.ai` | `Demo@1234` |

Without `GEMINI_API_KEY` everything still works: summaries, checklists and the assistant switch to built-in
offline fallbacks (labelled "offline" in the UI). `GEMINI_MODEL` defaults to `gemini-flash-latest`; if a model is retired the app switches to the newest available Flash model automatically.

## Features

- **Auth:** registration with full validation, duplicate-email rejection, hashed passwords, login/logout.
- **Recommendations:** TF-IDF vectors of the student profile and event text, ranked by cosine similarity,
  blended with category and course fit (`services/recommendation_service.py`). Each card shows a match % and why.
- **Interests:** technical and non-technical (public speaking, leadership, photography, music, volunteering…), with matching Soft Skills and Cultural & Creative events.
- **Discover:** personalised tab plus a searchable catalogue (category, mode, free-only, date range).
- **Register / save events,** seat limits, deadlines, cancel and re-register, CSV export.
- **Gemini:** event summaries (cached in MySQL), personalised preparation checklists, chat assistant.
- **Admin panel:** analytics, create/edit/hide/delete events, attendance tracking, student list, CSV exports.

## Project layout

```
app.py                 login, registration and home
pages/                 1_Dashboard … 7_Admin_Panel (Streamlit multipage)
services/              auth, student, event, registration, recommendation (ML), gemini
database/              schema.sql, db_connection.py, seed_data.py
utils/                 constants, validators, ui_helpers
tests/                 pytest unit tests (recommender and validators)
```

## Tests

```bash
python -m pytest tests                      # unit tests
python tests/evaluate_recommender.py        # ranking metrics (Precision@K, Recall@K, MRR, NDCG)
```
