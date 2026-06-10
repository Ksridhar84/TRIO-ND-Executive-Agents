import schedule
import time
import asyncio
import os
import json
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types
from agents import chief_of_staff
from workspace_tools import read_gmail_inbox

load_dotenv()
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")

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
        
    prompt += "Analyze these emails. If one of them is from ME (the user), treat it as a direct command and execute any instructions I gave you. Otherwise, if there is anything urgent or important from someone else, please send me an email summarizing it to keep me informed. If it's just spam or trivial, you can ignore it."
    
    asyncio.run(run_automated_report(prompt))

if __name__ == "__main__":
    print("Starting Autonomous Executive OS Scheduler...")
    
    # Pre-programmed triggers
    schedule.every().day.at("08:30").do(job_morning_briefing)
    schedule.every().day.at("18:00").do(job_evening_wind_down)
    schedule.every(1).hours.do(job_hourly_inbox_check)
    
    # Run the test job immediately on startup to verify it works!
    print("Running initial startup test job...")
    run_test_job()
    
    print("Running immediate initial inbox check...")
    job_hourly_inbox_check()
    
    print("\\nScheduler is now running in the background.")
    print("It will automatically trigger at 8:00 AM and 6:00 PM every day.")
    print("Press Ctrl+C to exit.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)
