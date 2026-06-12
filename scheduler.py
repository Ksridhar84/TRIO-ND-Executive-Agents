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

def load_processed_emails():
    if os.path.exists("processed_emails.json"):
        try:
            with open("processed_emails.json", "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_processed_emails(processed_ids):
    with open("processed_emails.json", "w") as f:
        json.dump(list(processed_ids), f)

def job_hourly_inbox_check():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Polling inbox for new unread emails...")
    emails = read_gmail_inbox(max_results=10)
    
    if not emails or "status" in emails[0] or "error" in emails[0]:
        print("No new emails found.")
        return
        
    processed_ids = load_processed_emails()
    new_emails = []
    
    for email in emails:
        if email.get("id") and email["id"] not in processed_ids:
            new_emails.append(email)
            processed_ids.add(email["id"])
            
    if not new_emails:
        print("All unread emails have already been processed.")
        return
        
    # Save the updated memory bank
    save_processed_emails(processed_ids)
    
    print(f"Found {len(new_emails)} new emails! Waking up CoS to process them...")
    
    # Construct the prompt for the agent
    prompt = f"Background Alert: I have received {len(new_emails)} new emails in my inbox:\\n\\n"
    for em in new_emails:
        prompt += f"- From: {em['sender']}\\n  Subject: {em['subject']}\\n  Snippet: {em['snippet']}\\n\\n"
        
    prompt += "Activate your Pattern Recognition Engine. Analyze these new emails alongside your memory of past emails. Do not just summarize them one-by-one. Connect the dots: Are there any emerging patterns, duplicate requests, overlapping projects, or systemic trends the user should know about? If you find a useful connection or urgent systemic issue, send me an email with your dot-connecting insights."
    
    asyncio.run(run_automated_report(prompt))

if __name__ == "__main__":
    print("Starting Autonomous Executive OS Scheduler...")
    
    # Pre-programmed triggers
    schedule.every().day.at("08:30").do(job_morning_briefing)
    schedule.every().day.at("18:00").do(job_evening_wind_down)
    schedule.every(1).hours.do(job_hourly_inbox_check)
    schedule.every(1).minutes.do(check_and_trigger_reminders)
    
    # Run dynamic reminder check on startup
    print("Running initial reminders check...")
    check_and_trigger_reminders()
    
    # Run the test job immediately on startup to verify it works!
    print("Running initial startup test job...")
    run_test_job()
    
    print("Running immediate initial inbox check...")
    job_hourly_inbox_check()
    
    print("\nScheduler is now running in the background.")
    print("It will automatically trigger at 8:00 AM and 6:00 PM every day.")
    print("Press Ctrl+C to exit.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)
