import streamlit as st
import os

# Map Streamlit secrets recursively and case-insensitively to environment variables
try:
    if hasattr(st, "secrets") and st.secrets:
        def map_dict(d, prefix=""):
            for k, v in d.items():
                if isinstance(v, dict) or (hasattr(v, "items") and callable(getattr(v, "items"))):
                    map_dict(v, prefix + k.upper() + "_")
                else:
                    val_str = str(v)
                    os.environ[k] = val_str
                    os.environ[k.upper()] = val_str
                    if prefix:
                        os.environ[prefix + k.upper()] = val_str
        map_dict(st.secrets)
except Exception:
    pass

import time
import asyncio
import datetime
import base64
from dotenv import load_dotenv
import re
from google.adk.runners import InMemoryRunner
import uuid
from google.genai import types
from agents import chief_of_staff
from voice_tools import generate_agent_voice
from streamlit_mic_recorder import mic_recorder
from chat_tools import save_chat_history, load_chat_history, list_chat_histories
from memory_tools import store_memory

# Setup API Key for Streamlit
load_dotenv()
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")


# Real Agent Backend Integration
async def get_agent_response(prompt_text, file_bytes=None, mime_type=None):
    runner = InMemoryRunner(agent=chief_of_staff)
    runner.auto_create_session = True
    session_id = f"streamlit_session_{int(time.time())}"
    
    parts = []
    if prompt_text:
        # Inject current time as hidden context so the agent never hallucinates the date
        current_time_str = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        hidden_context = f"[System Info: The current date and time is {current_time_str}]\n\n{prompt_text}"
        parts.append(types.Part.from_text(text=hidden_context))
    if file_bytes and mime_type:
        parts.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
        
    message = types.Content(role="user", parts=parts)
    
    full_output = []
    async for event in runner.run_async(user_id="streamlit_user", session_id=session_id, new_message=message):
        if event.author and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    # Format sub-agents as blockquotes
                    if event.author != "ChiefOfStaff":
                        formatted_text = part.text.replace("\n", "\n> ")
                        full_output.append(f"> **{event.author}**:\n> {formatted_text}")
                    else:
                        full_output.append(part.text)
    return "\n\n".join(full_output)

# --- Neurodivergent-Friendly Premium Config ---
st.set_page_config(page_title="Chief of Staff HQ", layout="wide", initial_sidebar_state="expanded")

# Aesthetic Glassmorphism & Soft Pastel CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Sleek background gradient to prevent sensory fatigue */
    [data-testid="stAppViewContainer"] { 
        background: linear-gradient(135deg, #0D0E15 0%, #1A1A24 100%);
    }
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Chat Message Bubbles - Glassmorphism */
    [data-testid="stChatMessage"] { 
        border-radius: 16px; 
        padding: 20px; 
        margin-bottom: 15px; 
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, background 0.2s ease;
    }
    [data-testid="stChatMessage"]:hover {
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Headers and accents - Soft Lavender/Blue Pastel Gradient */
    h1 {
        background: -webkit-linear-gradient(45deg, #B5C6FF, #E5B2FF) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
    }
    
    /* Subtle color pops for links or subtext */
    .st-emotion-cache-1wmy9hl { /* Generic caption target fallback */
        color: #8C9EFF !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(20, 20, 28, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Avatar Animations */
    @keyframes pulse-ring {
      0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(181, 198, 255, 0.7); }
      70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(181, 198, 255, 0); }
      100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(181, 198, 255, 0); }
    }
    .avatar-idle {
        width: 180px;
        height: 180px;
        border-radius: 50%;
        border: 2px solid #B5C6FF;
        display: block;
        margin: 0 auto 20px auto;
        object-fit: cover;
    }
    .avatar-speaking {
        width: 180px;
        height: 180px;
        border-radius: 50%;
        border: 2px solid #B5C6FF;
        display: block;
        margin: 0 auto 20px auto;
        object-fit: cover;
        animation: pulse-ring 1.5s infinite;
    }
    
    /* Mobile Responsiveness tweaks */
    @media (max-width: 768px) {
        .avatar-idle, .avatar-speaking {
            width: 100px !important;
            height: 100px !important;
            margin: 0 auto 15px auto !important;
        }
        [data-testid="stChatMessage"] { 
            padding: 12px !important; 
            border-radius: 12px !important;
        }
        h1 {
            font-size: 1.8rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 Neural Executive Command Center")
st.caption("Coordinated support: Chief of Staff (Supervisor) • Executive Assistant • Executive Coach")

# --- Avatar Loading ---
def load_image_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

avatar_b64 = load_image_b64("assets/cos_avatar.png")

# --- Initialize Session State for Audio & Session ID ---
if "voice_bytes" not in st.session_state:
    st.session_state.voice_bytes = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- Sidebar: Multi-Modal Hub & Avatar ---
with st.sidebar:
    avatar_placeholder = st.empty()
    if avatar_b64:
        avatar_placeholder.markdown(f'<img src="data:image/png;base64,{avatar_b64}" class="avatar-idle">', unsafe_allow_html=True)
        
    st.header("📎 Multi-Modal Hub")
    
    # Secrets Diagnostics Expander (collapsible, low-sensory clutter)
    try:
        if hasattr(st, "secrets") and st.secrets:
            loaded_keys = [f"`{k}`" for k in st.secrets.keys()]
            if loaded_keys:
                with st.expander("🔑 Secrets Diagnostics (Debug)"):
                    st.write("Loaded keys: " + ", ".join(loaded_keys))
                    st.caption("All keys mapped to system environment variables.")
            else:
                with st.expander("🔑 Secrets Diagnostics (Debug)"):
                    st.warning("No keys found in Streamlit Secrets!")
        else:
            with st.expander("🔑 Secrets Diagnostics (Debug)"):
                st.warning("st.secrets is empty or unavailable.")
    except Exception as e:
        pass

    st.markdown("Upload files, hand-written notes, or record a voice memo. They will be passed to your agents on your next chat message!")
    
    uploaded_file = st.file_uploader("Upload Image, Document, or Video")
    
    st.markdown("### 🎙️ Voice Memo")
    voice_memo = mic_recorder(
        start_prompt="🎙️ Start Recording",
        stop_prompt="🛑 Stop Recording",
        just_once=True,
        use_container_width=True,
        key="voice_recorder"
    )
    
    # Immediately catch and store the audio in session state before the page reruns!
    if voice_memo and "bytes" in voice_memo:
        st.session_state.voice_bytes = voice_memo["bytes"]
        st.success("✅ Audio recorded! Type a message below and hit Enter to send it.")
        
    st.markdown("---")
    st.header("🧘 Daily Coach Check-In")
    st.markdown("How are we feeling right now?")
    energy_level = st.slider("Energy Level", min_value=1, max_value=10, value=5)
    focus_level = st.slider("Focus/Cognitive Clarity", min_value=1, max_value=10, value=5)
    
    if st.button("Submit to Coach"):
        check_in_msg = f"Daily Check-In: My Energy Level is {energy_level}/10 and my Focus Level is {focus_level}/10. Coach, please assess my state and CoS, please recommend a Spotify playlist to match or fix this state."
        st.session_state.pending_checkin = check_in_msg
        st.success("Submitted! The Chief of Staff is reviewing your state...")

    st.markdown("---")
    st.header("🗄️ Conversation History")
    
    if st.button("➕ Start New Conversation", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = [
            {"role": "assistant", "avatar": "👔", "content": "I am your Chief of Staff. I have synthesized data from your Assistant and Coach. What strategic decision or tie-breaker do you need me to resolve right now?"}
        ]
        st.rerun()
        
    histories = list_chat_histories()
    if histories:
        chat_dict = {h[1]: h[0] for h in histories}
        selected_display = st.selectbox("Load Previous:", ["-- Select --"] + list(chat_dict.keys()), label_visibility="collapsed")
        if st.button("📂 Load Chat", use_container_width=True):
            if selected_display != "-- Select --":
                st.session_state.session_id = chat_dict[selected_display]
                st.session_state.messages = load_chat_history(chat_dict[selected_display])
                st.rerun()

# --- Initialize Conversation Session History ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "avatar": "👔", "content": "I am your Chief of Staff. I have synthesized data from your Assistant and Coach. What strategic decision or tie-breaker do you need me to resolve right now?", "id": str(uuid.uuid4())[:8]}
    ]

# Ensure all legacy messages have a permanent ID to prevent duplicate key errors on reruns
for msg in st.session_state.messages:
    if "id" not in msg:
        msg["id"] = str(uuid.uuid4())[:8]

# --- Render the Persistent Chat History ---
for msg in st.session_state.messages:
            st.write(msg["content"])
            
            # Check for standard Spotify URLs
            content = msg["content"]
            spotify_pattern = r'(https://open\.spotify\.com/playlist/[a-zA-Z0-9]+)'
            spotify_matches = [url.strip() for url in re.findall(spotify_pattern, content)]
            
            for url in spotify_matches:
                embed_url = url.replace("/playlist/", "/embed/playlist/") + "?utm_source=generator"
                st.components.v1.html(
                    f'<iframe style="border-radius:12px" src="{embed_url}" width="100%" height="152" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>',
                    height=160
                )
            
            if msg.get("has_file"):
                st.caption("*(📎 Included an attachment)*")
            if msg.get("audio_bytes"):
                st.audio(msg["audio_bytes"], format="audio/mp3")

            # Add Feedback & Copy UI for Assistant messages
            if msg["role"] == "assistant":
                col_spacer, col1, col2, col3 = st.columns([6, 1, 1, 1.5])
                msg_id = msg.get("id", str(uuid.uuid4())[:8]) # give it a pseudo id if none exists to prevent duplicate keys
                
                with col1:
                    if st.session_state.get(f"liked_{msg_id}"):
                        st.button("💖", key=f"up_{msg_id}_done", type="primary", disabled=True)
                    else:
                        if st.button("👍", key=f"up_{msg_id}"):
                            st.session_state[f"liked_{msg_id}"] = True
                            store_memory("Agent Feedback", f"The user PREFERS this style of response: {content[:200]}...")
                            st.rerun()
                with col2:
                    if st.session_state.get(f"disliked_{msg_id}"):
                        st.button("👎", key=f"down_{msg_id}_done", type="primary", disabled=True)
                    else:
                        if st.button("👎", key=f"down_{msg_id}"):
                            st.session_state[f"disliked_{msg_id}"] = True
                            store_memory("Agent Feedback", f"The user DISLIKES this style of response. AVOID doing this: {content[:200]}...")
                            st.rerun()
                with col3:
                    if st.button("📋 Copy", key=f"copy_{msg_id}"):
                        import subprocess
                        try:
                            subprocess.run("pbcopy", text=True, input=content)
                            st.toast("✅ Copied to clipboard!")
                        except Exception as e:
                            st.error(f"Failed to copy: {e}")

# --- Get Input from either Chat or Sidebar Check-In ---
user_prompt = st.chat_input("Type your messy thought, or press Enter to just send your uploaded file/audio...")
pending_checkin = getattr(st.session_state, "pending_checkin", None)

if pending_checkin:
    user_prompt = pending_checkin
    st.session_state.pending_checkin = None

# --- PROCESS THE INPUT ---
if user_prompt:
    
    # Check if we have files from the sidebar
    file_bytes = None
    mime_type = None
    has_file = False
    
    if st.session_state.voice_bytes:
        file_bytes = st.session_state.voice_bytes
        mime_type = "audio/wav"
        has_file = True
        st.session_state.voice_bytes = None # Clear after grabbing
    elif uploaded_file:
        file_bytes = uploaded_file.read()
        mime_type = uploaded_file.type
        has_file = True

    # 1. Display your text input instantly on screen
    st.session_state.messages.append({"role": "user", "avatar": "👤", "content": user_prompt, "has_file": has_file, "id": str(uuid.uuid4())[:8]})
    with st.chat_message("user", avatar="👤"):
        st.write(user_prompt)
        if has_file:
            st.caption("*(📎 Included an attachment)*")

    # 2. Trigger the Chief of Staff agent processing loop
    if avatar_b64:
        avatar_placeholder.markdown(f'<img src="data:image/png;base64,{avatar_b64}" class="avatar-speaking">', unsafe_allow_html=True)
        
    with st.spinner("CoS is building team consensus..."):
        try:
            cos_response = asyncio.run(get_agent_response(user_prompt, file_bytes, mime_type))
            if not cos_response.strip():
                cos_response = "The team processed your request but returned no text output."
                
            # --- FOOLPROOF SPOTIFY INJECTION ---
            # If the user did a check-in, we bypass the LLM and forcefully append the Spotify link!
            if "Daily Check-In:" in user_prompt:
                from spotify_tools import recommend_spotify_playlist
                if "Energy Level is 1/" in user_prompt or "Energy Level is 2/" in user_prompt or "Energy Level is 3/" in user_prompt:
                    forced_spotify = recommend_spotify_playlist("lofi")
                elif "Energy Level is 8/" in user_prompt or "Energy Level is 9/" in user_prompt or "Energy Level is 10/" in user_prompt:
                    forced_spotify = recommend_spotify_playlist("high_energy")
                elif "Focus Level is 1/" in user_prompt or "Focus Level is 2/" in user_prompt or "Focus Level is 3/" in user_prompt:
                    forced_spotify = recommend_spotify_playlist("brown_noise")
                else:
                    forced_spotify = recommend_spotify_playlist("focus")
                
                cos_response += f"\n\n***\n**Direct Audio Link:**\n{forced_spotify}"
                
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                cos_response = "⚠️ **Rate Limit Exceeded:** The AI API is currently rate-limited (429). Please wait a moment and try again."
            else:
                cos_response = f"**Error executing ADK workflow:**\n{e}"

    if avatar_b64:
        avatar_placeholder.markdown(f'<img src="data:image/png;base64,{avatar_b64}" class="avatar-idle">', unsafe_allow_html=True)

    # 3. Stream the agent result back to your screen
    audio_bytes = None
    if cos_response and "Error executing" not in cos_response:
        try:
            audio_bytes = generate_agent_voice(cos_response)
        except Exception as e:
            st.error(f"Failed to generate audio: {e}")

    st.session_state.messages.append({"role": "assistant", "avatar": "👔", "content": cos_response, "audio_bytes": audio_bytes, "id": str(uuid.uuid4())[:8]})
    save_chat_history(st.session_state.session_id, st.session_state.messages)
    
    # Rerun the app to seamlessly render the new message through the persistent loop above
    st.rerun()
