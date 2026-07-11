# 📚 AI Study Buddy

**Learn any topic — with explanation and a quiz!**

AI Study Buddy is an agentic learning assistant built with **LangGraph**, **LangChain**, **Groq (Llama 3.3 70B)**, and **Streamlit**. Tell it any topic you want to study, and it will:

1. Understand what you want to learn and at what level
2. Ask for clarification if your request is ambiguous (Human-in-the-Loop)
3. Research the topic using Wikipedia or Tavily web search
4. Synthesize a clean, structured study note tailored to your knowledge level
5. Generate a multiple-choice quiz to test your understanding
6. Check your answer and give instant feedback

---

## ✨ Features

- **Adaptive explanations** — beginner, intermediate, or advanced, based on how you phrase your question
- **Human-in-the-loop clarification** — if the topic is too vague, the app pauses and asks you to clarify before continuing
- **Smart research routing** — beginners get quick Wikipedia summaries, intermediate/advanced learners get deeper Tavily web search
- **Structured study notes** — every explanation follows a consistent format: definition, how it works, example, key points, and common mistakes
- **Auto-generated quiz** — one MCQ per topic, matched to your level (concept check, application, or edge-case/tradeoff questions)
- **Answer evaluation** — flexible checking (accepts "A", "Option A", or the actual answer text) with encouraging feedback

---

## 🧠 How It Works (Architecture)

The app is powered by a **LangGraph** state machine with a nested sub-graph for research:

```
START
  │
  ▼
Understand Topic ──(needs clarification?)──► Clarify with Human ──┐
  │ (topic is clear)                                              │
  ▼                                                                │
Search Agent  ◄─────────────────────────────────────────────────┘
  │  (sub-graph: decides Wikipedia/Tavily lookup vs. direct LLM answer)
  ▼
Synthesize (structured study note)
  │
  ▼
Quiz Generator
  │
  ▼
 END

(separately, on answer submission)
Answer Checker ──► END
```

### Main Graph Nodes
| Node | Responsibility |
|---|---|
| `Understand_topic` | Extracts topic, knowledge level, and whether clarification is needed |
| `clarify_with_human` | Pauses execution (`interrupt`) and asks the user to clarify an ambiguous topic |
| `search_agent` | Runs a research sub-graph to gather information on the topic |
| `synthesize` | Turns raw research into a structured, level-appropriate study note |
| `quiz_generator` | Creates one multiple-choice question based on the study note |
| `answer_checker` | Evaluates the user's submitted answer and returns feedback + score |

### Search Sub-Graph
A nested graph decides *how* to research a topic:
- **Decision Node** — decides whether external lookup is needed (`tool_node`) or the LLM can answer directly (`llm_node`)
- **`tool_node`** — beginners → Wikipedia summary; intermediate/advanced → Tavily search
- **`llm_node`** — direct LLM explanation, no external lookup

---

## 🛠️ Tech Stack

- **[LangGraph](https://langchain-ai.github.io/langgraph/)** — orchestration, state management, human-in-the-loop interrupts
- **[LangChain](https://www.langchain.com/)** — LLM/tool abstractions, structured output
- **[Groq](https://groq.com/)** — LLM inference (`llama-3.3-70b-versatile`)
- **[Tavily](https://tavily.com/)** — web search API
- **Wikipedia REST API** — quick factual summaries
- **[Streamlit](https://streamlit.io/)** — web UI
- **Pydantic** — structured output schemas

---

## 📂 Project Structure

```
AI-Study-Buddy/
├── app.py           # Streamlit front-end (UI + session/state management)
├── graph.py         # LangGraph pipeline: nodes, sub-graph, tools, routers
├── state.py         # Shared State schema (TypedDict) used across the graph
├── .env             # API keys (not committed)
└── requirements.txt # Python dependencies
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd AI-Study-Buddy
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` yet, install manually:
```bash
pip install streamlit langgraph langchain langchain-groq langchain-core tavily-python python-dotenv pydantic requests
```

### 4. Set up environment variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 5. Run the app
```bash
streamlit run app.py
```

---

## 🚀 Usage

1. Enter a topic you want to study (e.g. *"Python decorators"*, *"Newton's laws"*, *"LangGraph nodes"*).
2. If the topic is ambiguous, you'll be asked to clarify it.
3. Read the generated study note (definition, explanation, example, key points, common mistakes).
4. Click **Take Quiz!** to test yourself with an auto-generated MCQ.
5. Submit your answer and get instant feedback with your score.
6. Start a new topic anytime, or revisit your notes.

---

## ⚠️ Known Limitations

- Only one quiz question is generated per topic session (no multi-question quiz loop yet).
- The knowledge base is limited to Wikipedia summaries and single-result Tavily searches.
- Answer checking relies on the LLM's judgment and may occasionally misjudge borderline answers.
- Currently uses in-memory checkpointing (`MemorySaver`), so state is lost when the app restarts.

---

## 🗺️ Possible Improvements

- Support multi-question quizzes with a running score across attempts
- Persist checkpoints (e.g., SQLite/Postgres) instead of in-memory storage
- Add source citations to study notes
- Support file/PDF-based topic input
- Add difficulty progression across sessions

---

## 📄 License

This project is open for personal and educational use. Add your preferred license (MIT, Apache 2.0, etc.) here.
