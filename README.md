<div align="center">
  <h1>🌍 SupplySense: Autonomous Supply Chain Intelligence</h1>
  <p><i>Turning reactive supply chains into proactive, self-healing networks using Agentic AI.</i></p>
</div>

---

## 🚀 The Vision
Modern supply chains are incredibly fragile. When a supplier delays a shipment, or demand suddenly spikes, operations teams usually find out *after* the damage is done. 

**SupplySense** solves this by introducing a **Multi-Agent AI System** that constantly monitors supply chain data, predicts downstream impacts of delays, identifies high-risk suppliers, and autonomously proposes actionable solutions before critical stockouts occur.

---

## 🧠 Our Agentic AI Architecture
This project heavily relies on **Agentic AI**—not just simple chatbots, but autonomous agents that reason, plan, use tools, and critique their own work. We implemented a **multi-agent workflow** to ensure robust decision-making:

1. 🧭 **The Planner Agent:** Interprets complex, ambiguous human queries (e.g., *"What is causing today's biggest disruption?"*), breaks them down into logical steps, and selects the right backend tools.
2. ⚙️ **The Orchestrator Agent:** Executes the plan by dynamically calling Python tools, querying the SQLite database for live logistics data, and injecting context.
3. 🧐 **The Critic Agent:** Evaluates the Orchestrator's findings against strict business rules (e.g., checking if stock will drop below 3x weekly demand). If the output is flawed, the Critic forces a retry.
4. 🛠️ **The Action Agent:** When a vulnerability is found (like a failing supplier), this agent autonomously calculates the next best step—such as recommending an alternate supplier based on risk scores and geographical proximity.
5. 🤖 **The Autonomous Sweep:** A background system that periodically scans the entire database for anomalies (delays, demand spikes) and automatically generates "Pending Actions" for human approval on the dashboard.

---

## ✨ Key Features
* 💬 **Natural Language Logistics:** Ask complex questions about your supply chain in plain English.
* ⚠️ **Delay Impact Prediction:** Automatically calculates how a late shipment will affect warehouse utilization and downstream customer orders.
* 🏭 **Dynamic Supplier Risk Scoring:** Ranks suppliers based on on-time delivery percentages and quality scores, flagging high-risk vendors automatically.
* 🔄 **Alternate Source Recommendation:** If a supplier is failing, the AI instantly recommends a fallback supplier with a better risk profile.
* 📊 **Live Operations Dashboard:** A React-based command center displaying real-time warehouse utilization, demand forecasts, and pending AI actions.

---

## 🛠️ Tech Stack
* **Frontend:** React, Vite, Tailwind CSS (Modern, responsive UI)
* **Backend:** Python, Flask (Robust API and agent orchestration)
* **AI / LLMs:** Groq / Llama 3 (for ultra-fast agent reasoning)
* **Database:** SQLite (Relational logistics data)

---

## ⚙️ How to Run Locally (For Judges)

### 1. Environment Setup
Clone the repository and set up your API keys:
```bash
git clone https://github.com/punitmanojbhatarkar/Agentic-AI-Hackthon.git
cd Agentic-AI-Hackthon

# Create your .env file
cp .env.example .env
```
*Open the `.env` file and add your `GROQ_API_KEY`.*

### 2. Start the Backend (Python / Flask)
Open a terminal in the root directory:
```bash
# Create and activate a virtual environment
python -m venv env
env\Scripts\activate  # On Windows

# Install requirements
pip install -r requirements.txt

# Start the Flask API
python backend/api.py
```
*The backend will run on `http://localhost:5000`*

### 3. Start the Frontend (React / Vite)
Open a **new** terminal in the root directory:
```bash
cd frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```
*The frontend will run on `http://localhost:5173`. Open this in your browser!*

---

## 🔮 Future Scope
* **N8N Integration:** Fully autonomous workflows to automatically email alternate suppliers and reroute shipments without human intervention.
* **IoT Sensor Integration:** Feeding live GPS and temperature data of shipments directly into the Agent's context window.
* **ERP Sync:** Two-way sync with SAP or Oracle NetSuite.

---
<div align="center">
  <i>Built with ❤️ for the AI Agent Hackathon</i>
</div>
