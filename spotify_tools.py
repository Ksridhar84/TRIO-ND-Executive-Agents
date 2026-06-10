def recommend_spotify_playlist(mood: str) -> str:
    """Recommend a curated Spotify playlist based on the user's current mood, focus, or energy level.
    
    Args:
        mood (str): The desired mood or state (e.g., 'focus', 'adhd', 'high_energy', 'calm', 'brown_noise', 'lofi').
        
    Returns:
        str: A specially tagged string containing the Spotify embed URL that the dashboard will render.
    """
    mood_lower = mood.lower()
    
    playlists = {
        "focus": "37i9dQZF1DWZeKCadgRdKQ", # Deep Focus
        "adhd": "37i9dQZF1DXdfOcg1fm0VG", # Video Game Soundtracks (ADHD friendly)
        "lofi": "37i9dQZF1DWWQRwui0ExPn", # Official Lofi Beats
        "high_energy": "37i9dQZF1DXaXB8fQg7xif", # Dance Pop
        "calm": "37i9dQZF1DWZqd5JICZI0u", # Peaceful Meditation
        "brown_noise": "37i9dQZF1DX4hpoO8ggEto", # Brown Noise
    }
    
    # Default to ADHD Focus if not matched
    selected_id = playlists.get("adhd")
    
    if "focus" in mood_lower or "deep" in mood_lower:
        selected_id = playlists["focus"]
    elif "lofi" in mood_lower or "chill" in mood_lower:
        selected_id = playlists["lofi"]
    elif "energy" in mood_lower or "pump" in mood_lower or "dance" in mood_lower:
        selected_id = playlists["high_energy"]
    elif "calm" in mood_lower or "relax" in mood_lower or "peace" in mood_lower:
        selected_id = playlists["calm"]
    elif "noise" in mood_lower or "brown" in mood_lower or "pink" in mood_lower:
        selected_id = playlists["brown_noise"]
        
    playlist_url = f"https://open.spotify.com/playlist/{selected_id}"
    
    return f"Here is the Spotify Playlist link: [🎧 Open Spotify Playlist]({playlist_url})"
