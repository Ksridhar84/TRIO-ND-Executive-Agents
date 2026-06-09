import os
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types
from dotenv import load_dotenv
from agents import chief_of_staff

load_dotenv()

async def run_test():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set. Please check your .env file.")
        return
        
    # Ensure GEMINI_API_KEY is set for the underlying SDK
    os.environ["GEMINI_API_KEY"] = api_key

    print("Initializing ChiefOfStaff Agent Runner...")
    runner = InMemoryRunner(agent=chief_of_staff)
    runner.auto_create_session = True

    # This prompt requires delegation to both subagents:
    # 1. Executive Assistant (to break down the task)
    # 2. Executive Coach (to help with tunnel vision/overwhelm)
    prompt = (
        "I need to prep for a major project presentation tomorrow. I'm feeling extremely overwhelmed, "
        "stuck in a rabbit hole, and don't know where to start. Please check in with my assistant "
        "to break down the task, and check with my coach to help me step out of this tunnel vision."
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
    )

    print(f"\n[User Request]: {prompt}\n")
    print("--------------------------------------------------------------------------------")
    print("Streaming agent network execution events...")
    print("--------------------------------------------------------------------------------")
    
    async for event in runner.run_async(
        user_id="test_user",
        session_id="nd_trio_session",
        new_message=message
    ):
        if event.author:
            # Print text content
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"\n[{event.author}]: {part.text}")
            
            # Print tool calls (including agent transfers)
            fcs = event.get_function_calls()
            if fcs:
                for fc in fcs:
                    print(f"\n[{event.author} Tool Call]: {fc.name} (args: {fc.args})")
            
            # Print tool responses
            frs = event.get_function_responses()
            if frs:
                for fr in frs:
                    print(f"\n[Tool Response to {event.author}]: {fr.name} (result: {fr.response})")

if __name__ == "__main__":
    asyncio.run(run_test())
