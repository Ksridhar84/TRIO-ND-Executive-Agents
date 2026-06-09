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
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/presentations.readonly'
]

def authenticate_google_workspace() -> Credentials:
    """Authenticate with Google Workspace using OAuth 2.0.
    
    Returns:
        Credentials: The authenticated Google credentials.
    """
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

def read_gmail_inbox(max_results: int = 5) -> list[dict]:
    """Read the latest unread emails from the user's Gmail inbox.
    
    Args:
        max_results (int): The maximum number of emails to retrieve. Default is 5.
        
    Returns:
        list[dict]: A list of unread emails with sender, subject, and snippet.
    """
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

if __name__ == '__main__':
    print("Initiating Google Workspace First-Time User Handshake with expanded scopes...")
    creds = authenticate_google_workspace()
    print("Authentication successful! Token saved to 'token.json'.")
    print("Workspace Tools (Gmail, Calendar, Docs, Sheets, Slides) are fully integrated and ready to use.")
