
# 🧱 Architecture & Usage Guide

## 📌 Objective

This framework automates the software development lifecycle using a Multi-Agent architecture. Each agent, powered by GPT-4 via AutoGen, performs a specialized role in transforming natural language requirements into production-ready software.

---

## 🧠 Agentic Workflow Diagram

```
User Input (Natural Language)
         ↓
Requirement Analysis Agent
         ↓
     Coding Agent
         ↓
   ↳ Code Review Agent (loop until Approved)
         ↓
Documentation Agent → Test Agent → Deployment Agent → UI Agent
```

Each agent passes its output to the next stage, forming a pipeline managed in `main.py`.

---

## 🧩 Agent Descriptions

### 1. **RequirementAgent**
- Parses user input (free text) into structured format (dictionary with goal, features, inputs, outputs).

### 2. **CodingAgent**
- Converts structured requirements into executable Python code.
- Supports iterative feedback from CodeReviewAgent.

### 3. **CodeReviewAgent**
- Evaluates code for correctness, security, efficiency.
- Returns `"Approved"` or feedback for rework.

### 4. **DocumentationAgent**
- Generates human-readable documentation in Markdown format.

### 5. **TestAgent**
- Produces `pytest`-based test cases (unit & integration).

### 6. **DeploymentAgent**
- Creates a shell script to:
  - Setup a virtualenv
  - Install dependencies
  - Run the app

### 7. **UIAgent**
- Builds a Streamlit-based frontend to collect input and show outputs.

---

## 🛠 How to Use

### ➤ Development

```bash
# Create environment
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the agent pipeline
python main.py
```

### ➤ Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

---

## 📂 Folder Overview

```
main.py                 → Orchestrates agent collaboration
src/agents/             → Source code for each agent
ui/                     → Streamlit frontend
scripts/deploy.sh       → Auto-generated deployment script
docs/architecture.md    → This document
```

---

## ⚠️ Notes

- Requires an OpenAI API key (`OPENAI_API_KEY`) for all agent operations.
- Placeholder responses are used in the Streamlit app unless integrated with real backend logic.
- Do not execute unknown code directly without review.

---

## 🧩 Extension Ideas

- Add FastAPI backend to serve agent results via HTTP.
- Persist history of interactions.
- Add real-time feedback display in UI.
