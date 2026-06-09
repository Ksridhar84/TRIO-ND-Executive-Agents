# 🧠 ND TRIO Executive OS

An autonomous, multi-agent Executive Command Center designed specifically for Neurodivergent (ND) individuals. It provides a seamless, judgment-free interface to manage tasks, schedules, and communications through coordinated AI sub-agents.

## ✨ Features
- **Chief of Staff Agent:** Your primary supervisor that orchestrates the other agents and delegates tasks.
- **Executive Assistant Agent:** Handles tedious operational tasks, emails, scheduling, and document processing.
- **Executive Coach Agent:** Provides burnout prevention, emotional regulation check-ins, and strategic advice.
- **Multi-Modal Hub:** Speak to your agents via voice memos, upload handwritten notes, or chat via text.
- **Persistent Memory & Time Awareness:** The agents remember your past conversations and are fully aware of the current date and time to accurately manage your schedule.
- **Glassmorphism UI:** A sleek, low-sensory, pastel-gradient UI designed to reduce cognitive load and sensory fatigue.

## 🚀 Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ND-TRIO-Executive-OS.git
   cd ND-TRIO-Executive-OS
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   ```

4. **Google Workspace Auth**
   To enable the agent to read your calendar and send emails, you must obtain a `credentials.json` file from Google Cloud Console (OAuth 2.0 Client IDs for Desktop App) and place it in the root folder. Upon first run, the app will ask you to log in and generate a `token.json` file.

5. **Run the Dashboard**
   ```bash
   streamlit run dashboard.py
   ```

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
