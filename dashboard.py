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
from tools import get_localized_now
from streamlit_autorefresh import st_autorefresh
from reminder_tools import (
    create_reminder,
    list_reminders,
    delete_reminder,
    toggle_reminder,
    get_pending_voice_alert,
    mark_voice_alert_played
)

# Setup API Key for Streamlit
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key.strip()


# Real Agent Backend Integration
async def get_agent_response(prompt_text, session_id, file_bytes=None, mime_type=None, placeholder=None):
    from agents import ensure_gitlab_tools
    ensure_gitlab_tools()
    runner = InMemoryRunner(agent=chief_of_staff)
    runner.auto_create_session = True
    
    # Load chat history from disk to maintain continuity
    from chat_tools import load_chat_history
    history = load_chat_history(session_id) or []
    
    context_prompt = "Below is the history of the conversation so far for your reference:\n"
    for msg in history:
        # Exclude the user's current message which will be appended as new_message
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Strip out any voice alert indicators to keep clean text
        if content.startswith("📢 **Voice Alert**:") or content.startswith("📢 **Test Voice Alert**:"):
            continue
        context_prompt += f"- {role}: {content}\n"
        
    parts = []
    if prompt_text:
        # Inject current time and conversation history as hidden context so the agent has memory and date info
        current_time_str = get_localized_now().strftime("%A, %B %d, %Y at %I:%M %p")
        hidden_context = f"{context_prompt}\n\n[System Info: The current date and time is {current_time_str}]\n\n[New Message]: {prompt_text}"
        parts.append(types.Part.from_text(text=hidden_context))
    if file_bytes and mime_type:
        parts.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
        
    message = types.Content(role="user", parts=parts)
    
    full_output = []
    # Use the actual session_id to maintain consistency
    async for event in runner.run_async(user_id="streamlit_user", session_id=session_id, new_message=message):
        if event.author and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    # Format sub-agents as blockquotes
                    if event.author != "ChiefOfStaff":
                        formatted_text = part.text.replace("\n", "\n> ")
                        chunk = f"> **{event.author}**:\n> {formatted_text}"
                    else:
                        chunk = part.text
                    
                    full_output.append(chunk)
                    if placeholder:
                        placeholder.markdown("\n\n".join(full_output) + " ▌")
                        
    if placeholder:
        placeholder.markdown("\n\n".join(full_output))
        
    return "\n\n".join(full_output)

def run_agent_in_isolated_thread(prompt_text, session_id, file_bytes=None, mime_type=None, placeholder=None):
    import threading
    from streamlit.runtime.scriptrunner import add_script_run_ctx
    result = []
    exc = []
    
    def target():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(get_agent_response(prompt_text, session_id, file_bytes, mime_type, placeholder))
            result.append(res)
            loop.close()
        except Exception as e:
            exc.append(e)
            
    thread = threading.Thread(target=target)
    add_script_run_ctx(thread)
    thread.start()
    thread.join()
    
    if exc:
        raise exc[0]
    return result[0]

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
    histories = list_chat_histories()
    if histories:
        st.session_state.session_id = histories[0][0]
    else:
        st.session_state.session_id = str(uuid.uuid4())

# --- Auto-Refresh & Alerts Checker ---
# Trigger page refresh every 2 minutes to scan for background alerts if enabled
if st.session_state.get("enable_autorefresh", True) and not st.session_state.get("agent_running"):
    st_autorefresh(interval=120000, key="alerts_refresher")

# Check database for pending voice alerts generated by background scheduler
pending_alert = get_pending_voice_alert()
if pending_alert:
    alert_id, alert_text, audio_bytes = pending_alert
    
    # Render autoplay hidden audio element
    b64_audio = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(audio_html, height=0, width=0)
    
    # Determine the speaking agent's avatar based on text content
    speaker_avatar = "🧘" if "Coach" in alert_text or "coach" in alert_text.lower() else "👔"
    
    # Inject voice alert directly into chat history so it displays visually
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    st.session_state.messages.append({
        "role": "assistant",
        "avatar": speaker_avatar,
        "content": f"📢 **Voice Alert**: {alert_text}",
        "audio_bytes": audio_bytes,
        "id": f"alert_{alert_id}"
    })
    
    # Save session state history and mark alert as played
    save_chat_history(st.session_state.session_id, st.session_state.messages)
    mark_voice_alert_played(alert_id)

# Check for manually triggered test voice alerts
if "test_voice_bytes" in st.session_state and st.session_state.test_voice_bytes:
    t_bytes = st.session_state.test_voice_bytes
    t_text = st.session_state.get("test_voice_text", "Gentle reminder!")
    
    # Render autoplay hidden audio element
    b64_audio = base64.b64encode(t_bytes).decode()
    audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(audio_html, height=0, width=0)
    
    # Inject test voice alert directly into chat history
    speaker_avatar = "🧘" if "Coach" in t_text or "coach" in t_text.lower() else "👔"
    st.session_state.messages.append({
        "role": "assistant",
        "avatar": speaker_avatar,
        "content": f"📢 **Test Voice Alert**: {t_text}",
        "audio_bytes": t_bytes,
        "id": f"test_alert_{int(time.time())}"
    })
    
    # Clear test bytes and save chat
    st.session_state.test_voice_bytes = None
    st.session_state.test_voice_text = None
    save_chat_history(st.session_state.session_id, st.session_state.messages)



# --- Sidebar: Multi-Modal Hub & Avatar ---
with st.sidebar:
    avatar_placeholder = st.empty()
    if avatar_b64:
        avatar_placeholder.markdown(f'<img src="data:image/png;base64,{avatar_b64}" class="avatar-idle">', unsafe_allow_html=True)
        
    # Demo Mode Warning Banner
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        st.warning("🛡️ **Demo Mode Active**\n(Mock data is enabled to protect private calendars/emails)")

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
        
    st.markdown("---")
    st.header("⚙️ Settings")
    enable_voice = st.checkbox("Enable voice synthesis (can add 5-10s delay)", value=False, key="enable_voice_synthesis")
    enable_refresh = st.checkbox("Auto-refresh alerts (every 2 min)", value=True, key="enable_autorefresh")
    
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

    st.markdown("---")
    with st.expander("⏰ Reminders Center"):
        st.write("#### Add Reminder")
        rem_text = st.text_input("Reminder Message", value="Be present and step out of the rabbit hole.", key="rem_input_text")
        rem_freq = st.selectbox("Frequency", ["Hourly", "Daily", "Weekly", "Monthly"], key="rem_input_freq")
        rem_chan = st.selectbox("Alert Channel", ["Voice Alert", "Email", "Both"], key="rem_input_chan")
        rem_agent = st.selectbox("Voice Tone / Agent", ["ExecutiveCoach", "ChiefOfStaff"], key="rem_input_agent")
        
        rem_time = None
        rem_dow = None
        rem_dom = None
        
        if rem_freq in ["Daily", "Weekly", "Monthly"]:
            rem_time = st.text_input("Time of Day (HH:MM)", value="09:00", key="rem_input_time")
        if rem_freq == "Weekly":
            rem_dow = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], key="rem_input_dow")
        if rem_freq == "Monthly":
            rem_dom = st.number_input("Day of Month (1-31)", min_value=1, max_value=31, value=1, key="rem_input_dom")
            
        if st.button("➕ Schedule Reminder", use_container_width=True, key="rem_add_btn"):
            chan_map = {"Voice Alert": "voice", "Email": "email", "Both": "both"}
            res = create_reminder(
                text=rem_text,
                frequency=rem_freq.lower(),
                channel=chan_map[rem_chan],
                time_of_day=rem_time,
                day_of_week=rem_dow,
                day_of_month=rem_dom,
                tone_agent=rem_agent
            )
            st.success(res)
            st.rerun()
            
        st.markdown("---")
        st.write("#### Active Reminders")
        import sqlite3
        from reminder_tools import DB_PATH
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reminders")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                st.caption("No reminders set yet.")
            else:
                for row in rows:
                    details = []
                    if row['time_of_day']:
                        details.append(f"at {row['time_of_day']}")
                    if row['day_of_week']:
                        details.append(f"on {row['day_of_week']}")
                    if row['day_of_month']:
                        details.append(f"on day {row['day_of_month']}")
                    det_str = " " + " ".join(details) if details else ""
                    
                    st.write(f"**{row['text']}**")
                    st.caption(f"_{row['frequency'].capitalize()}{det_str} via {row['channel']} ({row['tone_agent']})_")
                    
                    # Columns for Actions
                    c1, c2, c3 = st.columns([2, 2.5, 3])
                    with c1:
                        is_act = (row['is_active'] == 1)
                        new_act = st.checkbox("Active", value=is_act, key=f"active_{row['id']}")
                        if new_act != is_act:
                            toggle_reminder(row['id'], new_act)
                            st.rerun()
                    with c2:
                        if st.button("🗑️ Del", key=f"del_{row['id']}", use_container_width=True):
                            delete_reminder(row['id'])
                            st.rerun()
                    with c3:
                        if st.button("📢 Test", key=f"test_{row['id']}", use_container_width=True):
                            from voice_tools import generate_agent_voice
                            async def run_test():
                                from scheduler import generate_email_message, generate_voice_message
                                if row['channel'] in ['email', 'both']:
                                    body = await generate_email_message(row['text'], row['tone_agent'])
                                    from workspace_tools import send_email
                                    send_email(to_email='me', subject=f"[TEST] Check-in from {row['tone_agent']}", body=body)
                                if row['channel'] in ['voice', 'both']:
                                    voice_txt = await generate_voice_message(row['text'], row['tone_agent'])
                                    st.session_state.test_voice_text = voice_txt
                                    aud_bytes = generate_agent_voice(voice_txt)
                                    st.session_state.test_voice_bytes = aud_bytes
                            
                            import asyncio
                            asyncio.run(run_test())
                            st.rerun()
        except Exception as e:
            st.error(f"Error loading reminders: {e}")

# --- Initialize/Sync Conversation Session History ---
if not st.session_state.get("agent_running"):
    disk_messages = load_chat_history(st.session_state.session_id)
    if disk_messages:
        st.session_state.messages = disk_messages
    else:
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
    with st.chat_message(msg["role"], avatar=msg.get("avatar", "👤")):
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
            col_spacer, col1, col2, col3 = st.columns([4, 1.5, 2.5, 1.5])
            msg_id = msg.get("id", str(uuid.uuid4())[:8]) # give it a pseudo id if none exists to prevent duplicate keys
            
            with col1:
                if msg.get("liked") or st.session_state.get(f"liked_{msg_id}"):
                    st.button("💖 Saved!", key=f"up_{msg_id}_done", type="primary", disabled=True)
                else:
                    if st.button("👍", key=f"up_{msg_id}"):
                        msg["liked"] = True
                        st.session_state[f"liked_{msg_id}"] = True
                        save_chat_history(st.session_state.session_id, st.session_state.messages)
                        store_memory("Agent Feedback", f"The user PREFERS this style of response: {content[:200]}...")
                        st.rerun()
            with col2:
                if msg.get("disliked") or st.session_state.get(f"disliked_{msg_id}"):
                    st.button("😢 Feedback Saved", key=f"down_{msg_id}_done", type="primary", disabled=True)
                else:
                    if st.button("👎", key=f"down_{msg_id}"):
                        msg["disliked"] = True
                        st.session_state[f"disliked_{msg_id}"] = True
                        save_chat_history(st.session_state.session_id, st.session_state.messages)
                        store_memory("Agent Feedback", f"The user DISLIKES this style of response. AVOID doing this: {content[:200]}...")
                        st.rerun()
            with col3:
                import base64
                b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                copy_html = f"""
                <html style="margin:0; padding:0; overflow:hidden;">
                <head>
                <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: transparent;
                    overflow: hidden;
                }}
                button {{
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #3a3a3a;
                    padding: 4px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 13px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    width: 100%;
                    height: 30px;
                    box-sizing: border-box;
                    justify-content: center;
                    transition: background-color 0.1s, border-color 0.1s;
                }}
                button:hover {{
                    background-color: #2a2a2a;
                    border-color: #5a5a5a;
                }}
                button:active {{
                    background-color: #333333;
                }}
                </style>
                </head>
                <body>
                <button id="copy-btn" onclick="copy()">📋 Copy</button>
                <script>
                function copy() {{
                    const text = atob("{b64_content}");
                    navigator.clipboard.writeText(text).then(() => {{
                        const btn = document.getElementById("copy-btn");
                        btn.innerHTML = "✅ Copied!";
                        setTimeout(() => {{
                            btn.innerHTML = "📋 Copy";
                        }}, 2000);
                    }}).catch(err => {{
                        const textArea = document.createElement("textarea");
                        textArea.value = text;
                        textArea.style.position = "fixed";
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        try {{
                            document.execCommand("copy");
                            const btn = document.getElementById("copy-btn");
                            btn.innerHTML = "✅ Copied!";
                            setTimeout(() => {{
                                btn.innerHTML = "📋 Copy";
                            }}, 2000);
                        }} catch (e) {{
                            console.error("Fallback copy failed", e);
                        }}
                        document.body.removeChild(textArea);
                    }});
                }}
                </script>
                </body>
                </html>
                """
                st.components.v1.html(copy_html, height=35)

# --- Get Input from either Chat or Sidebar Check-In ---
user_prompt = st.chat_input("Type your messy thought, or press Enter to just send your uploaded file/audio...")
pending_checkin = getattr(st.session_state, "pending_checkin", None)

if pending_checkin:
    user_prompt = pending_checkin
    st.session_state.pending_checkin = None

# --- PROCESS THE INPUT ---
if user_prompt:
    st.session_state.agent_running = True
    try:
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
        save_chat_history(st.session_state.session_id, st.session_state.messages)
        with st.chat_message("user", avatar="👤"):
            st.write(user_prompt)
            if has_file:
                st.caption("*(📎 Included an attachment)*")

        # 2. Trigger the Chief of Staff agent processing loop
        if avatar_b64:
            avatar_placeholder.markdown(f'<img src="data:image/png;base64,{avatar_b64}" class="avatar-speaking">', unsafe_allow_html=True)
            
        with st.spinner("CoS is building team consensus..."):
            try:
                # Use isolated thread to run the agent and stream outputs dynamically
                with st.chat_message("assistant", avatar="👔"):
                    message_placeholder = st.empty()
                    cos_response = run_agent_in_isolated_thread(
                        user_prompt, 
                        st.session_state.session_id, 
                        file_bytes, 
                        mime_type, 
                        placeholder=message_placeholder
                    )
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
                    import traceback
                    cos_response = f"**Error executing ADK workflow:**\n{e}\n\n```python\n{traceback.format_exc()}\n```"

        if avatar_b64:
            avatar_placeholder.markdown(f'<img src="data:image/png;base64,{avatar_b64}" class="avatar-idle">', unsafe_allow_html=True)

        # 3. Stream the agent result back to your screen
        audio_bytes = None
        if enable_voice and cos_response and "Error executing" not in cos_response:
            try:
                audio_bytes = generate_agent_voice(cos_response)
            except Exception as e:
                st.error(f"Failed to generate audio: {e}")

        st.session_state.messages.append({"role": "assistant", "avatar": "👔", "content": cos_response, "audio_bytes": audio_bytes, "id": str(uuid.uuid4())[:8]})
        save_chat_history(st.session_state.session_id, st.session_state.messages)
    finally:
        st.session_state.agent_running = False
        # Rerun the app to seamlessly render the new message through the persistent loop above
        st.rerun()
