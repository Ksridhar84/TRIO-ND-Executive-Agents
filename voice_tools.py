import io
from gtts import gTTS

def generate_agent_voice(text: str) -> bytes:
    """Generate audio bytes from text using Google TTS.
    
    Args:
        text (str): The text response to convert to speech.
        
    Returns:
        bytes: MP3 audio bytes.
    """
    # Clean text to avoid reading markdown symbols awkwardly
    clean_text = text.replace("*", "").replace("#", "").replace(">", "").strip()
    
    # Generate speech
    tts = gTTS(text=clean_text, lang='en', slow=False)
    
    # Save to in-memory bytes buffer
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    
    return fp.read()
