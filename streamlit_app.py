# Streamlit Community Cloud Entry Point
# This redirects the execution to dashboard.py

import streamlit as st
import os

# Map Streamlit secrets to environment variables for cloud deployment
try:
    if hasattr(st, "secrets"):
        for key in st.secrets:
            os.environ[key] = str(st.secrets[key])
except Exception:
    pass

with open("dashboard.py", "r", encoding="utf-8") as f:
    code = compile(f.read(), "dashboard.py", "exec")
    exec(code, globals())
