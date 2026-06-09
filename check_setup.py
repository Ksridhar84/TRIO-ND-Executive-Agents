import os
import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def verify_setup():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in the environment or .env file.")
        print("Please set your GEMINI_API_KEY in the .env file.")
        return
    
    # Ensure GEMINI_API_KEY is set for the underlying SDK
    os.environ["GEMINI_API_KEY"] = api_key

    print("Verifying setup configuration...")
    try:
        # Create a simple agent with a test instruction
        agent = Agent(
            name="verification_agent",
            instruction="You are a helpful assistant. Keep your response under 10 words.",
        )
        
        # Initialize the InMemoryRunner to execute our agent
        runner = InMemoryRunner(agent=agent)
        runner.auto_create_session = True
        
        # Prepare a verification message
        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text="Respond with 'Setup Works!'")]
        )
        
        print("Sending request to Gemini model...")
        
        # Run the agent and capture response events
        response_text = ""
        async for event in runner.run_async(
            user_id="verifier",
            session_id="verify_session",
            new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        
        print(f"Agent Response: {response_text.strip()}")
        if "Setup Works" in response_text or response_text.strip():
            print("SUCCESS: Google ADK setup and model authentication are working correctly!")
        else:
            print("FAILURE: No response received from the model.")
            
    except Exception as e:
        print(f"ERROR: Failed to run setup verification. Details: {e}")

if __name__ == "__main__":
    asyncio.run(verify_setup())
