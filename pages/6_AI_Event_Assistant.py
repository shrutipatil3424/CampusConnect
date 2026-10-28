"""AI Event Assistant: chat about events and generate preparation checklists."""
import streamlit as st

from services import event_service, gemini_service, recommendation_service, registration_service
from utils.date_filter import parse_date_range
from utils.ui_helpers import fmt_dt, hero, setup_page

user = setup_page("AI Event Assistant", icon="🤖")
hero("AI Event Assistant", "Ask what to attend, or get a personal preparation plan for any event.")

if gemini_service.is_configured():
    st.success(f"Gemini connected · model `{gemini_service.get_model_name()}`")
else:
    st.info("No Gemini API key found — the assistant uses the built-in offline fallback. "
            "Add `GEMINI_API_KEY` to your `.env` file for full AI answers.")

tab_chat, tab_prep = st.tabs(["💬 Ask the assistant", "📝 Event preparation planner"])


def build_context(question: str) -> list:
    """Events relevant to the question (TF-IDF search) plus the student's top recommendations.

    If the question has a date limit ("before 30 October", "this week") only events in that range are used.
    """
    df = event_service.get_events_df(open_for_registration=False)
    if df.empty:
        return []
    start, end, _ = parse_date_range(question)
    if start is not None or end is not None:
        if start is not None:
            df = df[df["event_date"] >= start]
        if end is not None:
            df = df[df["event_date"] < end]
        if df.empty:
            return []
        df = df.sort_values("event_date")
        return [e for e in event_service.list_events(ids=[int(i) for i in df["id"]])]
    ids = []
    for found in recommendation_service.search_events(question, df, top_n=5)["id"]:
        ids.append(int(found))
    for recommended in recommendation_service.recommend(user, df, top_n=3)["id"]:
        if int(recommended) not in ids:
            ids.append(int(recommended))
    by_id = {e["id"]: e for e in event_service.list_events(ids=ids)}
    return [by_id[i] for i in ids if i in by_id]


with tab_chat:
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    quick = None
    q1, q2, q3 = st.columns(3)
    if q1.button("Suggest events for my interests", width="stretch"):
        quick = "Which upcoming events best match my interests and skills?"
    if q2.button("Hackathons & competitions", width="stretch"):
        quick = "What hackathons or coding competitions are coming up and how should I choose?"
    if q3.button("Events for my career goals", width="stretch"):
        quick = "Which events will help me reach my career interests?"

    for message in st.session_state["chat"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask about events, preparation or career paths…") or quick
    if question:
        history = list(st.session_state["chat"])
        st.session_state["chat"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                answer, used_ai = gemini_service.generate_assistant_reply(
                    question, user, build_context(question), history)
            st.markdown(answer)
            if not used_ai and gemini_service.is_configured():
                st.caption(f"Gemini was unavailable ({gemini_service.get_last_error()[:160]}); "
                           "showing the offline answer.")
        st.session_state["chat"].append({"role": "assistant", "content": answer})

    if st.session_state["chat"] and st.button("Clear conversation"):
        st.session_state["chat"] = []
        st.rerun()

with tab_prep:
    events = event_service.list_events()
    if not events:
        st.info("There are no upcoming events to plan for.")
    else:
        registered = registration_service.get_registered_ids(user["id"])
        events.sort(key=lambda e: (e["id"] not in registered, e["event_date"]))
        labels = {e["id"]: f"{'✔ ' if e['id'] in registered else ''}{e['title']} — {fmt_dt(e['event_date'])}"
                  for e in events}
        chosen_id = st.selectbox("Choose an event", list(labels), format_func=labels.get)
        chosen = next(e for e in events if e["id"] == chosen_id)
        if st.button("Generate my checklist", type="primary"):
            with st.spinner("Building your personalised checklist…"):
                st.session_state["prep_result"] = (chosen_id, *gemini_service.generate_prep_checklist(chosen, user))
        result = st.session_state.get("prep_result")
        if result and result[0] == chosen_id:
            st.markdown(f"#### Checklist for {chosen['title']}" + (" · Gemini" if result[2] else " · offline"))
            st.markdown(result[1])
            st.download_button("⬇️ Download checklist", result[1].encode("utf-8"),
                               file_name=f"checklist_event_{chosen_id}.md", mime="text/markdown")
