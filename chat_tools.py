import os
import json
import glob
from datetime import datetime

CHAT_DIR = "chat_history"

def ensure_chat_dir():
    if not os.path.exists(CHAT_DIR):
        os.makedirs(CHAT_DIR)

def save_chat_history(session_id: str, messages: list):
    """Saves the chat messages to a JSON file."""
    ensure_chat_dir()
    file_path = os.path.join(CHAT_DIR, f"{session_id}.json")
    
    # Filter out binary data like audio_bytes or file_bytes to save space
    clean_messages = []
    for msg in messages:
        clean_msg = {"role": msg["role"], "content": msg["content"], "avatar": msg.get("avatar")}
        if msg.get("has_file"):
            clean_msg["has_file"] = True
        clean_messages.append(clean_msg)
        
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(clean_messages, f, indent=4)

def load_chat_history(session_id: str) -> list:
    """Loads chat messages from a JSON file."""
    file_path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def list_chat_histories() -> list:
    """Returns a list of tuples (session_id, display_name) sorted by newest first."""
    ensure_chat_dir()
    files = glob.glob(os.path.join(CHAT_DIR, "*.json"))
    sessions = []
    for file_path in files:
        filename = os.path.basename(file_path)
        session_id = filename.replace(".json", "")
        # Get file modification time for display
        mtime = os.path.getmtime(file_path)
        dt = datetime.fromtimestamp(mtime)
        display_name = dt.strftime("%b %d, %Y - %I:%M %p")
        sessions.append((session_id, display_name, mtime))
        
    # Sort by mtime descending
    sessions.sort(key=lambda x: x[2], reverse=True)
    return [(s[0], s[1]) for s in sessions]
