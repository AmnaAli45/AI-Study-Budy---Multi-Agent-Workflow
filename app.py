# import streamlit as st
# from graph import workflow
# from langchain_core.messages import HumanMessage
# from dotenv import load_dotenv
# from langgraph.types import Command

# load_dotenv()

# st.set_page_config(page_title="AI Study Buddy", page_icon="📚")
# st.title("AI Study Buddy")
# st.caption("Learn any topic — with explanation and a quiz!")

# # ── Session state initialize ──────────────────────────────────
# if "phase" not in st.session_state:
#     st.session_state.phase = "input"
# if "thread_id" not in st.session_state:
#     st.session_state.thread_id = "session-1"
# if "state" not in st.session_state:
#     st.session_state.state = None

# config = {"configurable": {"thread_id": st.session_state.thread_id}}

# #  -------------------------------- Topic Input ----------------------------------
# if st.session_state.phase == "input":
#     topic = st.text_input(
#         "Which topic do you want to learn?",
#         placeholder="e.g. LangGraph nodes, Newton's laws, Python decorators..."
#     )

#     if st.button("Start") and topic:
#         with st.spinner("Analyzing..."):
#             result = workflow.invoke(
#                 {
#                     "user_msg": topic,
#                     "messages": [],
#                     "score": 0,
#                     "attempts": 0,
#                     "quiz": None,
#                 },
#                 config
#             )
#             st.session_state.state = result

#             if result.get("needs_classification"):
#                 st.session_state.phase = "clarify"
#             else:
#                 st.session_state.phase = "explain"

#         st.rerun()

# #  -------------------------------- Clarification (HITL) -----------------------------------
# elif st.session_state.phase == "clarify":
#     state = st.session_state.state

#     st.warning("I found the topic a bit ambiguous. Could you provide more clarification? (")
#     st.info(f"**Topic detected:** {state.get('topic', '')}")

#     clarification = st.text_input(
#         "Make the Topic more clear:",
#         placeholder="e.g. Do you mean recursion in Python, or just the concept of recursion??"
#     )

#     if st.button("Continue ") and clarification:
#         with st.spinner("Searching..."):
#             result = workflow.invoke(
#                 Command(resume=clarification),
#                 config
#             )
#             st.session_state.state = result
#             st.session_state.phase = "explain"
#         st.rerun()

# # ----------------------------------- Explanation -----------------------------------------
# elif st.session_state.phase == "explain":
#     state = st.session_state.state

#     st.success(f"**Topic:** {state['topic']}  |  **Level:** {state['knowledge_level']}")
#     st.markdown("---")
#     st.markdown(state["notes"])
#     st.markdown("---")

#     if st.button("Take Quiz!"):
#         with st.spinner("Generating Quiz..."):
#             result = workflow.invoke(None, config)
#             st.session_state.state = result
#             st.session_state.phase = "quiz"
#         st.rerun()

# #  ------------------------------------- Quiz --------------------------------------------------
# elif st.session_state.phase == "quiz":
#     state = st.session_state.state
#     quiz = state.get("quiz")

#     if not quiz:
#         st.error("Quiz generate nahi hua. Dobara koshish karo.")
#         if st.button("Wapas jao"):
#             st.session_state.phase = "explain"
#             st.rerun()
#         st.stop()

#     st.subheader("Quiz Time!")

#     # Quiz ka question aur options
#     st.markdown(f"**{quiz['question']}**")

#     options_map = quiz["options"]
#     answer = st.radio(
#         "Jawab chuno:",
#         options=[f"{k}: {v}" for k, v in options_map.items()],
#         index=None
#     )

#     if st.button("Submit") and answer:
#         selected_letter = answer.split(":")[0].strip()

#         with st.spinner("Checking..."):
#             result = workflow.invoke(
#                 {"messages": [HumanMessage(content=selected_letter)]},
#                 config
#             )
#             st.session_state.state = result

#         if result.get("last_answer_correct"):
#             st.success(f" Correct Answer ! {result['last_feedback']}")
#             st.balloons()
#         else:
#             correct_letter = quiz["correct"]
#             correct_text = options_map[correct_letter]
#             st.error(f" {result['last_feedback']}")
#             st.info(f"**Correct Answer:** {correct_letter}: {correct_text}")

#         st.session_state.phase = "done"
#         st.rerun()

# #  --------------------------------------- Done ---------------------------------------------------
# elif st.session_state.phase == "done":
#     state = st.session_state.state
#     score = state.get("score", 0)
#     correct = state.get("last_answer_correct", False)

#     st.markdown("---")

#     if correct:
#         st.success(f" Congaratulations! You gave correct Answer! Score: {score}/1")
#     else:
#         st.error(f"Score: {score}/1 — That's okay. The more you practice, the better you'll get!")

#     st.markdown("---")

#     col1, col2 = st.columns(2)

#     with col1:
#         if st.button("Learn New Topic"):
#             import time
#             st.session_state.phase = "input"
#             st.session_state.thread_id = f"session-{int(time.time())}"
#             st.session_state.state = None
#             st.rerun()

#     with col2:
#         if st.button("Review Notes Again"):
#             st.session_state.phase = "explain"
#             st.rerun()


import time
import streamlit as st
from graph import workflow
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from langgraph.types import Command

load_dotenv()

# ── Brand config ───────────────────────────────────────────────
APP_NAME = "AI StudyBudy"                      # swap in your product name
APP_TAGLINE = "Understand any topic, then prove it."
PRIMARY = "#4F46E5"
PRIMARY_DARK = "#3730A3"
BG = "#F8F9FC"
CARD_BG = "#FFFFFF"
TEXT_MUTED = "#6B7280"
SUCCESS = "#16A34A"
DANGER = "#DC2626"

st.set_page_config(page_title=APP_NAME, page_icon="◆", layout="centered")

# ── Global styling ─────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    #MainMenu, footer, header {{visibility: hidden;}}

    .stApp {{
        background-color: {BG};
    }}

    .block-container {{
        max-width: 720px;
        padding-top: 3rem;
    }}

    .brand-title {{
        font-size: 1.9rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0;
        letter-spacing: -0.02em;
    }}

    .brand-tagline {{
        color: {TEXT_MUTED};
        font-size: 0.95rem;
        margin-top: 0.15rem;
        margin-bottom: 2rem;
    }}

    .sb-card {{
        background: {CARD_BG};
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 1.75rem 1.85rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 1.25rem;
    }}

    .sb-badge {{
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }}

    .badge-level {{
        background: #EEF2FF;
        color: {PRIMARY_DARK};
    }}

    .badge-pass {{
        background: #DCFCE7;
        color: {SUCCESS};
    }}

    .badge-fail {{
        background: #FEE2E2;
        color: {DANGER};
    }}

    .question-counter {{
        color: {TEXT_MUTED};
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.4rem;
    }}

    .question-text {{
        font-size: 1.15rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 1rem;
    }}

    .score-line {{
        font-size: 0.9rem;
        color: {TEXT_MUTED};
    }}

    .result-score {{
        font-size: 2.6rem;
        font-weight: 700;
        color: #111827;
        margin: 0.25rem 0 0.5rem 0;
    }}

    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        border: none;
    }}

    .stButton > button[kind="primary"] {{
        background-color: {PRIMARY};
    }}

    .stButton > button[kind="primary"]:hover {{
        background-color: {PRIMARY_DARK};
    }}
</style>
""", unsafe_allow_html=True)

# ── Session state initialize ──────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "input"
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session-1"
if "state" not in st.session_state:
    st.session_state.state = None
if "pending_feedback" not in st.session_state:
    st.session_state.pending_feedback = None

config = {"configurable": {"thread_id": st.session_state.thread_id}}

st.markdown(f'<div class="brand-title">{APP_NAME}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-tagline">{APP_TAGLINE}</div>', unsafe_allow_html=True)

# ── Topic Input ─────────────────────────────────────────────────
if st.session_state.phase == "input":
    with st.container():
        st.markdown('<div class="sb-card">', unsafe_allow_html=True)
        st.markdown("**What would you like to learn today?**")
        topic = st.text_input(
            "Topic",
            placeholder="e.g. LangGraph nodes, Newton's laws, Python decorators",
            label_visibility="collapsed",
        )
        start = st.button("Start Learning", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    if start and topic:
        with st.spinner("Analyzing your topic..."):
            result = workflow.invoke(
                {"user_msg": topic, "messages": []},
                config
            )
            st.session_state.state = result

            if result.get("needs_classification"):
                st.session_state.phase = "clarify"
            else:
                st.session_state.phase = "explain"
        st.rerun()

# ── Clarification (HITL) ─────────────────────────────────────────
elif st.session_state.phase == "clarify":
    state = st.session_state.state

    st.markdown('<div class="sb-card">', unsafe_allow_html=True)
    st.markdown(f"**Detected topic:** {state.get('topic', '')}")
    st.markdown(
        f'<p style="color:{TEXT_MUTED}; margin-top:0.3rem;">'
        "This topic could mean a few things — a quick clarification will help tailor the explanation."
        "</p>",
        unsafe_allow_html=True,
    )
    clarification = st.text_input(
        "Clarify",
        placeholder="e.g. I mean recursion in Python specifically",
        label_visibility="collapsed",
    )
    confirm = st.button("Continue", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if confirm and clarification:
        with st.spinner("Preparing your explanation..."):
            result = workflow.invoke(Command(resume=clarification), config)
            st.session_state.state = result
            st.session_state.phase = "explain"
        st.rerun()

# ── Explanation ───────────────────────────────────────────────────
elif st.session_state.phase == "explain":
    state = st.session_state.state

    st.markdown(
        f'<span class="sb-badge badge-level">{state["knowledge_level"]}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {state['topic']}")

    st.markdown('<div class="sb-card">', unsafe_allow_html=True)
    st.markdown(state["notes"])
    st.markdown('</div>', unsafe_allow_html=True)

    total_q = len(state.get("quiz_questions", []) or [])
    if st.button(f"Take the Quiz ({total_q} questions)", type="primary"):
        st.session_state.phase = "quiz"
        st.session_state.pending_feedback = None
        st.rerun()

# ── Quiz ──────────────────────────────────────────────────────────
elif st.session_state.phase == "quiz":
    state = st.session_state.state
    quiz_list = state.get("quiz_questions") or []
    idx = state.get("current_question_index", 0)
    total = state.get("total_questions", len(quiz_list))

    if not quiz_list or idx >= len(quiz_list):
        st.error("The quiz couldn't be generated. Please go back and try again.")
        if st.button("Back to explanation"):
            st.session_state.phase = "explain"
            st.rerun()
        st.stop()

    quiz = quiz_list[idx]

    # Feedback from the previous question, shown once at the top
    if st.session_state.pending_feedback:
        fb = st.session_state.pending_feedback
        if fb["correct"]:
            st.success(fb["text"])
        else:
            st.error(fb["text"])
        st.session_state.pending_feedback = None

    st.progress(idx / total)
    st.markdown(f'<div class="question-counter">Question {idx + 1} of {total}</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="question-text">{quiz["question"]}</div>', unsafe_allow_html=True)

    options_map = quiz["options"]
    answer = st.radio(
        "Choose an answer",
        options=[f"{k}. {v}" for k, v in options_map.items()],
        index=None,
        label_visibility="collapsed",
    )
    submit = st.button("Submit Answer", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="score-line">Current score: {state.get("score", 0)} / {idx}</div>',
        unsafe_allow_html=True,
    )

    if submit and answer:
        selected_letter = answer.split(".")[0].strip()

        with st.spinner("Checking your answer..."):
            result = workflow.invoke(
                {"messages": [HumanMessage(content=selected_letter)]},
                config
            )
            st.session_state.state = result

        st.session_state.pending_feedback = {
            "correct": result.get("last_answer_correct", False),
            "text": result.get("last_feedback", ""),
        }

        if result.get("quiz_complete"):
            st.session_state.phase = "results"
        st.rerun()

# ── Results ─────────────────────────────────────────────────────
elif st.session_state.phase == "results":
    state = st.session_state.state
    score = state.get("score", 0)
    total = state.get("total_questions", 0)
    percentage = round((score / total) * 100) if total else 0
    passed = state.get("quiz_result") == "pass"

    st.markdown('<div class="sb-card" style="text-align:center;">', unsafe_allow_html=True)
    st.markdown(
        f'<span class="sb-badge {"badge-pass" if passed else "badge-fail"}">'
        f'{"Passed" if passed else "Not Passed"}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="result-score">{score} / {total}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="score-line">{percentage}% correct on <strong>{state.get("topic", "")}</strong></div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if not passed:
            if st.button("Retry Quiz", type="primary", use_container_width=True):
                with st.spinner("Preparing a new set of questions..."):
                    result = workflow.invoke(
                        {"messages": [HumanMessage(content="retry")]},
                        config
                    )
                    st.session_state.state = result
                    st.session_state.phase = "quiz"
                    st.session_state.pending_feedback = None
                st.rerun()
        else:
            if st.button("Review Notes", use_container_width=True):
                st.session_state.phase = "explain"
                st.rerun()

    with col2:
        if st.button("Learn a New Topic", use_container_width=True):
            st.session_state.phase = "input"
            st.session_state.thread_id = f"session-{int(time.time())}"
            st.session_state.state = None
            st.session_state.pending_feedback = None
            st.rerun()