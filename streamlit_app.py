# Streamlit Community Cloud Entry Point
# This redirects the execution to dashboard.py

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
except Exception as e:
    print(f"Error mapping secrets: {e}")

with open("dashboard.py", "r", encoding="utf-8") as f:
    code = compile(f.read(), "dashboard.py", "exec")
    exec(code, globals())
