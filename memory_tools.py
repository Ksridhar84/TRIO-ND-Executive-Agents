import sqlite3
import json
import os
import math
from google.genai import client, types

# Initialize SQLite database
DB_PATH = os.path.join(os.path.dirname(__file__), "memory_db.sqlite")

def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        details TEXT,
        embedding TEXT
    )''')
    return conn

def get_embedding(text: str) -> list[float]:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    genai_client = client.Client(api_key=api_key)
    response = genai_client.models.embed_content(
        model='text-embedding-004',
        contents=text,
    )
    return response.embeddings[0].values

def cosine_similarity(v1, v2):
    dot = sum(a*b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a*a for a in v1))
    norm2 = math.sqrt(sum(b*b for b in v2))
    return dot / (norm1 * norm2)

def store_memory(topic: str, details: str) -> str:
    """Store important context, preferences, or project details into the persistent long-term vector memory bank.
    
    Args:
        topic (str): The subject or category of the memory (e.g., 'user_preferences', 'project_alpha').
        details (str): The detailed context or information to remember.
        
    Returns:
        str: Confirmation message.
    """
    conn = _get_db()
    cursor = conn.cursor()
    # Combine for embedding context
    embedding = get_embedding(f"Topic: {topic}. Details: {details}")
    cursor.execute("INSERT INTO memories (topic, details, embedding) VALUES (?, ?, ?)", 
                   (topic, details, json.dumps(embedding)))
    conn.commit()
    conn.close()
    
    return f"Successfully stored memory under topic: '{topic}'"

def search_memory(query: str, n_results: int = 3) -> str:
    """Search the persistent long-term vector memory bank for past context, preferences, or project details.
    
    Args:
        query (str): The keyword, topic, or semantic idea to search for.
        n_results (int): Number of top results to return.
        
    Returns:
        str: Formatted string containing any matched memories.
    """
    try:
        query_emb = get_embedding(query)
    except Exception as e:
        return f"Error connecting to embedding model: {e}"
    
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT topic, details, embedding FROM memories")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return f"No memories found matching '{query}'."
        
    scored_results = []
    for topic, details, emb_str in rows:
        emb = json.loads(emb_str)
        sim = cosine_similarity(query_emb, emb)
        scored_results.append((sim, topic, details))
        
    scored_results.sort(reverse=True, key=lambda x: x[0])
    
    top_results = scored_results[:n_results]
    
    formatted_results = []
    for sim, topic, details in top_results:
        # Only return reasonably relevant results
        if sim > 0.5:
            formatted_results.append(f"[{topic}]: {details}")
            
    if not formatted_results:
        return f"No strongly relevant memories found for '{query}'."
        
    return "Found the following semantically relevant memories:\n- " + "\n- ".join(formatted_results)
