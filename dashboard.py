import streamlit as st
import time
import asyncio
import os
import datetime
import base64
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types
from agents import chief_of_staff
from voice_tools import generate_agent_voice
from streamlit_mic_recorder import mic_recorder

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

# --- Initialize Session State for Audio ---
if "voice_bytes" not in st.session_state:
    st.session_state.voice_bytes = None

# --- Sidebar: Multi-Modal Hub & Avatar ---
with st.sidebar:
    avatar_placeholder = st.empty()
    if avatar_b64:
        avatar_placeholder.markdown(f'<img src="data:image/png;base64,{avatar_b64}" class="avatar-idle">', unsafe_allow_html=True)
        
    st.header("📎 Multi-Modal Hub")
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

# --- Initialize Conversation Session History ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "avatar": "👔", "content": "I am your Chief of Staff. I have synthesized data from your Assistant and Coach. What strategic decision or tie-breaker do you need me to resolve right now?"}
    ]

# --- Render the Persistent Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg["avatar"]):
        st.write(msg["content"])
        if msg.get("has_file"):
            st.caption("*(📎 Included an attachment)*")
        if msg.get("audio_bytes"):
            st.audio(msg["audio_bytes"], format="audio/mp3")

# --- THE FIXED INPUT BLOCK ---
if user_prompt := st.chat_input("Type your messy thought, or press Enter to just send your uploaded file/audio..."):
    
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
    st.session_state.messages.append({"role": "user", "avatar": "👤", "content": user_prompt, "has_file": has_file})
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

    st.session_state.messages.append({"role": "assistant", "avatar": "👔", "content": cos_response, "audio_bytes": audio_bytes})
    with st.chat_message("assistant", avatar="👔"):
        st.write(cos_response)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
