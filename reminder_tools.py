import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "memory_db.sqlite")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_reminders_db():
    conn = get_db_connection()
    # Create reminders table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            frequency TEXT NOT NULL, -- 'hourly', 'daily', 'weekly', 'monthly'
            channel TEXT NOT NULL, -- 'email', 'voice', 'both'
            time_of_day TEXT, -- 'HH:MM' (24-hour format)
            day_of_week TEXT, -- 'Monday', 'Tuesday', etc.
            day_of_month INTEGER, -- 1-31
            tone_agent TEXT DEFAULT 'ExecutiveCoach', -- 'ExecutiveCoach', 'ChiefOfStaff'
            is_active INTEGER DEFAULT 1, -- 1 = active, 0 = inactive
            last_triggered TEXT, -- ISO 8601 timestamp
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create pending_voice_alerts table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pending_voice_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            audio_bytes BLOB NOT NULL,
            played INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize tables
init_reminders_db()

def create_reminder(
    text: str,
    frequency: str,
    channel: str,
    time_of_day: str = None,
    day_of_week: str = None,
    day_of_month: int = None,
    tone_agent: str = "ExecutiveCoach"
) -> str:
    """Create a scheduled reminder.
    
    Args:
        text (str): The reminder message or theme.
        frequency (str): The trigger frequency. One of: 'hourly', 'daily', 'weekly', 'monthly'.
        channel (str): How to alert. One of: 'email', 'voice', 'both'.
        time_of_day (str, optional): The time in 'HH:MM' 24-hour format (e.g. '09:00' or '14:30'). Required for daily, weekly, monthly.
        day_of_week (str, optional): Day of the week for weekly reminders (e.g. 'Monday', 'Friday').
        day_of_month (int, optional): Day of the month for monthly reminders (e.g. 1 to 31).
        tone_agent (str, optional): Which agent's personality/tone to use. Either 'ExecutiveCoach' or 'ChiefOfStaff'. Default is 'ExecutiveCoach'.
        
    Returns:
        str: Success or error message.
    """
    frequency = frequency.lower().strip()
    if frequency not in ['hourly', 'daily', 'weekly', 'monthly']:
        return "Error: frequency must be one of 'hourly', 'daily', 'weekly', 'monthly'."
        
    channel = channel.lower().strip()
    if channel not in ['email', 'voice', 'both']:
        return "Error: channel must be one of 'email', 'voice', 'both'."
        
    if frequency in ['daily', 'weekly', 'monthly'] and not time_of_day:
        return "Error: time_of_day (e.g. '09:00') is required for daily, weekly, and monthly reminders."
        
    if frequency == 'weekly' and not day_of_week:
        return "Error: day_of_week (e.g. 'Monday') is required for weekly reminders."
        
    if frequency == 'monthly' and not day_of_month:
        return "Error: day_of_month (1-31) is required for monthly reminders."
        
    try:
        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO reminders 
               (text, frequency, channel, time_of_day, day_of_week, day_of_month, tone_agent, is_active) 
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)''',
            (text, frequency, channel, time_of_day, day_of_week, day_of_month, tone_agent)
        )
        conn.commit()
        conn.close()
        return f"Successfully created a new {frequency} reminder: '{text}' via {channel}."
    except Exception as e:
        return f"Error creating reminder: {e}"

def list_reminders() -> str:
    """List all scheduled reminders in the system.
    
    Returns:
        str: A formatted Markdown table of all reminders.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, frequency, channel, time_of_day, day_of_week, day_of_month, tone_agent, is_active FROM reminders")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No reminders have been set yet."
            
        md = ["| ID | Active | Message | Frequency | Channel | Details | Agent Tone |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for row in rows:
            active_str = "✅ Yes" if row['is_active'] == 1 else "❌ No"
            details = []
            if row['time_of_day']:
                details.append(f"at {row['time_of_day']}")
            if row['day_of_week']:
                details.append(f"on {row['day_of_week']}")
            if row['day_of_month']:
                details.append(f"on day {row['day_of_month']}")
            details_str = " ".join(details) if details else "N/A"
            
            md.append(f"| {row['id']} | {active_str} | {row['text']} | {row['frequency']} | {row['channel']} | {details_str} | {row['tone_agent']} |")
            
        return "\n".join(md)
    except Exception as e:
        return f"Error listing reminders: {e}"

def delete_reminder(reminder_id: int) -> str:
    """Delete a reminder by its ID.
    
    Args:
        reminder_id (int): The ID of the reminder to delete.
        
    Returns:
        str: Success or error message.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM reminders WHERE id = ?", (reminder_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return f"Error: No reminder found with ID {reminder_id}."
            
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
        return f"Successfully deleted reminder {reminder_id}: '{row['text']}'"
    except Exception as e:
        return f"Error deleting reminder: {e}"

def toggle_reminder(reminder_id: int, active: bool) -> str:
    """Toggle a reminder's active status.
    
    Args:
        reminder_id (int): The ID of the reminder to toggle.
        active (bool): True to activate, False to pause.
        
    Returns:
        str: Success or error message.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM reminders WHERE id = ?", (reminder_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return f"Error: No reminder found with ID {reminder_id}."
            
        status_val = 1 if active else 0
        cursor.execute("UPDATE reminders SET is_active = ? WHERE id = ?", (status_val, reminder_id))
        conn.commit()
        conn.close()
        status_word = "activated" if active else "paused"
        return f"Successfully {status_word} reminder {reminder_id}: '{row['text']}'"
    except Exception as e:
        return f"Error toggling reminder: {e}"

def insert_pending_voice_alert(text: str, audio_bytes: bytes):
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO pending_voice_alerts (text, audio_bytes, played) VALUES (?, ?, ?)",
            (text, audio_bytes, 0)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error inserting pending voice alert: {e}")

def get_pending_voice_alert():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, audio_bytes FROM pending_voice_alerts WHERE played = 0 ORDER BY id ASC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row['id'], row['text'], row['audio_bytes']
        return None
    except Exception as e:
        print(f"Error fetching pending voice alert: {e}")
        return None

def mark_voice_alert_played(alert_id: int):
    try:
        conn = get_db_connection()
        conn.execute("UPDATE pending_voice_alerts SET played = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error marking voice alert played: {e}")
