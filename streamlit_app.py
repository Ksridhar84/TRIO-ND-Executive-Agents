# Streamlit Community Cloud Entry Point
# This redirects the execution to dashboard.py

with open("dashboard.py", "r", encoding="utf-8") as f:
    code = compile(f.read(), "dashboard.py", "exec")
    exec(code, globals())
