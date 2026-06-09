import asyncio
from mcp_config import gitlab_mcp_toolset

async def main():
    print("Connecting to GitLab MCP server and listing tools...")
    try:
        tools = await gitlab_mcp_toolset.get_tools()
        print(f"\nSuccess! Found {len(tools)} tools:")
        for t in tools:
            # We truncate description to keep console output clean
            desc = t.description.split('\n')[0] if t.description else 'No description'
            print(f"- {t.name}: {desc[:80]}")
    except Exception as e:
        print(f"\nError listing tools: {e}")

if __name__ == "__main__":
    asyncio.run(main())
