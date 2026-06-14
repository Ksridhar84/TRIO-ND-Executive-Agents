import schedule
import time
import asyncio
import os
import json
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types
from datetime import datetime
from agents import chief_of_staff
from workspace_tools import read_gmail_inbox, send_email
from reminder_tools import get_db_connection, insert_pending_voice_alert

load_dotenv()
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")

async def run_agent_prompt(prompt: str) -> str:
    runner = InMemoryRunner(agent=chief_of_staff)
    runner.auto_create_session = True
    session_id = f"background_prompt_{int(time.time())}"
    message = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    full_output = []
    try:
        async for event in runner.run_async(user_id="background_scheduler", session_id=session_id, new_message=message):
            if event.author and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        full_output.append(part.text)
    except Exception as e:
        print(f"Error running agent prompt: {e}")
    return "".join(full_output)

async def generate_email_message(text: str, tone_agent: str) -> str:
    try:
        agent_tag = "@coach" if tone_agent == "ExecutiveCoach" else "@cos"
        prompt = f"{agent_tag} The user set a reminder: '{text}'. Please write a short, warm, encouraging, and casual message to gently remind the user of this, reminding them to stay present and not get lost in a rabbit hole. Keep it under 3-4 sentences. Do not use markdown tags, formatting, or bullet points."
        response = await run_agent_prompt(prompt)
        if response.strip():
            return response.strip()
    except Exception as e:
        print(f"Warning: Failed to generate email message with agent: {e}")
    return f"Hey there! Just a gentle reminder to '{text}'. Take a deep breath, come back to the present moment, and step out of the rabbit hole for a second. You're doing great! - Your {tone_agent}"

async def generate_voice_message(text: str, tone_agent: str) -> str:
    try:
        agent_tag = "@coach" if tone_agent == "ExecutiveCoach" else "@cos"
        prompt = f"{agent_tag} The user set a reminder: '{text}'. Please write a very short (1-2 sentences max), highly encouraging, soft, and casual voice message to gently bring them back to the present moment and step out of their rabbit hole. Talk to them directly, and keep it warm and friendly. Do not use any markdown formatting or bullet points."
        response = await run_agent_prompt(prompt)
        if response.strip():
            clean_text = response.replace("*", "").replace("#", "").replace('"', '').strip()
            return clean_text
    except Exception as e:
        print(f"Warning: Failed to generate voice message with agent: {e}")
    return f"Hey there! Just a gentle check-in to help you stay present. Remember your reminder: '{text}'. Take a breath and stretch."

async def trigger_reminder(text: str, channel: str, tone_agent: str):
    from voice_tools import generate_agent_voice
    
    # 1. Email Channel
    if channel in ['email', 'both']:
        email_body = await generate_email_message(text, tone_agent)
        subject = f"🌟 Gentle check-in from your Coach" if tone_agent == "ExecutiveCoach" else f"👔 Gentle check-in from your Chief of Staff"
        print(f"Sending reminder email: '{subject}'...")
        try:
            send_email(to_email='me', subject=subject, body=email_body)
        except Exception as e:
            print(f"Failed to send reminder email: {e}")
            
    # 2. Voice Channel
    if channel in ['voice', 'both']:
        voice_text = await generate_voice_message(text, tone_agent)
        print(f"Generating voice alert: '{voice_text}'...")
        try:
            audio_bytes = generate_agent_voice(voice_text)
            insert_pending_voice_alert(voice_text, audio_bytes)
        except Exception as e:
            print(f"Error generating or saving voice bytes for reminder: {e}")

async def check_reminders_async():
    now = datetime.now()
    current_time_str = now.strftime("%H:%M") # "HH:MM"
    current_day_of_week = now.strftime("%A") # "Monday"
    current_day_of_month = now.day # 1-31
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, frequency, channel, time_of_day, day_of_week, day_of_month, tone_agent, last_triggered FROM reminders WHERE is_active = 1")
    reminders = cursor.fetchall()
    
    for r in reminders:
        r_id = r['id']
        r_text = r['text']
        freq = r['frequency']
        channel = r['channel']
        time_of_day = r['time_of_day']
        day_of_week = r['day_of_week']
        day_of_month = r['day_of_month']
        tone_agent = r['tone_agent']
        last_triggered_str = r['last_triggered']
        
        due = False
        
        # Parse last triggered time
        last_triggered = None
        if last_triggered_str:
            try:
                last_triggered = datetime.fromisoformat(last_triggered_str)
            except:
                pass
                
        if freq == 'hourly':
            if not last_triggered:
                due = True
            else:
                time_diff = now - last_triggered
                if time_diff.total_seconds() >= 55 * 60:
                    due = True
        elif freq == 'daily':
            if current_time_str == time_of_day:
                if not last_triggered or last_triggered.date() < now.date():
                    due = True
        elif freq == 'weekly':
            if current_day_of_week.lower() == day_of_week.lower() and current_time_str == time_of_day:
                if not last_triggered or last_triggered.date() < now.date():
                    due = True
        elif freq == 'monthly':
            if current_day_of_month == day_of_month and current_time_str == time_of_day:
                if not last_triggered or last_triggered.date() < now.date():
                    due = True
                    
        if due:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Reminder {r_id} is due! Triggering...")
            cursor.execute("UPDATE reminders SET last_triggered = ? WHERE id = ?", (now.isoformat(), r_id))
            conn.commit()
            
            try:
                await trigger_reminder(r_text, channel, tone_agent)
            except Exception as ex:
                print(f"Error triggering reminder {r_id}: {ex}")
                
    conn.close()

def check_and_trigger_reminders():
    try:
        asyncio.run(check_reminders_async())
    except Exception as e:
        print(f"Error checking reminders: {e}")

async def run_automated_report(prompt: str):
    from agents import ensure_gitlab_tools
    ensure_gitlab_tools()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Waking up CoS Agent for scheduled task...")
    runner = InMemoryRunner(agent=chief_of_staff)
    runner.auto_create_session = True
    session_id = f"auto_scheduler_{int(time.time())}"
    
    full_prompt = f"[SYSTEM AUTO-TRIGGER] The current time is {time.strftime('%I:%M %p')}. {prompt}"
    message = types.Content(role="user", parts=[types.Part.from_text(text=full_prompt)])
    
    print("Agent is thinking and executing tools...")
    try:
        async for event in runner.run_async(user_id="background_scheduler", session_id=session_id, new_message=message):
            if event.author == "ChiefOfStaff":
                # The agent will handle sending the email via its tool.
                pass
        print("Task complete. Agent went back to sleep.")
    except Exception as e:
        print(f"Error executing scheduled task: {e}")

def job_morning_briefing():
    prompt = """
    Good morning Chief of Staff! It is time for my daily Morning Executive Briefing. 
    Please check my calendar for today and scan my latest emails. 
    Then, send me a highly structured, ADHD-friendly email briefing that includes:
    1. Key things to focus on today.
    2. Any urgent reminders.
    3. Potential risks or dependencies I need to watch out for.
    4. Clear, actionable steps I need to take.
    5. A quick motivational tip to start my day strong!
    """
    asyncio.run(run_automated_report(prompt))

def job_evening_wind_down():
    prompt = "Check my calendar for tomorrow to prep me. Search my memory bank to see what projects I'm working on. Send me an email with a short 'wind down' plan for the evening."
    asyncio.run(run_automated_report(prompt))

def run_test_job():
    prompt = "This is a test of the automated background scheduler. Please send me a quick email confirming that your background automated system is online and functioning."
    asyncio.run(run_automated_report(prompt))

def job_morning_pattern_check():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running daily Morning Email Pattern & Insight Check...")
    prompt = """
    Good morning! Run a daily pattern analysis on my email communications.
    Specifically:
    1. Read the latest emails using `read_gmail_inbox`.
    2. Search and retrieve recent emails sent by you or me (using `search_gmail_messages` with query 'label:SENT' or 'from:me') to review past communication context.
    3. FILTER NOISE: Learn to discern important/actionable emails (e.g., client requests, updates, direct questions) from newsletters or noise (spam, subscriptions, logs). Newsletters and noise MUST be completely ignored.
    4. NO HALLUCINATIONS: Do NOT fabricate or invent connections or patterns. Base everything strictly on actual email details. If there are no new significant patterns, connections, or strategic insights, do NOT generate a report and do NOT send an email (state 'No significant new patterns found.').
    5. PROVIDE REASONING: For any connections, patterns, or insights identified, provide clear reasoning explaining why you came to that conclusion, citing specific emails (sender, subject, date).
    6. If and only if you find significant new insights or patterns, send me an email using the `send_email` tool with the subject 'Executive Pattern Analysis: New Strategic Insights' detailing the patterns, insights, and reasoning.
    """
    asyncio.run(run_automated_report(prompt))

def job_evening_pattern_check():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running daily Evening Email Pattern & Insight Check...")
    prompt = """
    Good evening! Run an end-of-day pattern analysis on my email communications.
    Specifically:
    1. Read the latest emails using `read_gmail_inbox`.
    2. Search and retrieve emails sent today (using `search_gmail_messages` with query 'label:SENT' or 'from:me') to review past communication context.
    3. FILTER NOISE: Learn to discern important/actionable emails from newsletters or noise. Newsletters and noise MUST be completely ignored.
    4. NO HALLUCINATIONS: Do NOT fabricate or invent connections or patterns. Base everything strictly on actual email details. If there are no new significant patterns, connections, or strategic insights, do NOT generate a report and do NOT send an email.
    5. PROVIDE REASONING: For any connections, patterns, or insights identified, provide clear reasoning explaining why you came to that conclusion, citing specific emails (sender, subject, date).
    6. If and only if you find significant new insights or patterns, send me an email using the `send_email` tool with the subject 'Evening Pattern Analysis: New Strategic Insights' detailing the patterns, insights, and reasoning.
    """
    asyncio.run(run_automated_report(prompt))

def load_processed_commands():
    if os.path.exists("processed_commands.json"):
        try:
            with open("processed_commands.json", "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_processed_commands(processed_ids):
    with open("processed_commands.json", "w") as f:
        json.dump(list(processed_ids), f)

def job_check_user_commands():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking inbox for direct user commands or replies...")
    emails = read_gmail_inbox(max_results=5)
    if not emails or "status" in emails[0] or "error" in emails[0]:
        print("No new emails or error fetching inbox.")
        return
        
    processed_ids = load_processed_commands()
    triggered = False
    
    for em in emails:
        msg_id = em.get("id")
        if not msg_id or msg_id in processed_ids:
            continue
            
        subject = em.get("subject", "")
        sender = em.get("sender", "")
        snippet = em.get("snippet", "")
        
        is_reply = subject.lower().startswith("re:") or subject.lower().startswith("fwd:")
        is_agent_subject = any(kw in subject.lower() for kw in ["pattern analysis", "check-in", "briefing", "[test]"])
        is_direct_command = any(kw in snippet.lower() for kw in ["draft", "schedule", "remind"])
        
        if is_reply and (is_agent_subject or is_direct_command):
            print(f"Found new user instruction/reply: '{subject}'. Waking up CoS...")
            
            # Retrieve full email body
            details = get_gmail_message_details(msg_id)
            body = details.get("body", snippet)
            
            # Find active chat session ID
            from chat_tools import list_chat_histories
            histories = list_chat_histories()
            active_session_id = histories[0][0] if histories else "shared_session"
            
            asyncio.run(run_agent_and_update_history(active_session_id, body, msg_id))
            processed_ids.add(msg_id)
            triggered = True
            
    if triggered:
        save_processed_commands(processed_ids)

async def run_agent_and_update_history(session_id: str, user_prompt: str, user_email_msg_id: str = None):
    from agents import ensure_gitlab_tools
    ensure_gitlab_tools()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Waking up CoS Agent to respond to user session '{session_id}'...")
    
    from chat_tools import load_chat_history, save_chat_history
    import uuid
    
    # 1. Load active chat history
    messages = load_chat_history(session_id)
    if not messages:
        messages = [
            {"role": "assistant", "avatar": "👔", "content": "I am your Chief of Staff. I have synthesized data from your Assistant and Coach. What strategic decision or tie-breaker do you need me to resolve right now?", "id": str(uuid.uuid4())[:8]}
        ]
        
    # 2. Append the user message (from email)
    messages.append({
        "role": "user",
        "avatar": "✉️",
        "content": f"[Email Reply] {user_prompt}",
        "id": str(uuid.uuid4())[:8]
    })
    save_chat_history(session_id, messages)
    
    # 3. Construct prompt with context history to maintain continuity
    context_prompt = "Below is the history of the conversation so far for your reference:\n"
    for msg in messages[:-1]:
        context_prompt += f"- {msg['role']}: {msg['content']}\n"
    
    full_prompt = f"{context_prompt}\n\n[New Message via Email]: {user_prompt}\n\nPlease execute the command and draft your response. If you need to send an email or draft a response to an email, use the send_email tool. Make sure to reply back to the user via email if they asked you to."
    
    # 4. Run the agent
    runner = InMemoryRunner(agent=chief_of_staff)
    runner.auto_create_session = True
    session_run_id = f"sched_session_{int(time.time())}"
    message_content = types.Content(role="user", parts=[types.Part.from_text(text=full_prompt)])
    
    full_response = []
    try:
        async for event in runner.run_async(user_id="background_scheduler", session_id=session_run_id, new_message=message_content):
            if event.author == "ChiefOfStaff" and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        full_response.append(part.text)
    except Exception as e:
        print(f"Error executing agent in command response: {e}")
        
    agent_reply = "".join(full_response).strip()
    if not agent_reply:
        agent_reply = "I have received your email command and executed the task successfully."
        
    # 5. Append the agent's reply to history
    messages.append({
        "role": "assistant",
        "avatar": "👔",
        "content": agent_reply,
        "id": str(uuid.uuid4())[:8]
    })
    save_chat_history(session_id, messages)
    
    # 6. Send the reply back to the user via email as a thread reply
    if user_email_msg_id:
        try:
            from workspace_tools import get_gmail_message_details, send_email
            details = get_gmail_message_details(user_email_msg_id)
            orig_subject = details.get("subject", "Agent Response")
            reply_subject = orig_subject if orig_subject.lower().startswith("re:") else f"Re: {orig_subject}"
            print(f"Sending email reply: '{reply_subject}'...")
            send_email(to_email="me", subject=reply_subject, body=agent_reply)
        except Exception as ex:
            print(f"Failed to send email confirmation: {ex}")

if __name__ == "__main__":
    print("Starting Autonomous Executive OS Scheduler...")
    
    # Pre-programmed triggers
    schedule.every().day.at("08:00").do(job_morning_pattern_check)
    schedule.every().day.at("08:30").do(job_morning_briefing)
    schedule.every().day.at("18:00").do(job_evening_wind_down)
    schedule.every().day.at("18:00").do(job_evening_pattern_check)
    schedule.every(5).minutes.do(job_check_user_commands)
    schedule.every(1).minutes.do(check_and_trigger_reminders)
    
    # Run dynamic reminder check on startup
    print("Running initial reminders check...")
    check_and_trigger_reminders()
    
    # Run the test job immediately on startup to verify it works!
    print("Running initial startup test job...")
    run_test_job()
    
    print("Running immediate initial command check...")
    job_check_user_commands()
    
    print("Running immediate initial email patterns check...")
    job_morning_pattern_check()
    
    print("\nScheduler is now running in the background.")
    print("It will automatically trigger daily checks.")
    print("Press Ctrl+C to exit.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)
