"""Google Gemini integration with graceful fallbacks when no API key is configured.

Every public function returns (text, used_ai). When Gemini is unavailable (missing key, quota,
network error) a deterministic local fallback is produced and used_ai is False.
"""
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_MODEL = "gemini-flash-latest"  # alias that always points to the newest Flash model
SYSTEM_PROMPT = (
    "You are CampusConnect AI, a friendly assistant that helps college students in India choose and "
    "prepare for campus events (workshops, seminars, hackathons, coding competitions, technical events "
    "and career programs). Be concise, practical and encouraging. Never invent event details."
)

_client = None
_last_error = ""
_model_override = None  # set automatically if the configured model is unavailable


# ---------------------------------------------------------------- configuration
def _api_key() -> str:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""


def get_model_name() -> str:
    if _model_override:
        return _model_override
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def is_configured() -> bool:
    return bool(_api_key().strip())


def get_last_error() -> str:
    return _last_error


_SKIP_WORDS = ("image", "tts", "live", "audio", "embedding", "robotics", "computer-use", "native", "learnlm")


def _model_rank(name: str):
    """Higher is better: newest version first, stable before preview/experimental, flash before lite."""
    version = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
    ver = float(version.group(1)) if version else 0.0
    unstable = any(w in name for w in ("preview", "exp"))
    return (ver, not unstable, "lite" not in name)


def _discover_model(client, exclude: str):
    """Ask the API which models this key can use and pick the best Flash model."""
    candidates = []
    for m in client.models.list():
        name = (getattr(m, "name", "") or "").replace("models/", "")
        actions = getattr(m, "supported_actions", None) or []
        if "flash" in name and "generateContent" in actions and name != exclude \
                and not any(w in name for w in _SKIP_WORDS):
            candidates.append(name)
    return max(candidates, key=_model_rank) if candidates else None


def _is_model_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return "404" in text or "not_found" in text or "no longer available" in text or "not found" in text


def generate_text(prompt: str, system: str = SYSTEM_PROMPT):
    """Call Gemini. Returns the text, or None if unavailable or failed.

    If the configured model has been retired (404), the app lists the models your API key can use,
    switches to the newest Flash model automatically and retries once.
    """
    global _client, _last_error, _model_override
    if not is_configured():
        _last_error = "GEMINI_API_KEY is not set."
        return None
    try:
        from google import genai
        from google.genai import types

        if _client is None:
            # 30 second limit so the app never waits forever on a slow "thinking" model
            _client = genai.Client(api_key=_api_key(), http_options=types.HttpOptions(timeout=30000))
        config = types.GenerateContentConfig(
            system_instruction=system, temperature=0.6, max_output_tokens=2048,
            thinking_config=types.ThinkingConfig(thinking_budget=0),  # answer directly, no long reasoning
        )
        plain_config = types.GenerateContentConfig(system_instruction=system, temperature=0.6,
                                                   max_output_tokens=2048)

        def call(model_name):
            """Retry a few times only for transient service overloads."""
            use = config
            for attempt in range(3):
                try:
                    return _client.models.generate_content(model=model_name, contents=prompt, config=use)
                except Exception as exc:
                    text = f"{type(exc).__name__} {exc}".upper()
                    if use is config and ("THINKING" in text or "INVALID_ARGUMENT" in text or "400" in text):
                        # this model rejects the thinking setting: retry with plain settings
                        use = plain_config
                        continue
                    busy = any(w in text for w in ("503", "504", "UNAVAILABLE", "OVERLOADED", "DEADLINE", "TIMEOUT", "TIMED OUT"))
                    if not busy or attempt == 2:
                        raise
                    time.sleep(2 * (attempt + 1))

        try:
            try:
                response = call(get_model_name())
            except Exception as exc:
                text_err = f"{type(exc).__name__} {exc}".upper()
                if any(w in text_err for w in ("503", "504", "UNAVAILABLE", "DEADLINE", "TIMEOUT", "TIMED OUT", "429", "RESOURCE_EXHAUSTED")) \
                        and "lite" not in get_model_name():
                    response = call("gemini-flash-lite-latest")  # try the lighter model during overload or quota limits
                else:
                    raise
        except Exception as exc:
            if not _is_model_error(exc):
                raise
            replacement = _discover_model(_client, exclude=get_model_name())
            if not replacement:
                raise
            _model_override = replacement
            response = call(replacement)
        text = (response.text or "").strip()
        if not text:
            _last_error = "Gemini returned an empty response."
            return None
        _last_error = ""
        return text
    except Exception as exc:  # network, quota, invalid key, unsupported model ...
        error = f"{type(exc).__name__}: {exc}"
        if "429" in error or "RESOURCE_EXHAUSTED" in error.upper():
            _last_error = "Gemini quota/rate limit reached. Check the API project's quota or try again after it resets."
        else:
            _last_error = error
        return None


# ------------------------------------------------------------------- formatting
def _fmt_date(value) -> str:
    try:
        return value.strftime("%d %b %Y, %I:%M %p")
    except AttributeError:
        return str(value)


def _fee(event) -> str:
    fee = float(event.get("fee") or 0)
    return "Free" if fee == 0 else f"₹{fee:,.0f}"


def _event_block(event) -> str:
    return (
        f"Title: {event['title']}\nCategory: {event['category']}\nOrganizer: {event['organizer']}\n"
        f"Date: {_fmt_date(event['event_date'])}\nVenue: {event['venue']} ({event['mode']})\n"
        f"Difficulty: {event['difficulty']}\nFee: {_fee(event)}\nTags: {event.get('tags') or 'n/a'}\n"
        f"Suitable for: {event.get('target_courses') or 'All'}\nDescription: {event['description']}"
    )


def _profile_block(student) -> str:
    return (
        f"Course: {student.get('course')} ({student.get('academic_year')})\n"
        f"Interests: {student.get('technical_interests') or 'n/a'}\n"
        f"Skills: {student.get('skills') or 'n/a'}\n"
        f"Career interests: {student.get('career_interests') or 'n/a'}"
    )


# ---------------------------------------------------------------------- summary
def generate_event_summary(event: dict):
    prompt = (
        "Write a short, engaging summary (3-4 sentences, plain text, no headings) of this college event "
        "for students. Mention who should attend and one key takeaway. Use only the facts below.\n\n"
        + _event_block(event)
    )
    text = generate_text(prompt)
    if text:
        return text, True
    return _fallback_summary(event), False


def _fallback_summary(event) -> str:
    sentences = [s.strip() for s in str(event["description"]).replace("\n", " ").split(".") if s.strip()]
    core = ". ".join(sentences[:2]) + ("." if sentences else "")
    tags = event.get("tags") or ""
    return (
        f"{event['title']} is a {event['difficulty'].lower()}-level {event['category'].lower()} organised by "
        f"{event['organizer']} on {_fmt_date(event['event_date'])} ({event['mode'].lower()}, {event['venue']}). "
        f"{core} Registration is {_fee(event).lower() if _fee(event) == 'Free' else _fee(event)}"
        f"{'; focus areas: ' + tags if tags else ''}. Suitable for: {event.get('target_courses') or 'All'}."
    )


# -------------------------------------------------------------------- checklist
_CATEGORY_PREP = {
    "Hackathon": [
        "Form a team of 2–4 and agree on roles (developer, designer, presenter)",
        "Shortlist two or three problem ideas you could build in the time available",
        "Set up a GitHub repository and a working development environment",
        "Prepare a 3-minute pitch outline: problem, solution, demo, impact",
    ],
    "Coding Competition": [
        "Practise 10–15 timed problems on topics from the event tags",
        "Revise core data structures, complexity analysis and common patterns",
        "Set up your preferred language, fast input/output templates and an IDE",
        "Read the contest rules and scoring system carefully",
    ],
    "Workshop": [
        "Install the tools or libraries mentioned in the description beforehand",
        "Revise the prerequisite basics so you can follow along with hands-on tasks",
        "Prepare two or three questions you want answered",
        "Create a folder or repository to store workshop code and notes",
    ],
    "Seminar": [
        "Read about the speaker or topic for ten minutes before attending",
        "Write down two or three questions for the Q&A session",
        "Carry a notebook or notes app to capture key takeaways",
    ],
    "Technical Event": [
        "Review the event schedule and pick the sessions or stalls you want to visit",
        "Revise basic concepts of the technologies being demonstrated",
        "Prepare to network: be ready to introduce yourself in 30 seconds",
    ],
    "Soft Skills": [
        "Think of one real situation where you want to improve and bring it to the session",
        "Be ready to take part: these sessions are activity-based, not just lectures",
        "Bring a notebook to write down exercises and feedback",
        "Plan to practise what you learn within a week",
    ],
    "Cultural & Creative": [
        "Prepare something to share, such as a portfolio, sample work or an idea",
        "Check what you need to bring (instruments, camera, costumes or a laptop)",
        "Team up with a friend if the event has group activities",
    ],
    "Career Development": [
        "Update your resume and LinkedIn profile before the session",
        "Prepare a 60-second self-introduction",
        "List your top projects and be ready to explain your role in each",
        "Dress professionally and carry printed copies of your resume if it is in person",
    ],
}


def generate_prep_checklist(event: dict, student: dict):
    prompt = (
        "Create a practical preparation checklist for this student attending the event below. "
        "Use Markdown with exactly these four sections as bold headings: **Before the event**, "
        "**What to carry or set up**, **During the event**, **After the event**. Give 3–5 short checkbox "
        "bullets (- [ ] ...) per section, personalised to the student's skills and interests. "
        "Do not invent facts about the event.\n\nEVENT\n"
        + _event_block(event) + "\n\nSTUDENT\n" + _profile_block(student)
    )
    text = generate_text(prompt)
    if text:
        return text, True
    return _fallback_checklist(event, student), False


def _fallback_checklist(event, student) -> str:
    tags = [t.strip() for t in str(event.get("tags") or "").split(",") if t.strip()]
    skills = {s.strip().lower() for s in str(student.get("skills") or "").split(",") if s.strip()}
    before = list(_CATEGORY_PREP.get(event["category"], _CATEGORY_PREP["Technical Event"]))
    for tag in tags[:3]:
        if tag.lower() in skills:
            before.append(f"You already know {tag} — revise intermediate topics to get more out of the event")
        else:
            before.append(f"Spend 30 minutes learning the basics of {tag}")
    if event["mode"] == "Online":
        carry = ["Test your internet, camera and microphone 30 minutes early",
                 "Save the meeting link and keep the registration confirmation handy",
                 "Keep your laptop charged and close unnecessary tabs"]
    else:
        carry = [f"Plan your travel to {event['venue']} and arrive 15 minutes early",
                 "Carry your college ID card and a copy of your registration confirmation",
                 "Bring a laptop, charger, notebook and pen"]
    if float(event.get("fee") or 0) > 0:
        carry.append(f"Keep the registration fee ({_fee(event)}) or payment proof ready")
    during = ["Be on time and introduce yourself to the organisers and peers",
              "Take notes on key tools, ideas and contacts",
              "Ask at least one question or contribute in a discussion"]
    after = ["Organise your notes and code within 24 hours",
             "Connect with new contacts on LinkedIn",
             "Add what you learned (or any certificate) to your resume and portfolio"]

    def section(title, items):
        return f"**{title}**\n" + "\n".join(f"- [ ] {i}" for i in items)

    return "\n\n".join([
        section("Before the event", before), section("What to carry or set up", carry),
        section("During the event", during), section("After the event", after),
    ])


# ---------------------------------------------------------------------- chatbot
def generate_assistant_reply(question: str, student: dict, context_events: list, history: list):
    """Answer a student's question using only the supplied events as event facts."""
    lines = []
    for e in context_events:
        lines.append(
            f"- [{e['id']}] {e['title']} | {e['category']} | {_fmt_date(e['event_date'])} | {e['mode']} | "
            f"{e['difficulty']} | {_fee(e)} | tags: {e.get('tags') or 'n/a'} | seats left: {e['seats_left']}"
        )
    events_text = "\n".join(lines) if lines else "(no matching upcoming events)"
    convo = "\n".join(f"{m['role'].title()}: {m['content']}" for m in history[-6:])
    prompt = (
        "Answer the student's question. For any statement about specific events use ONLY the event list "
        "below; if nothing fits, say so honestly and suggest what to look for. Keep the answer under "
        "180 words, use short bullet points when listing events, and mention event titles exactly.\n\n"
        f"STUDENT PROFILE\n{_profile_block(student)}\n\nUPCOMING EVENTS\n{events_text}\n\n"
        f"RECENT CONVERSATION\n{convo or '(none)'}\n\nQUESTION: {question}"
    )
    text = generate_text(prompt)
    if text:
        return text, True
    return _fallback_reply(context_events), False


def _fallback_reply(context_events) -> str:
    if not context_events:
        return ("I couldn't find upcoming events matching that. Try asking about a topic such as "
                "*machine learning*, *hackathons*, *web development* or *placements*.")
    lines = ["Here are the upcoming events that best match your question and profile "
             "(AI chat is in offline mode, so these come from the recommendation engine):", ""]
    for e in context_events[:12]:
        lines.append(f"- **{e['title']}** — {e['category']}, {_fmt_date(e['event_date'])}, "
                     f"{e['mode']}, {_fee(e)}")
    return "\n".join(lines)
