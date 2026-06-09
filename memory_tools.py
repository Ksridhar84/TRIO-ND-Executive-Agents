import json
import os

MEMORY_FILE = "memory_bank.json"

def _load_memory() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def _save_memory(data: dict):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def store_memory(topic: str, details: str) -> str:
    """Store important context, preferences, or project details into the persistent long-term memory bank.
    
    Args:
        topic (str): The subject or category of the memory (e.g., 'user_preferences', 'project_alpha').
        details (str): The detailed context or information to remember.
        
    Returns:
        str: Confirmation message.
    """
    memory = _load_memory()
    topic_lower = topic.lower()
    
    if topic_lower not in memory:
        memory[topic_lower] = []
        
    memory[topic_lower].append(details)
    _save_memory(memory)
    
    return f"Successfully stored memory under topic: '{topic}'"

def search_memory(query: str) -> str:
    """Search the persistent long-term memory bank for past context, preferences, or project details.
    
    Args:
        query (str): The keyword or topic to search for.
        
    Returns:
        str: Formatted string containing any matched memories.
    """
    memory = _load_memory()
    query_lower = query.lower()
    results = []
    
    for topic, entries in memory.items():
        if query_lower in topic:
            for entry in entries:
                results.append(f"[{topic}]: {entry}")
        else:
            for entry in entries:
                if query_lower in entry.lower():
                    results.append(f"[{topic}]: {entry}")
                    
    if not results:
        return f"No memories found matching '{query}'."
        
    return "Found the following memories:\n- " + "\n- ".join(results)
