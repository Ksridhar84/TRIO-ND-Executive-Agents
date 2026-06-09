import os
import sys
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types
from dotenv import load_dotenv
from agents import chief_of_staff

async def run_workflow(command_text: str):
    # Load environment variables
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set. Please check your .env file.")
        return
        
    os.environ["GEMINI_API_KEY"] = api_key
    
    project_id = os.environ.get("GITLAB_PROJECT_ID")
    if not project_id:
        print("ERROR: GITLAB_PROJECT_ID is not defined in the .env file.")
        return

    max_retries = 3
    retry_delay = 25  # seconds (Free tier allows 5 requests per minute)

    for attempt in range(1, max_retries + 1):
        print(f"Initializing ChiefOfStaff Agent Runner (Attempt {attempt}/{max_retries})...")
        runner = InMemoryRunner(agent=chief_of_staff)
        runner.auto_create_session = True

        # Use a unique session ID per attempt to start clean and avoid duplication
        session_id = f"gitlab_workflow_session_attempt_{attempt}"

        # Construct the instruction prompt for the agent team
        prompt = (
            f"We need to create a GitLab task card (issue) for the following command:\n"
            f"\"{command_text}\"\n\n"
            f"Please execute this task on GitLab project: {project_id}\n\n"
            f"Steps to execute:\n"
            f"1. Chief of Staff: Transfer/delegate this request to the Executive Assistant agent.\n"
            f"2. Executive Assistant: Use the create_issue tool to build a task card (issue) in the GitLab project '{project_id}'. The title, description, and any labels should be derived from the user's command.\n"
            f"3. Executive Assistant: Once the task card is successfully created, transfer control back to the Chief of Staff.\n"
            f"4. Chief of Staff: Compile a unified summary of the created issue (including the title, description, and any generated ID/link) and list the next actions."
        )

        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )

        print("\n--------------------------------------------------------------------------------")
        print(f"[User command text]: {command_text}")
        print("--------------------------------------------------------------------------------")
        print(f"Executing Multi-Agent Workflow (Attempt {attempt})...")
        print("--------------------------------------------------------------------------------")
        
        try:
            async for event in runner.run_async(
                user_id="workflow_user",
                session_id=session_id,
                new_message=message
            ):
                if event.author:
                    # Print text content from agent
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                print(f"\n[{event.author}]: {part.text}")
                    
                    # Print tool calls (including agent transfers)
                    fcs = event.get_function_calls()
                    if fcs:
                        for fc in fcs:
                            args_str = ", ".join(f"{k}={v}" for k, v in fc.args.items()) if fc.args else ""
                            print(f"\n[{event.author} Tool Call]: {fc.name}({args_str})")
                    
                    # Print tool responses
                    frs = event.get_function_responses()
                    if frs:
                        for fr in frs:
                            print(f"\n[Tool Response to {event.author}]: {fr.name} -> {fr.response}")

            print("\n--------------------------------------------------------------------------------")
            print("Workflow execution completed successfully.")
            print("--------------------------------------------------------------------------------")
            break  # Exit retry loop on success

        except Exception as e:
            e_str = str(e)
            if "RESOURCE_EXHAUSTED" in e_str or "429" in e_str:
                if attempt < max_retries:
                    print(f"\n[Warning] Hit rate limit (RESOURCE_EXHAUSTED / 429). Waiting {retry_delay} seconds before retrying...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    print(f"\n[Error] Maximum retries reached. Rate limit error details: {e}")
                    raise e
            else:
                print(f"\n[Error] Unexpected exception: {e}")
                raise e

def main():
    if len(sys.argv) > 1:
        command_text = " ".join(sys.argv[1:])
    else:
        print("No command-line arguments provided.")
        command_text = input("Please enter the text command you want to process:\n> ")
        if not command_text.strip():
            print("Empty command. Exiting.")
            sys.exit(0)
            
    asyncio.run(run_workflow(command_text))

if __name__ == "__main__":
    main()
