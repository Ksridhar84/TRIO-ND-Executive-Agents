import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.message import EmailMessage

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/presentations.readonly'
]

def authenticate_google_workspace() -> Credentials:
    """Authenticate with Google Workspace using OAuth 2.0.
    
    Returns:
        Credentials: The authenticated Google credentials.
    """
    # Write credentials.json and token.json from env vars if they exist but aren't on disk (for cloud deployment)
    if not os.path.exists('token.json'):
        token_env = os.environ.get('GOOGLE_TOKEN_JSON')
        if token_env:
            with open('token.json', 'w') as f:
                f.write(token_env)
                
    if not os.path.exists('credentials.json'):
        creds_env = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_env:
            with open('credentials.json', 'w') as f:
                f.write(creds_env)

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("The 'credentials.json' file is missing. Please download it from your Google Cloud Console and place it in the project directory.")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def read_gmail_inbox(max_results: int = 50) -> list[dict]:
    """Read the latest unread emails from the user's Gmail inbox.
    
    Args:
        max_results (int): The maximum number of emails to retrieve. Default is 50.
        
    Returns:
        list[dict]: A list of unread emails with sender, subject, and snippet.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        return [
            {
                "id": "mock_email_1",
                "sender": "CEO / Board President <president@company.com>",
                "subject": "Urgent: Project Pitch Slide Review required by tomorrow 9 AM",
                "snippet": "Hi, please make sure you review the slides for the pitch tomorrow. We need to finalize the cloud migration architecture slides before the presentation."
            },
            {
                "id": "mock_email_2",
                "sender": "HR Team <hr@company.com>",
                "subject": "Action Needed: Complete quarterly health wellness survey",
                "snippet": "Hello, this is a reminder to complete your quarterly survey. We value your feedback on burnout prevention and wellness."
            },
            {
                "id": "mock_email_3",
                "sender": "Partner <partner@household.org>",
                "subject": "Household Quests: chore list updated",
                "snippet": "Hey, I added the grocery shopping and trash disposal chores to our Notion shared page. Let's finish them tonight."
            }
        ]
    try:
        creds = authenticate_google_workspace()
        service = build('gmail', 'v1', credentials=creds)

        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=max_results).execute()
        messages = results.get('messages', [])

        if not messages:
            return [{"status": "No new unread messages found in the inbox."}]

        email_data = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
            headers = msg.get('payload', {}).get('headers', [])
            
            subject = "No Subject"
            sender = "Unknown Sender"
            
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                if header['name'] == 'From':
                    sender = header['value']
                    
            email_data.append({
                "id": message['id'],
                "sender": sender,
                "subject": subject,
                "snippet": msg.get('snippet', '')
            })
            
        return email_data
    except Exception as e:
        return [{"error": f"Failed to fetch emails: {str(e)}"}]

def send_email(to_email: str, subject: str, body: str) -> dict:
    """Send an email from the user's Gmail account.
    
    Args:
        to_email (str): The email address of the recipient. If sending to yourself, use 'me'.
        subject (str): The subject line of the email.
        body (str): The main body text of the email.
        
    Returns:
        dict: Status message indicating success or failure.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        return {"status": "success", "message_id": "mock_email_send_id_12345"}
    try:
        creds = authenticate_google_workspace()
        service = build('gmail', 'v1', credentials=creds)

        if to_email.lower() == 'me':
            profile = service.users().getProfile(userId='me').execute()
            to_email = profile.get('emailAddress')

        message = EmailMessage()
        message.set_content(body)
        message['To'] = to_email
        message['From'] = 'me'
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return {"status": "success", "message_id": send_message['id']}
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}

def get_calendar_events(max_results: int = 5) -> list[dict]:
    """Get the upcoming events from the user's Google Calendar.
    
    Args:
        max_results (int): The maximum number of upcoming events to retrieve. Default is 5.
        
    Returns:
        list[dict]: A list of upcoming events with summary, start, and end times.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        today = datetime.date.today()
        return [
            {
                "summary": "Google Cloud Architecture Consulting Session",
                "start": f"{today}T10:00:00Z",
                "end": f"{today}T11:00:00Z",
                "link": "https://calendar.google.com/mock"
            },
            {
                "summary": "Client Data Migration Sync",
                "start": f"{today}T13:00:00Z",
                "end": f"{today}T14:00:00Z",
                "link": "https://calendar.google.com/mock"
            },
            {
                "summary": "Daily Wellness Coaching Check-In",
                "start": f"{today}T16:30:00Z",
                "end": f"{today}T17:00:00Z",
                "link": "https://calendar.google.com/mock"
            }
        ]
    try:
        creds = authenticate_google_workspace()
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=max_results, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            return [{"status": "No upcoming events found."}]

        event_data = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            event_data.append({
                "summary": event.get('summary', 'No Title'),
                "start": start,
                "end": end,
                "link": event.get('htmlLink', '')
            })
            
        return event_data
    except Exception as e:
        return [{"error": f"Failed to fetch calendar events: {str(e)}"}]

def read_google_doc(document_id: str) -> str:
    """Extract all text from a Google Document.
    
    Args:
        document_id (str): The ID of the Google Doc (found in the URL).
        
    Returns:
        str: The full text content of the document.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        return "This is a mock Google Doc content. It contains summary points for the consulting project details."
    try:
        creds = authenticate_google_workspace()
        service = build('docs', 'v1', credentials=creds)
        
        document = service.documents().get(documentId=document_id).execute()
        content = document.get('body').get('content')
        text = ""
        for value in content:
            if 'paragraph' in value:
                elements = value.get('paragraph').get('elements')
                for elem in elements:
                    text_run = elem.get('textRun')
                    if text_run:
                        text += text_run.get('content')
        return text if text else "Document is empty."
    except Exception as e:
        return f"Error reading Google Doc: {str(e)}"

def read_google_sheet(spreadsheet_id: str, range_name: str) -> list[list]:
    """Extract rows of data from a Google Sheet.
    
    Args:
        spreadsheet_id (str): The ID of the Google Sheet.
        range_name (str): The A1 notation of the range to retrieve (e.g., 'Sheet1!A1:D10').
        
    Returns:
        list[list]: The rows of data from the sheet.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        return [["Header 1", "Header 2"], ["Row 1 Col 1", "Row 1 Col 2"], ["Row 2 Col 1", "Row 2 Col 2"]]
    try:
        creds = authenticate_google_workspace()
        service = build('sheets', 'v4', credentials=creds)
        
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        if not values:
            return [["No data found."]]
        return values
    except Exception as e:
        return [[f"Error reading Google Sheet: {str(e)}"]]

def read_google_slide(presentation_id: str) -> str:
    """Extract text from a Google Slides presentation.
    
    Args:
        presentation_id (str): The ID of the Google Slide presentation.
        
    Returns:
        str: The extracted text from the slides.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        return "\n--- Slide 1 ---\nTitle: Pitch Presentation\n\n--- Slide 2 ---\nContent: Enterprise Cloud Architecture Overview"
    try:
        creds = authenticate_google_workspace()
        service = build('slides', 'v1', credentials=creds)
        
        presentation = service.presentations().get(presentationId=presentation_id).execute()
        slides = presentation.get('slides')
        
        text = ""
        for i, slide in enumerate(slides):
            text += f"\\n--- Slide {i + 1} ---\\n"
            for element in slide.get('pageElements'):
                if 'shape' in element and 'text' in element.get('shape'):
                    text_elements = element.get('shape').get('text').get('textElements')
                    for te in text_elements:
                        if 'textRun' in te:
                            text += te.get('textRun').get('content')
        return text if text else "Presentation is empty."
    except Exception as e:
        return f"Error reading Google Slides: {str(e)}"

def create_calendar_event(summary: str, start_time: str, end_time: str, description: str = "") -> dict:
    """Create a new event on the user's primary Google Calendar.
    
    Args:
        summary (str): The title of the event.
        start_time (str): ISO 8601 formatted start time (e.g., '2026-06-10T10:00:00-04:00').
        end_time (str): ISO 8601 formatted end time (e.g., '2026-06-10T11:00:00-04:00').
        description (str): Description or notes for the event. Default is empty.
        
    Returns:
        dict: Status message with event link.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        return {"status": "success", "event_link": "https://calendar.google.com/mock-event-link"}
    try:
        creds = authenticate_google_workspace()
        service = build('calendar', 'v3', credentials=creds)
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return {"status": "success", "event_link": created_event.get('htmlLink')}
    except Exception as e:
        return {"error": f"Failed to create calendar event: {str(e)}"}

def create_google_doc(title: str, text_content: str) -> dict:
    """Create a new Google Document and insert text content into it.
    
    Args:
        title (str): The title of the new document.
        text_content (str): The text to insert into the document body.
        
    Returns:
        dict: Status message with the document ID.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        return {"status": "success", "document_id": "mock_doc_id_9999", "document_link": "https://docs.google.com/document/d/mock-doc/edit"}
    try:
        creds = authenticate_google_workspace()
        service = build('docs', 'v1', credentials=creds)
        
        # Create the blank document
        document = service.documents().create(body={'title': title}).execute()
        doc_id = document.get('documentId')
        
        # Insert the text content
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': text_content
                }
            }
        ]
        
        service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        
        return {"status": "success", "document_id": doc_id, "document_link": f"https://docs.google.com/document/d/{doc_id}/edit"}
    except Exception as e:
        return {"error": f"Failed to create Google Doc: {str(e)}"}

def get_gmail_message_details(message_id: str) -> dict:
    """Retrieve the full body and metadata of a specific Gmail email, along with any attachment details.
    
    Args:
        message_id (str): The ID of the Gmail message to retrieve.
        
    Returns:
        dict: A dictionary containing subject, sender, date, body, and a list of attachments (name, mimeType, size, attachmentId).
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        return {
            "id": message_id,
            "sender": "CEO / Board President <president@company.com>",
            "subject": "Urgent: Project Pitch Slide Review required by tomorrow 9 AM",
            "date": "2026-06-12",
            "body": "Hi, please review the attached PDF document containing the cloud migration architecture summary. We need to finalize the pitch slides based on these insights before tomorrow morning. Let me know if you spot any issues.",
            "attachments": [
                {
                    "filename": "cloud_migration_summary.pdf",
                    "mimeType": "application/pdf",
                    "size": 15000,
                    "attachmentId": "mock_attach_id_1"
                }
            ]
        }
    try:
        creds = authenticate_google_workspace()
        service = build('gmail', 'v1', credentials=creds)
        
        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = "No Subject"
        sender = "Unknown Sender"
        date = "Unknown Date"
        for h in headers:
            if h['name'] == 'Subject':
                subject = h['value']
            elif h['name'] == 'From':
                sender = h['value']
            elif h['name'] == 'Date':
                date = h['value']
                
        body = ""
        attachments = []
        
        def parse_parts(parts):
            nonlocal body
            for part in parts:
                mime_type = part.get('mimeType')
                filename = part.get('filename')
                body_data = part.get('body', {})
                
                # Check for attachment
                if filename and body_data.get('attachmentId'):
                    attachments.append({
                        "filename": filename,
                        "mimeType": mime_type,
                        "size": body_data.get('size'),
                        "attachmentId": body_data.get('attachmentId')
                    })
                # Check for body text
                elif mime_type == 'text/plain' and 'data' in body_data:
                    body += base64.urlsafe_b64decode(body_data['data']).decode('utf-8', errors='ignore')
                elif mime_type == 'text/html' and 'data' in body_data and not body:
                    html_content = base64.urlsafe_b64decode(body_data['data']).decode('utf-8', errors='ignore')
                    import re
                    body += re.sub('<[^<]+?>', '', html_content)
                elif 'parts' in part:
                    parse_parts(part['parts'])
                    
        if 'parts' in payload:
            parse_parts(payload['parts'])
        else:
            body_data = payload.get('body', {})
            if 'data' in body_data:
                body = base64.urlsafe_b64decode(body_data['data']).decode('utf-8', errors='ignore')
                
        return {
            "id": message_id,
            "sender": sender,
            "subject": subject,
            "date": date,
            "body": body.strip(),
            "attachments": attachments
        }
    except Exception as e:
        return {"error": f"Failed to get email details: {str(e)}"}

def read_gmail_attachment(message_id: str, attachment_id: str, filename: str) -> str:
    """Retrieve and extract the text content of an email attachment from Gmail.
    
    Args:
        message_id (str): The ID of the Gmail message containing the attachment.
        attachment_id (str): The ID of the attachment to download.
        filename (str): The name of the file (to determine how to parse it).
        
    Returns:
        str: The extracted text content or a status message.
    """
    if os.environ.get("DEMO_MODE", "").lower() == "true":
        if filename.endswith(".pdf"):
            return (
                "--- PDF Attachment: cloud_migration_summary.pdf ---\n"
                "Cloud Migration Phase 1 Overview:\n"
                "- Goal: Migrate core databases to Google Cloud SQL (PostgreSQL).\n"
                "- Current database size: 1.2 TB.\n"
                "- Target migration date: June 30, 2026.\n"
                "- Risk: High network latency during initial seeding sync.\n"
                "- Recommendation: Use GCP Database Migration Service (DMS) with continuous CDC replication."
            )
        return f"--- Attachment Content for {filename} ---\nThis is mock attachment text content."
        
    try:
        creds = authenticate_google_workspace()
        service = build('gmail', 'v1', credentials=creds)
        
        attachment = service.users().messages().attachments().get(
            userId='me', messageId=message_id, id=attachment_id).execute()
        data = attachment.get('data')
        if not data:
            return "Error: Attachment contains no data."
            
        file_bytes = base64.urlsafe_b64decode(data)
        ext = filename.lower().split('.')[-1]
        
        if ext in ['txt', 'csv', 'tsv', 'json', 'md', 'xml', 'yaml', 'yml']:
            return file_bytes.decode('utf-8', errors='ignore')
        elif ext == 'pdf':
            try:
                import pypdf
                import io
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return f"--- PDF Content: {filename} ---\n" + (text.strip() if text else "PDF file contains no readable text.")
            except ImportError:
                return "Error: pypdf library is required to read PDF attachments."
            except Exception as e:
                return f"Error parsing PDF: {str(e)}"
        else:
            return f"Attachment '{filename}' (type: {ext}) is downloaded but not directly readable. Supported extensions for auto-reading: txt, csv, pdf, json, md, yaml."
    except Exception as e:
        return f"Error reading attachment: {str(e)}"

if __name__ == '__main__':
    print("Initiating Google Workspace First-Time User Handshake with expanded scopes...")
    creds = authenticate_google_workspace()
    print("Authentication successful! Token saved to 'token.json'.")
    print("Workspace Tools (Gmail, Calendar, Docs, Sheets, Slides) are fully integrated and ready to use.")
