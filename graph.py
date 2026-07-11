from dotenv import load_dotenv
import operator
from langchain_groq import ChatGroq
from typing import TypedDict,List,Literal
from pydantic import Field,BaseModel
from langchain_core.messages import AIMessage,SystemMessage,HumanMessage
from langgraph.graph import START,END,StateGraph
from langgraph.types import Command,interrupt # to implement the concept of human in the loop
from langchain_core.tools import tool
import requests
from tavily import TavilyClient
import os
import urllib.parse
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from state import State


load_dotenv()

model = ChatGroq( model="llama-3.3-70b-versatile",)

#  ------------------------Schema of Understan Topic Node ---------------------------------
class understandtopic(BaseModel):
    topic: str
    knowledge_level :  Literal["beginner" ,"intermediate","advanced"]
    needs_classification: bool = Field(description="Boolean value. Set to true if the topic is unclear or ambiguous, false if the topic is clear."
    )

#  ------------------------------ Structured LLM ------------------------------------------
struc_model= model.with_structured_output(understandtopic,strict = True)

# ------------------------------ Understand Topic Node -----------------------------------
topic_msg = """You are the first node in an AI Study Buddy pipeline.

Your job is to analyze the user's study request and extract structured information from it.

Given the user's message, you must determine:
1. The main topic they want to study (e.g. "Python decorators", "Newton's laws", "LangGraph nodes")
2. Their apparent knowledge level based on how they asked:
   - "beginner" — they used simple language, asked "what is", or seem unfamiliar
   - "intermediate" — they know basics, asking "how does X work" or "difference between"
   - "advanced" — they used technical terms, asking about internals or edge cases
3. Whether the topic is clear enough to proceed or needs clarification:
   - "clear" — you know exactly what to study and can search for it
   - "unclear" — the request is too vague, ambiguous, or missing context"""
def understandtopic_node(state:State)->dict:
    message = state['user_msg']
    output = struc_model.invoke([
        SystemMessage(content=topic_msg),
        HumanMessage(content=message)
    ])

    return {'topic': output.topic,'knowledge_level': output.knowledge_level,'needs_classification': bool(output.needs_classification)}


# --------------------------------------- Router Function ----------------------------------------------
def router(state:State)->Literal['clarify_with_human','search_agent']:
    clearification = state['needs_classification']
    if clearification == True:
        return 'clarify_with_human'
    else:
        return 'search_agent'


# -------------------------------------------- Clarify with Human Node -----------------------------------
def clarify_with_human(state: State):
    decision = interrupt(
        {
            "question": f"Aap '{state['topic']}' kis level pe seekhna chahti hain?",
            "options": ["Beginner", "Intermediate", "Advanced"],
            "user_msg": state["user_msg"]
        }
    )
    # return {
    #    # "knowledge_level": decision 
    #    "knowledge_level": "advanced"  #  user ka answer yahan store hoga
    # }
    return {"user_msg": decision, "needs_classification": False}

# --------------------------------------------- Search Agent (Sub-Graph) -------------------------------------

# Subgraph state 
class sub_graph_state(TypedDict):
    user_msg:str
    topic: str
    knowledge_level: Literal["beginner" ,"intermediate","advanced"]
    response: str
    action: Literal['tool_node','llm_node']

# Decision Node Schema
class decisionschema(BaseModel):
    action: Literal['tool_node','llm_node']
    
# Structured LLM For Decision Making
struc_decision_model= model.with_structured_output(decisionschema,strict = True)

#  Desicion Node
def decision_node(state: sub_graph_state) -> dict:
    decision_msg = f"""
You are a decision agent.

User query: {state['user_msg']}
Topic: {state['topic']}
Knowledge Level: {state['knowledge_level']}

Decide:
- If external knowledge/API is needed, respond with action = "tool_node"
- If you can answer directly without external lookup, respond with action = "llm_node"

Return structured output only.
"""
    output = struc_decision_model.invoke(
        [SystemMessage(content = decision_msg),
         HumanMessage(content= "answer it.")]
    )
    print(output.action)
    return {**state,'action': output.action}

# SubGraph Router 
def sub_router(state: sub_graph_state) -> Literal['tool_node','llm_node']:
    return state['action']  

# ---------------------------------------------- Defining Tools ----------------------------------------------

# 1- Wikepedia
@tool
def wikepedia_search_node(topic: str) -> dict:
    """
    Fetch a short summary of a topic from Wikipedia.
    Use this when factual or definition-based information is needed.
    """
    encoded_topic = urllib.parse.quote(topic.strip().replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_topic}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("extract", "")
    except (requests.exceptions.RequestException, ValueError):
        return f"No Wikipedia summary found for topic: {topic}"

# 2- Tavily Search
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def tavily_search_tool(topic,depth)->dict:
    
    
    result = tavily_client.search(
        query=topic,
        search_depth=depth,
        max_results=1
    )
    return result

#  ------------------------------------- Making LLM tool aware ------------------------------------
tools = [wikepedia_search_node]
tool_llm= model.bind_tools(tools) 

# -------------------------------------------- Defining Tool Node -----------------------------------
def search_node(state: sub_graph_state) -> dict:
    topic = state['topic']
    knowledgeLevel = state['knowledge_level']
    if knowledgeLevel == "beginner":
        data = wikepedia_search_node.invoke({'topic': topic})
    else:
        depth = "advanced" if knowledgeLevel == "advanced" else "basic"
        data = tavily_search_tool(topic,depth)
    if not data:
        data = f"No search data found for topic: {topic}"

    
    response = model.invoke([
        SystemMessage(content="Explain clearly based on data"),
        HumanMessage(content=data)
    ])
    return {'response': response.content}

# ------------------------------------------ Defining LLM Search Node ---------------------------------
search_msg ="You are Student assistant. Explain the Given topic by user according to the required knowledge depth"
def llm_search(state: sub_graph_state) -> dict:
    topic = state['topic']
    knowledgedepth = state['knowledge_level']
    response = model.invoke([
        SystemMessage(content=search_msg),
        HumanMessage(content=f'topic-{topic}.... knowledgedepth - {knowledgedepth}')
    ])
    return {'response': response.content}

# ------------------------------------------ Creating Sub graph ------------------------------------
sub_graph = StateGraph(sub_graph_state)

## Adding Nodes
sub_graph.add_node('Decision Node',decision_node)
sub_graph.add_node('tool_node',search_node)
sub_graph.add_node('llm_node',llm_search)

## Adding Edges
sub_graph.add_edge(START,'Decision Node')
sub_graph.add_conditional_edges('Decision Node',sub_router)
sub_graph.add_edge('tool_node',END)
sub_graph.add_edge('llm_node',END)

sub_workflow = sub_graph.compile()

# ---------------------------------- Search Agent Node -----------------------------------------------
def search_agent(state:State):
    msg = state['user_msg']
    knowledge = state['knowledge_level']
    topic = state['topic']
    

    result = sub_workflow.invoke({'user_msg': msg,'topic': topic,'knowledge_level': knowledge})
    return({'llm_description': result['response']})

#  ---------------------------------------------Syntheize Node --------------------------------------------

synthesize_msg = """You are a world-class tutor inside an AI Study Buddy pipeline.

You will receive:
- A topic the student wants to learn
- Their knowledge level: beginner, intermediate, or advanced
- Raw search results about the topic

Your job is to synthesize this into a clean, engaging study note.

Adapt your explanation based on level:
- beginner: Simple language, no jargon, real-life analogies, short sentences
- intermediate: Assume basic knowledge, explain the "why", include code/formulas
- advanced: Go deep, cover edge cases, internals, tradeoffs, comparisons

Your response must follow this exact structure:

## Topic: <topic name>

### What is it?
<1-2 sentence simple definition>

### How it works
<core explanation — 3 to 5 sentences, adapted to level>

### Example
<one concrete example — code snippet, real-life analogy, or formula>

### Key points to remember
- <point 1>
- <point 2>
- <point 3>

### Common mistakes
- <mistake 1>
- <mistake 2>

Keep the total length appropriate:
- beginner: short and friendly (150-200 words)
- intermediate: medium with some depth (200-300 words)
- advanced: thorough and precise (300-400 words)

Do NOT include anything outside this structure. No greetings, no "sure!", no extra commentary.
"""
def synthesize(state:State) -> dict:
    topic = state['topic']
    level = state['knowledge_level']
    llm_result = state['llm_description']

    output = model.invoke([
        SystemMessage(content =synthesize_msg ),
        HumanMessage(content= f"""
Topic: {topic}
Student level: {level}
raw_data: {llm_result} """)
    ])

    return {"notes": output.content}

# ----------------------------- Schema of quiz generator Node -------------------------------
class QuizOption(BaseModel):
    A: str
    B: str
    C: str
    D: str

class QuizSchema(BaseModel):
    question: str
    options: QuizOption
    correct: Literal["A", "B", "C", "D"]
    explanation: str

class AnswerCheckSchema(BaseModel):
    is_correct: bool
    feedback: str

quiz_struc_model = model.with_structured_output(QuizSchema, strict=True)
answer_struc_model = model.with_structured_output(AnswerCheckSchema, strict=True)

# ------------------------------------- Quiz Generator Node -----------------------------------------
QUIZ_GENERATOR_PROMPT = """You are a quiz master inside an AI Study Buddy pipeline.

Given a study note on a topic, generate ONE multiple choice question to test the student.

The question must:
- Test actual understanding, not just memorization
- Have 4 options labeled A, B, C, D
- Have exactly one correct answer
- Match the student's level:
  - beginner: straightforward concept check
  - intermediate: application or "why" based
  - advanced: edge case, tradeoff, or internals based

Respond ONLY in this JSON format with no extra text:
{
  "question": "<the question>",
  "options": {
    "A": "<option A>",
    "B": "<option B>",
    "C": "<option C>",
    "D": "<option D>"
  },
  "correct": "A" | "B" | "C" | "D",
  "explanation": "<why this answer is correct, in 1-2 sentences>"
}
"""
ANSWER_CHECK_PROMPT = """You are an answer evaluator in an AI Study Buddy pipeline.

The student was asked a quiz question and gave an answer.
Evaluate if their answer is correct.

Be flexible — if they typed "A", "option A", or the actual text of option A, treat it as correct.
If their answer is completely wrong or unrelated, mark it incorrect.

Respond ONLY in this JSON format:
{
  "is_correct": true | false,
  "feedback": "<encouraging 1-2 sentence feedback explaining why correct or what they missed>"
}
"""









# def quiz_generator(state: State) -> dict:
#     if state.get("quiz") is None:
#         response = quiz_struc_model.invoke([
#             SystemMessage(content=QUIZ_GENERATOR_PROMPT),
#             HumanMessage(content=f'Topic: {state["topic"]}   Student level: {state["knowledge_level"]}    Study note:{state["notes"]}')
#         ])
#         return {
#             "quiz": response.model_dump(),  # convert Pydantic object -> dict
#             "attempts": 0,
#             "score": 0,
#         }
#     else:
#         user_answer = state["messages"][-1].content
#         quiz = state["quiz"]
#         result = answer_struc_model.invoke([
#             SystemMessage(content=ANSWER_CHECK_PROMPT),
#             HumanMessage(content=f'''Question: {quiz["question"]}
#                         Options: A: {quiz["options"]["A"]} B: {quiz["options"]["B"]} C: {quiz["options"]["C"]} D: {quiz["options"]["D"]}
#                         Correct answer: {quiz["correct"]}
#                         Student's answer: {user_answer}''')
#         ])
#         new_score = state["score"] + (1 if result.is_correct else 0)
#         new_attempts = state["attempts"] + 1
#         return {
#             "score": new_score,
#             "attempts": new_attempts,
#             "last_answer_correct": result.is_correct,
#             "last_feedback": result.feedback,
#         }

def quiz_generator(state: State) -> dict:
    response = quiz_struc_model.invoke([
        SystemMessage(content=QUIZ_GENERATOR_PROMPT),
        HumanMessage(content=f'Topic: {state["topic"]}  Level: {state["knowledge_level"]}  Notes: {state["notes"]}')
    ])
    return {
        "quiz": response.model_dump(),
        "attempts": 0,
        "score": 0,
    }

# ------------------------------------------ Answer Checker Node --------------------------------------
def answer_checker(state: State) -> dict:
    user_answer = state["messages"][-1].content
    quiz = state["quiz"]

    result = answer_struc_model.invoke([
        SystemMessage(content=ANSWER_CHECK_PROMPT),
        HumanMessage(content=f'''Question: {quiz["question"]}
Options: A: {quiz["options"]["A"]} B: {quiz["options"]["B"]} C: {quiz["options"]["C"]} D: {quiz["options"]["D"]}
Correct answer: {quiz["correct"]}
Student's answer: {user_answer}''')
    ])

    return {
        "score": 1 if result.is_correct else 0,
        "attempts": 1,
        "last_answer_correct": result.is_correct,
        "last_feedback": result.feedback,
    }

#  --------------------------------------------- Entry Router ---------------------------------------
# --------------------------------------- Entry Router ----------------------------------------------
def entry_router(state: State) -> Literal['Understand_topic', 'answer_checker']:
    # If a quiz already exists and the user just sent a new message,
    # treat this as an answer submission, not a fresh topic request.
    if state.get('quiz') and state.get('messages'):
        return 'answer_checker'
    return 'Understand_topic'

#  --------------------------------------------- Creating  Graph ---------------------------------------------
graph = StateGraph(State)

## Adding Nodes

graph.add_node('Understand_topic',understandtopic_node)
graph.add_node('clarify_with_human',clarify_with_human)
graph.add_node('search_agent',search_agent)
graph.add_node('synthesize',synthesize)
graph.add_node('quiz_generator',quiz_generator)
graph.add_node('answer_checker', answer_checker)

## Add Edges
graph.add_conditional_edges(START, entry_router)
# graph.add_edge(START,'Understand_topic')
graph.add_conditional_edges('Understand_topic',router)
graph.add_edge('clarify_with_human','search_agent')
graph.add_edge('search_agent','synthesize')
graph.add_edge('synthesize','quiz_generator')
graph.add_edge('quiz_generator',END)
graph.add_edge('answer_checker', END)

# Graph compilation
checkpointer = MemorySaver()
workflow = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["clarify_with_human"]  # HITL
)