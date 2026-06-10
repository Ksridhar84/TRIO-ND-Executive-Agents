# 🧠 ND TRIO Executive OS
**Google Cloud Rapid Agent Hackathon Submission**

An autonomous, multi-agent "Executive Command Center" designed specifically for Neurodivergent (ND) professionals. The system acts as a judgment-free, deeply integrated support network to manage tasks, code, schedule, and cognitive wellness through coordinated AI sub-agents.

## 🎯 The Vision
Neurodivergent individuals (ADHD, Autism, Dyslexia) often struggle with Executive Dysfunction—the inability to initiate tasks, manage time, or regulate focus. Traditional productivity apps rely on the user to manually organize data, which causes cognitive overload.

**ND TRIO** flips the paradigm. Instead of *you* managing the app, the **Agents manage your life**, breaking down complex tasks, monitoring your energy levels, and autonomously executing actions across your digital workspace.

---

## 🏗️ System Architecture & Multi-Agent Design

The system is built on the **Google ADK (Agent Development Kit)** and utilizes a hierarchical agent topology:

1. **The Chief of Staff (CoS)** *[The Orchestrator]*
   - **Role**: The only agent that speaks directly to the user.
   - **Capabilities**: Translates raw data into low-clutter, highly scannable Markdown. Possesses long-term memory to learn the user's quirks and preferences. Delegates specialized tasks to sub-agents.
   
2. **The Executive Assistant (EA)** *[The Executor]*
   - **Role**: Tactical operations and deep-work management.
   - **Capabilities**: Connects to external APIs to draft emails, read calendars, manage Notion project wikis, and interact with GitLab repositories.

3. **The Executive Coach** *[The Regulator]*
   - **Role**: Emotional and cognitive wellness monitor.
   - **Capabilities**: Steps in during "Daily Check-Ins" to assess burnout, energy, and focus levels. Provides neuro-inclusive interventions (e.g., body-doubling, forced breaks, Lofi music).

---

## 🔌 API Connections & Integrations

The agents are granted real-world agency through a massive suite of secure API integrations:

*   **Google Workspace API (OAuth 2.0)**
    *   **Gmail**: Reads inbox, flags urgent items, and sends outbound emails.
    *   **Calendar**: Reads upcoming events and schedules new blocks.
    *   **Docs/Slides**: Extracts text and context from Google Drive.
*   **GitLab API (via Model Context Protocol - MCP)**
    *   Securely accesses the user's repositories, reads code, and tracks issues.
*   **Notion API**
    *   Acts as the system's "Second Brain". The EA can search, read, and write project documentation, meeting notes, and handle "Partner Delegated Tasks" (e.g., household chores).
*   **Spotify Integration**
    *   Dynamically recommends and embeds curated playlists (Lofi, Brown Noise, High Energy) into the dashboard based on the user's real-time cognitive energy levels.
*   **Local SQLite Vector Database**
    *   Provides persistent, long-term memory (`sqlite-vec`) across chat sessions.

---

## 🧰 Tools & Agent Capabilities
Here is a complete list of the tools the agents can use to execute tasks for you:

*   **Communication Tools:** `send_email`, `read_gmail_inbox`
*   **Scheduling Tools:** `get_calendar_events`, `create_calendar_event`, `get_current_datetime`
*   **Knowledge & Docs:** `read_google_doc`, `read_google_sheet`, `read_google_slide`, `create_google_doc`, `search_notion`, `read_notion_page`, `create_notion_page`
*   **Software Engineering:** `read_gitlab_issue`, `create_issue`, `list_commits` (via MCP)
*   **Cognitive Support:** `recommend_spotify_playlist`, `get_wellness_break_recommendation`, `get_cheery_inspiration`, `analyze_decision_matrix`
*   **Cognitive Offloading:** `breakdown_complex_task`
*   **Persistent Memory:** `store_memory`, `search_memory`

---

## 🆕 Features Added During Hackathon
*   **Notion Integration**: "Second Brain" project wikis and the "Household Quests" shared partner-task page.
*   **Spotify Wellness**: Real-time iframe embedding of Lofi/Brown Noise playlists based on the user's energy check-in.
*   **Voice & Multimodal Inputs**: Audio memo recordings and image uploads directly passed to Gemini.
*   **Chat Archiving**: File-based long-term memory to save, retrieve, and scroll through past chat sessions.
*   **Background Autonomous Schedulers**: Python scripts that run independently to deliver morning briefings.
*   **Glassmorphism UI**: A sleek, ADHD-friendly, low-sensory frontend dashboard.

---

## ✨ Core Workflows & Functionalities

### 1. The "Daily Check-In" Energy Workflow
Users submit their current "Energy" and "Focus" levels (1-10) via the sidebar. The **Coach** evaluates the scores (e.g., identifying "Emergency Low Power Mode") and the **Chief of Staff** embeds an auto-playing Spotify widget into the dashboard with a tailored soundscape (e.g., Brown Noise for focus, Lofi for sensory regulation).

### 2. Multi-Modal Hub
Users don't have to type. They can record **Voice Memos** or upload **Handwritten Notes/Images**. The system processes the audio/images using Gemini multimodal capabilities and feeds the exact text/intent to the agents.

### 3. The "Partner Hotline" (Body Doubling)
To support ADHD household management, the user's partner has access to a shared Notion page called "Household Quests." When the user asks the dashboard "What do I need to do today?", the EA silently scrapes that Notion page and integrates the partner's requested chores into the executive summary.

### 4. Background Morning Briefings
A dedicated `scheduler.py` background process runs on the host machine. Every morning at 8:30 AM, it autonomously wakes up the EA, scans the user's unread emails and daily calendar, generates a prioritized "Morning Briefing," and emails it directly to the user before they even open the dashboard.

### 5. Chat History Archiving
The Streamlit dashboard includes a persistent file-system memory. Users can instantly clear the screen for a new session or load previous chat logs from the sidebar dropdown, eliminating the anxiety of losing context.

---

## 🛠️ Tech Stack
*   **LLM Framework**: Google ADK (Agent Development Kit), Google Gemini API
*   **Frontend**: Streamlit (with custom Glassmorphism CSS & persistent Session State)
*   **Tooling Protocols**: MCP (Model Context Protocol) for GitLab
*   **Memory**: SQLite with Vector Extensions (`sqlite-vec`)
*   **Integrations**: Notion Client, Google API Python Client

---

## 🚀 Setup & Installation

1. **Clone & Install**
   ```bash
   git clone https://github.com/Ksridhar84/TRIO-ND-Executive-Agents.git
   cd TRIO-ND-Executive-Agents
   pip install -r requirements.txt
   ```
2. **Environment Variables**
   Create a `.env` file:
   ```env
   GEMINI_API_KEY=your_key
   GITLAB_TOKEN=your_token
   GITLAB_PROJECT_ID=your_id
   NOTION_API_TOKEN=your_token
   ```
3. **Google Auth**
   Place your `credentials.json` in the root folder.
4. **Run the Dashboard**
   ```bash
   streamlit run dashboard.py
   ```
