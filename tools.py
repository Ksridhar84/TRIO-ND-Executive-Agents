import random
import datetime

def get_current_datetime() -> str:
    """Get the current date, time, and day of the week.
    
    Returns:
        str: Formatted current datetime string.
    """
    now = datetime.datetime.now()
    return now.strftime("Today is %A, %B %d, %Y at %I:%M %p")

def check_emails() -> list[dict]:
    """Check mock email inbox for new updates and priority messages.
    
    Returns:
        list[dict]: A list of unread emails with sender and subject.
    """
    return [
        {
            "sender": "CEO / Board President",
            "subject": "Urgent: Project Pitch Slide Review required by tomorrow 9 AM",
            "priority": "High"
        },
        {
            "sender": "HR Team",
            "subject": "Action Needed: Complete quarterly health wellness survey",
            "priority": "Medium"
        },
        {
            "sender": "Weekly Newsletter",
            "subject": "Productivity Tip: The power of the 5-minute break",
            "priority": "Low"
        }
    ]

def breakdown_complex_task(task_title: str, steps_count: int = 3) -> list[str]:
    """Breakdown a complex, overwhelming task into bite-sized, ADHD-friendly micro-steps.
    
    Args:
        task_title: The name/title of the complex task.
        steps_count: Number of micro-steps to generate. Default is 3.
        
    Returns:
        list[str]: List of small, sequential micro-steps.
    """
    templates = {
        "presentation": [
            "Set a 15-minute timer and open a blank document (no slides yet!).",
            "Write down the top 3 core takeaways you want the audience to remember.",
            "Gather 1-2 images or figures and drop them in a folder.",
            "Write a single one-breath sentence summary for each slide.",
            "Do a final run-through out loud to verify timing."
        ],
        "email": [
            "Open your inbox and focus only on the top email.",
            "Draft a 2-sentence response template.",
            "Hit send and immediately take a deep breath.",
            "Move onto the next email or close the tab for a break."
        ]
    }
    
    # Try to match keywords in the title, otherwise generate general micro-steps
    task_lower = task_title.lower()
    steps = []
    if "presentation" in task_lower or "slide" in task_lower or "deck" in task_lower:
        steps = templates["presentation"]
    elif "email" in task_lower or "inbox" in task_lower or "message" in task_lower:
        steps = templates["email"]
    else:
        steps = [
            f"Set a 10-minute timer to do the absolute first, smallest step of '{task_title}'.",
            "Prepare the tools or workspace needed (e.g., open tabs, grab a glass of water).",
            "Write down just one sentence or outline one part of the task.",
            "Reward yourself with a 2-minute break once the timer rings."
        ]
        
    # Return requested number of steps
    return steps[:steps_count]

def analyze_decision_matrix(options: list[str]) -> dict:
    """Analyze a list of decision options by outlining pros, cons, and mapping goals.
    
    Args:
        options: The different choices/options to analyze.
        
    Returns:
        dict: A decision matrix with pros, cons, and a recommended easy choice to avoid decision paralysis.
    """
    matrix = {}
    for opt in options:
        opt_lower = opt.lower()
        if "now" in opt_lower or "immediately" in opt_lower or "first" in opt_lower:
            matrix[opt] = {
                "Pros": "Generates immediate momentum, reduces anxiety of delay.",
                "Cons": "Requires immediate activation energy, might feel stressful.",
                "Alignment": "Matches ADHD need for urgency/momentum."
            }
        else:
            matrix[opt] = {
                "Pros": "Provides prep time, lowers pressure.",
                "Cons": "Higher risk of procrastination, prolongs anxiety.",
                "Alignment": "Good if prerequisites/dependencies are missing."
            }
            
    # Highlight the option with the lowest activation energy as the recommended starting point
    recommendation = options[0] if options else "No options provided"
    
    return {
        "matrix": matrix,
        "recommended_starting_point": recommendation,
        "coaching_tip": "Choose the path with the lowest starting friction to beat task inertia!"
    }

def get_wellness_break_recommendation() -> str:
    """Get a quick, ADHD-friendly physical or mental wellness break recommendation.
    
    Returns:
        str: A cheery break activity description.
    """
    breaks = [
        "Hydration Check: Go drink a big glass of cool water right now! 💧",
        "Physical Reset: Stand up, stretch your arms high, and roll your shoulders back. 🧘",
        "Sensory Break: Close your eyes for 30 seconds and take three slow, deep breaths. 🌬️",
        "Movement Burst: Do a 30-second silly dance break to shake off the physical tension! 💃"
    ]
    return random.choice(breaks)

def get_cheery_inspiration() -> str:
    """Retrieve an uplifting joke, funny anecdote, or inspirational story.
    
    Returns:
        str: A supportive, motivating, or lighthearted joke.
    """
    inspirations = [
        "Why don't scientists trust atoms? Because they make up everything! Just like that overwhelming feeling—it's mostly empty space, you've got this! ⚛️",
        "Remember: You don't have to build the whole wall today. Just lay one brick as perfectly as you can. Brick by brick! 🧱",
        "ADHD superpower check: Your brain is incredibly fast, creative, and capable of unique connections. You aren't behind; you're just running on a different system! 🚀",
        "Why did the computer go to the doctor? It had a virus! Just like a rabbit hole—sometimes a quick reboot is all we need to clear the cache. Let's start fresh! 💻"
    ]
    return random.choice(inspirations)
