import os
from google.adk.tools import McpToolset
from mcp import StdioServerParameters
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Streamlit Community Cloud secret mapping helper
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        for key in st.secrets:
            if key not in os.environ:
                os.environ[key] = str(st.secrets[key])
except Exception:
    pass

# Retrieve GitLab configuration parameters (allow fallback for GITLAB_PERSONAL_ACCESS_TOKEN)
gitlab_token = os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PERSONAL_ACCESS_TOKEN")
if gitlab_token:
    gitlab_token = gitlab_token.strip()
    
gitlab_project_id = os.environ.get("GITLAB_PROJECT_ID")
if gitlab_project_id:
    gitlab_project_id = gitlab_project_id.strip()

gitlab_mcp_client = None

if not gitlab_token or not gitlab_project_id:
    print(
        "WARNING: GITLAB_TOKEN (or GITLAB_PERSONAL_ACCESS_TOKEN) and GITLAB_PROJECT_ID "
        "environment variables must be defined to initialize the GitLab MCP server. "
        "Proceeding without GitLab integration."
    )
else:
    # Configure the connection parameters using Stdio transport to run npx.
    # We map GITLAB_PERSONAL_ACCESS_TOKEN as required by the official GitLab MCP server.
    connection_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-gitlab"],
        env={
            **os.environ,
            "GITLAB_TOKEN": gitlab_token,
            "GITLAB_PERSONAL_ACCESS_TOKEN": gitlab_token,
            "GITLAB_PROJECT_ID": gitlab_project_id,
        }
    )

    # Initialize the McpToolset as a client to retrieve and register all tools from the GitLab MCP server
    gitlab_mcp_client = McpToolset(
        connection_params=connection_params,
        use_mcp_resources=False  # Disable resources since the GitLab MCP server does not support resource listing
    )

# Compatibility alias
gitlab_mcp_toolset = gitlab_mcp_client
