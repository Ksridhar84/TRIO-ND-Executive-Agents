import schedule
import time
import asyncio
import os
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types
from agents import chief_of_staff

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
    prompt = "Check my calendar for today and my latest 3 emails. Send an email to me summarizing my morning briefing in an ADHD-friendly, highly structured format. Tell me to drink water."
    asyncio.run(run_automated_report(prompt))

def job_evening_wind_down():
    prompt = "Check my calendar for tomorrow to prep me. Search my memory bank to see what projects I'm working on. Send me an email with a short 'wind down' plan for the evening."
    asyncio.run(run_automated_report(prompt))

def run_test_job():
    prompt = "This is a test of the automated background scheduler. Please send me a quick email confirming that your background automated system is online and functioning."
    asyncio.run(run_automated_report(prompt))

if __name__ == "__main__":
    print("Starting Autonomous Executive OS Scheduler...")
    
    # Pre-programmed triggers
    schedule.every().day.at("08:00").do(job_morning_briefing)
    schedule.every().day.at("18:00").do(job_evening_wind_down)
    
    # Run the test job immediately on startup to verify it works!
    print("Running initial startup test job...")
    run_test_job()
    
    print("\\nScheduler is now running in the background.")
    print("It will automatically trigger at 8:00 AM and 6:00 PM every day.")
    print("Press Ctrl+C to exit.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)
