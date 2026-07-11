from typing import TypedDict,Annotated,List
from operator import add 

class State(TypedDict):
    user_msg: str
    messages:Annotated[list, add]
    topic:str
    needs_classification: bool
    knowledge_level : str
    llm_description: str
    notes: str
    quiz: dict
    score: int
    attempts: int
    last_answer_correct: bool
    last_feedback : str