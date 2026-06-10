import os
import json
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")

def _get_notion_client():
    if not NOTION_TOKEN:
        raise ValueError("NOTION_API_TOKEN is not set in the environment variables.")
    return Client(auth=NOTION_TOKEN)

def search_notion(query: str) -> str:
    """Searches the user's Notion workspace for pages and databases matching the query.
    
    Args:
        query (str): The search term to look for.
        
    Returns:
        str: A summary of the matching pages and their IDs.
    """
    try:
        notion = _get_notion_client()
        results = notion.search(query=query).get("results", [])
        
        if not results:
            return f"No pages or databases found in Notion matching '{query}'."
            
        output = [f"Found {len(results)} matching items in Notion:"]
        for item in results:
            title = "Untitled"
            if "title" in item and item["title"]:
                title = item["title"][0]["plain_text"]
            elif "properties" in item and "Name" in item["properties"] and item["properties"]["Name"]["title"]:
                title = item["properties"]["Name"]["title"][0]["plain_text"]
            elif "properties" in item and "title" in item["properties"] and item["properties"]["title"]["title"]:
                 title = item["properties"]["title"]["title"][0]["plain_text"]
            
            obj_type = item.get('object', 'unknown')
            url = item.get('url', '')
            item_id = item.get('id', '')
            output.append(f"- [{obj_type}] **{title}** (ID: {item_id})\n  Link: {url}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error searching Notion: {str(e)}"

def read_notion_page(page_id: str) -> str:
    """Reads the content blocks of a specific Notion page.
    
    Args:
        page_id (str): The ID of the Notion page to read.
        
    Returns:
        str: The extracted text content of the page.
    """
    try:
        notion = _get_notion_client()
        blocks = notion.blocks.children.list(block_id=page_id).get("results", [])
        
        if not blocks:
            return f"The Notion page {page_id} is empty or unreadable."
            
        content = []
        for block in blocks:
            block_type = block.get("type")
            if block_type and block_type in block:
                rich_text = block[block_type].get("rich_text", [])
                text_content = "".join([t.get("plain_text", "") for t in rich_text])
                if text_content:
                    if block_type == "heading_1":
                        content.append(f"# {text_content}")
                    elif block_type == "heading_2":
                        content.append(f"## {text_content}")
                    elif block_type == "heading_3":
                        content.append(f"### {text_content}")
                    elif block_type == "bulleted_list_item":
                        content.append(f"* {text_content}")
                    else:
                        content.append(text_content)
        
        return "\n".join(content) if content else "No readable text blocks found on this page."
    except Exception as e:
        return f"Error reading Notion page: {str(e)}"

def create_notion_page(title: str, content: str, parent_page_id: str) -> str:
    """Creates a new Notion page with the given title and content under a specific parent page.
    
    Args:
        title (str): The title of the new page.
        content (str): The markdown or text content to insert into the page.
        parent_page_id (str): The ID of the parent Notion page where this should be created.
        
    Returns:
        str: A success message with the new page URL, or an error.
    """
    try:
        notion = _get_notion_client()
        
        # Split content into paragraphs for simple block creation
        paragraphs = content.split("\n")
        children_blocks = []
        for p in paragraphs:
            if p.strip():
                children_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": p}}]
                    }
                })
        
        new_page = notion.pages.create(
            parent={"page_id": parent_page_id},
            properties={
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            },
            children=children_blocks
        )
        
        return f"Successfully created Notion page '{title}'.\nURL: {new_page.get('url')}"
    except Exception as e:
        return f"Error creating Notion page: {str(e)}"
