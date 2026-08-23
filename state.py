# from typing import TypedDict,Annotated,List
# from operator import add 

# class State(TypedDict):
#     user_msg: str
#     messages:Annotated[list, add]
#     topic:str
#     needs_classification: bool
#     knowledge_level : str
#     llm_description: str
#     notes: str
#     quiz: dict
#     score: int
#     attempts: int
#     last_answer_correct: bool
#     last_feedback : str

from typing import TypedDict, Annotated, List
from operator import add


class State(TypedDict):
    user_msg: str
    messages: Annotated[list, add]
    topic: str
    needs_classification: bool
    knowledge_level: str
    llm_description: str
    notes: str

    # ---------------- Quiz related state ----------------
    quiz_questions: List[dict]      # list of ~10 quiz question dicts
    current_question_index: int     # which question (0-based) is currently active
    score: int                      # correct answers so far in current attempt
    total_questions: int            # total number of questions in the quiz
    quiz_complete: bool             # True once all questions have been answered
    quiz_result: str                # "pass" or "fail" (set after evaluation)
    attempts: int                   # how many times the user has retried the full quiz
    last_answer_correct: bool
    last_feedback: str