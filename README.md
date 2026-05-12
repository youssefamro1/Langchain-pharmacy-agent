# 💊 LangChain Pharmacy AI Agent

An advanced, context-aware AI assistant designed for pharmacy management. This project leverages **LangChain** and **LangGraph** to create a ReAct Agent that can intelligently chat with users and query a SQL database for real-time pharmaceutical data.

---

## 🚀 Overview
This is not just a simple chatbot. It is an **AI Agentic System** that understands intent. It can distinguish between a casual greeting and a complex data inquiry (like stock levels, sales reports, or order details).

### 🧠 Key Features
* **ReAct Agent Pattern:** Decides whether to use the database tool or reply directly based on reasoning.
* **LangGraph Orchestration:** Manages the complex state and flow of the conversation.
* **SQL Integration:** Automated SQL query generation to fetch real-time data from the pharmacy schema.
* **Per-User Memory:** Maintains conversation history for each user to allow contextual follow-up questions.
* **Secure by Design:** Built with read-only database permissions to prevent unauthorized data modification.

---

## 🛠️ Tech Stack
* **Framework:** LangChain & LangGraph
* **LLM:** GPT-4o-Turbo (via OpenRouter)
* **Interface:** Telegram Bot API
* **Database:** SQL (PostgreSQL/MySQL)

---

## 🔄 Workflow
1.  **User Input:** Natural language received via Telegram.
2.  **Reasoning (LLM):** The agent analyzes the intent using a specialized `System Prompt`.
3.  **Action:** If data is needed, the `SQL Agent Tool` generates a precise query.
4.  **Output:** The result is formatted into a clean Markdown table and sent to the user.

---

## 🛡️ Security Note
The SQL agent is restricted to `SELECT` operations only. It cannot perform `DELETE`, `DROP`, or `UPDATE` commands, ensuring the safety of the pharmacy's data.