# 🤖 MongoChat AI Platform

**MongoChat** is an intelligent, conversational interface for your MongoDB database. It allows you to chat with your data using natural language, powered by advanced RAG (Retrieval-Augmented Generation) and Large Language Models (LLMs).

Forget writing complex aggregation pipelines manually—just ask, and MongoChat understands the structure of your data and helps you retrieve it.

---
Dashboard
<img width="955" height="443" alt="image" src="https://github.com/user-attachments/assets/e819a772-319e-4ddf-977d-579c5991a55f" />
Chat Agent
<img width="1920" height="891" alt="image" src="https://github.com/user-attachments/assets/0a89c0ec-5aa5-48d9-9e74-af5bc32f4303" />

Convertion - Chat
<img width="1920" height="899" alt="image" src="https://github.com/user-attachments/assets/32f986e6-9aa0-481a-9b79-c7dcd07b85ae" />
<img width="1920" height="890" alt="image" src="https://github.com/user-attachments/assets/0667f9cd-be5a-44e4-8e38-bfee4b73969c" />
<img width="1920" height="889" alt="image" src="https://github.com/user-attachments/assets/89d4e5e0-b0b1-4d49-8970-2c6da45913dc" />


## 🚀 Key Features

*   **⚡ Agentic Data Retrieval:** The AI simply doesn't just "talk"—it **ACTS**. If you ask "Count the users", it securely executes the query and gives you the real number.
*   **🧑‍💻 Smart Code Generation:** If you ask "How do I write a query?", it switches modes to teach you, providing clean, copy-pasteable code without internal tool jargon.
*   **🗣️ Natural Language Chat:** Ask complex questions in plain English.
*   **🔌 Secure Connection:** Connect to any MongoDB cluster (Atlas or local) securely. Credentials are ephemeral and stored only in your session.
*   **🧠 RAG Engine:** The system scans your database schema, indexes it, and uses this knowledge to give accurate answers.
*   **📝 Comprehensive Logging:**
    *   **Application Logs:** Detailed system events in `logs/mongo_chat.log`.
    *   **Audit History:** Tracks who asked what, including **System IPv4** (LAN IP) logging for local users.
*   **⏱️ Real-Time UX:** AJAX-based chat, auto-scrolling, and per-message **timestamps**.

---

## 📂 Project Structure

Here is a map of the files in this project:

```text
mongo_chat_platform/            # 📁 ROOT DIRECTORY
│
├── manage.py                   # ⚙️ Django's command-line utility
├── run.sh / run.bat            # 🚀 Scripts to start the server (Auto-cleans caches)
├── requirements.txt            # 📦 List of python libraries required
├── README.md                   # 📖 This documentation file
├── .env                        # 🔐 Secrets (API Keys) - Create this yourself!
│
├── mongo_chat_platform/        # 🧠 CORE CONFIGURATION & SERVICES
│   ├── settings.py             # Global settings (Installed apps, Middleware)
│   ├── logger.py               # Central logging setup (Console + File)
│   └── services/               # The "Brain" of the application
│       ├── mongo_service.py    # Connects to your MongoDB to execute queries (Agentic)
│       ├── chroma_service.py   # Vector DB (RAG) to remember your schema
│       ├── llm_service.py      # Talks to Groq AI (Llama 3)
│       └── logging_service.py  # Saves chat history to a database
│
├── connect/                    # 🔌 APP: CONNECTION SCREEN
│   ├── views.py                # Handles login/logout logic (AJAX enabled)
│   └── templates/connect/      # HTML for the Connection Form
│
├── chat/                       # 💬 APP: CHAT INTERFACE
│   ├── views.py                # Handles messaging, tool execution loop & logging
│   └── templates/chat/         # HTML for the Chat Interface (Timestamps enabled)
│
├── templates/                  # 🎨 SHARED TEMPLATES
│   └── base.html               # Main layout file (includes Tailwind CSS)
│
├── logs/                       # 📝 LOG FILES
│   └── mongo_chat.log          # Detailed application logs appear here
│
└── .husky/                     # 🛡️ GIT HOOKS
    └── pre-commit              # Script that blocks you from committing .env
```

---

## ⚙️ Setup Guide

### Prerequisites
*   **Python 3.10+** (Ensure it is added to your PATH)
*   **MongoDB Database** (Local or Atlas Connection String)
*   **Groq API Key** (Free beta keys available at [console.groq.com](https://console.groq.com))

### 1. Installation

Clone the repository and navigate to the folder:

```bash
git clone https://github.com/yourusername/mongo-chat-platform.git
cd mongo-chat-platform
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the `mongo_chat_platform` folder (next to `settings.py`) with the following keys:

```ini
# Security
SECRET_KEY=your_django_secret_key
DEBUG=True

# LLM Provider
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Logging (Optional: Where to store chat logs)
MONGO_LOGS_URI=mongodb://localhost:27017/chat_logs

# ChromaDB (Optional: For cloud vector storage)
# CHROMA_API_KEY=...
```

### 3. Running the App

Run the database migrations and start the server:

**Windows:**
Double-click `run.bat` or run:
```powershell
.\run.bat
```

**Linux/Mac:**
```bash
./run.sh
```

Visit **`http://127.0.0.1:8000`** in your browser.

---

## 📖 How to Use

1.  **Connect:** Enter your MongoDB Connection String (e.g., `mongodb+srv://user:pass@cluster...`) on the home screen.
2.  **Wait:** On the very first run, the system will download a small AI embedding model. This takes about 1-2 minutes.
3.  **Chat:** Once connected, you'll be taken to the chat interface.

### Agentic Capabilities (New!)
*   **Ask for Data:** "How many users are active?"
    *   *The AI performs a live count in the DB and answers: "There are 150 active users."*
*   **Ask for Code:** "Show me the query to find active users."
    *   *The AI switches mode and gives you the clean code block: `db.users.find({...})`.*

---

## 🛡️ Security & Contribution

*   **Credential Safety**: We never store your MongoDB URI in a persistent database. It lives only in your temporary session.
*   **Git Protection**: A `husky` pre-commit hook is installed to prevent you from accidentally committing your `.env` file.
*   **Logging**: All interactions are logged with timestamps and **System IP** (even for localhost users) to ensure accountability.

Feel free to fork this project and submit Pull Requests!
