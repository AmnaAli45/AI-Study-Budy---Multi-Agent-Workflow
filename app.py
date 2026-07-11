import streamlit as st
from graph import workflow
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from langgraph.types import Command

load_dotenv()

st.set_page_config(page_title="AI Study Buddy", page_icon="📚")
st.title("AI Study Buddy")
st.caption("Koi bhi topic seekho — explanation aur quiz ke saath!")

# ── Session state initialize ──────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "input"
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session-1"
if "state" not in st.session_state:
    st.session_state.state = None

config = {"configurable": {"thread_id": st.session_state.thread_id}}

#  -------------------------------- Topic Input ----------------------------------
if st.session_state.phase == "input":
    topic = st.text_input(
        "Which topic do you want to learn?",
        placeholder="e.g. LangGraph nodes, Newton's laws, Python decorators..."
    )

    if st.button("Start") and topic:
        with st.spinner("Analyzing..."):
            result = workflow.invoke(
                {
                    "user_msg": topic,
                    "messages": [],
                    "score": 0,
                    "attempts": 0,
                    "quiz": None,
                },
                config
            )
            st.session_state.state = result

            if result.get("needs_classification"):
                st.session_state.phase = "clarify"
            else:
                st.session_state.phase = "explain"

        st.rerun()

#  -------------------------------- Clarification (HITL) -----------------------------------
elif st.session_state.phase == "clarify":
    state = st.session_state.state

    st.warning("I found the topic a bit ambiguous. Could you provide more clarification? (")
    st.info(f"**Topic detected:** {state.get('topic', '')}")

    clarification = st.text_input(
        "Make the Topic more clear:",
        placeholder="e.g. Do you mean recursion in Python, or just the concept of recursion??"
    )

    if st.button("Continue ") and clarification:
        with st.spinner("Searching..."):
            result = workflow.invoke(
                Command(resume=clarification),
                config
            )
            st.session_state.state = result
            st.session_state.phase = "explain"
        st.rerun()

# ----------------------------------- Explanation -----------------------------------------
elif st.session_state.phase == "explain":
    state = st.session_state.state

    st.success(f"**Topic:** {state['topic']}  |  **Level:** {state['knowledge_level']}")
    st.markdown("---")
    st.markdown(state["notes"])
    st.markdown("---")

    if st.button("Take Quiz!"):
        with st.spinner("Generating Quiz..."):
            result = workflow.invoke(None, config)
            st.session_state.state = result
            st.session_state.phase = "quiz"
        st.rerun()

#  ------------------------------------- Quiz --------------------------------------------------
elif st.session_state.phase == "quiz":
    state = st.session_state.state
    quiz = state.get("quiz")

    if not quiz:
        st.error("Quiz generate nahi hua. Dobara koshish karo.")
        if st.button("Wapas jao"):
            st.session_state.phase = "explain"
            st.rerun()
        st.stop()

    st.subheader("Quiz Time!")

    # Quiz ka question aur options
    st.markdown(f"**{quiz['question']}**")

    options_map = quiz["options"]
    answer = st.radio(
        "Jawab chuno:",
        options=[f"{k}: {v}" for k, v in options_map.items()],
        index=None
    )

    if st.button("Submit") and answer:
        selected_letter = answer.split(":")[0].strip()

        with st.spinner("Checking..."):
            result = workflow.invoke(
                {"messages": [HumanMessage(content=selected_letter)]},
                config
            )
            st.session_state.state = result

        if result.get("last_answer_correct"):
            st.success(f" Correct Answer ! {result['last_feedback']}")
            st.balloons()
        else:
            correct_letter = quiz["correct"]
            correct_text = options_map[correct_letter]
            st.error(f" {result['last_feedback']}")
            st.info(f"**Correct Answer:** {correct_letter}: {correct_text}")

        st.session_state.phase = "done"
        st.rerun()

#  --------------------------------------- Done ---------------------------------------------------
elif st.session_state.phase == "done":
    state = st.session_state.state
    score = state.get("score", 0)
    correct = state.get("last_answer_correct", False)

    st.markdown("---")

    if correct:
        st.success(f" Congaratulations! You gave correct Answer! Score: {score}/1")
    else:
        st.error(f"Score: {score}/1 — That's okay. The more you practice, the better you'll get!")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Naya topic seekho"):
            import time
            st.session_state.phase = "input"
            st.session_state.thread_id = f"session-{int(time.time())}"
            st.session_state.state = None
            st.rerun()

    with col2:
        if st.button("Notes dobara dekho"):
            st.session_state.phase = "explain"
            st.rerun()