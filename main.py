import time
import google.auth

import os
from dotenv import load_dotenv
load_dotenv()

import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import openai
from openai import OpenAI

# Assistant Function: High Level Browse
browse = {
    "name": "highLevelBrowse",
    "description": "Browse the web using natural language instructions. This tool enables control over web browsers to fetch and interact with web content.",
    "parameters": {
        "type": "object",
        "properties": {
            "instruction": {"type": "string", "description": "Detailed natural language instruction for browsing."},
            "url": {"type": "string", "description": "Optional starting URL for the browsing session."}
        },
        "required": ["instruction"]
    }
}


# Function to authenticate and create a Gmail API service
def gmail_authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                scopes=[
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.compose'
                ]
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


# Function to read emails
def get_emails(service, user_id='me'):
    # Call the Gmail API
    results = service.users().messages().list(userId=user_id, labelIds=['INBOX'], maxResults=1).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return None
    else:
        message = messages[0]
        full_email = service.users().messages().get(userId=user_id, id=message['id'], format='full').execute()

        headers = full_email['payload']['headers']
        sender = next(header['value'] for header in headers if header['name'] == 'From')
        subject = next(header['value'] for header in headers if header['name'] == 'Subject')

        # Handle different types of email payloads
        if 'parts' in full_email['payload']:
            # Multipart email, could be mixed, alternative, related, etc.
            part = full_email['payload']['parts'][0]
            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        else:
            # Simple email, usually plain text or HTML
            body = base64.urlsafe_b64decode(full_email['payload']['body']['data']).decode('utf-8')

        return sender, subject, body, full_email


# Function to send emails
def send_email(service, user_id, destination, subject, body):
    message = MIMEMultipart()
    message['to'] = destination
    message['subject'] = subject
    msg = MIMEText(body)
    message.attach(msg)

    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}

    try:
        message = (service.users().messages().send(userId=user_id, body=body).execute())
        print('Message Id: %s' % message['id'])
        return message
    except Exception as error:
        print(f'An error occurred: {error}')


# Function to analyze email with OpenAI API
def analyze_email(email):
    # Create an Assistant with the MultiOn Browse API
    # assistant = client.beta.assistants.create(
    #     instructions="You are an assistant with the capability to browse the web. Use the MultiOn browser to assist users in fetching and interacting with web content.",
    #     model="gpt-4-1106-preview",  
    #     tools=[{
    #         "type": "function",
    #         "function": browse
    #     }]
    # )

    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
 
    # Create a Thread with the initial user message
    thread = openai.beta.threads.create(
        messages=[{
            "role": "user",
            "content": email
        }]
    )
 
    # Run the Assistant on the Thread
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Wait for run to complete
    # success if run.status == "completed"
    # failure if run.status == "failed", "cancelled", or "expired"
    # wait 1 second between checks
    while run.status != "completed":
        if run.status == "failed" or run.status == "cancelled" or run.status == "expired":
            return "An error occurred while analyzing the email."
        time.sleep(1)
        run = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    # Retrieve the latest message from the Thread
    response = openai.beta.threads.messages.list(
        thread_id=thread.id,
        limit=1,
        order='asc',
    )
 
    return response.data[0].content


# Main logic
def main():
    service = gmail_authenticate()

    # Read the most recent email and get its details
    print("Reading the most recent email...")
    sender, subject, body, full_email = get_emails(service)
    print(f"Sender: {sender}")
    print(f"Subject: {subject}")

    # Analyze email content with OpenAI (optional, based on your requirement)
    print("Analyzing email content...")
    analysis = analyze_email(body)
    print(f"Analysis: {analysis}")

    # send a text message to the sender with the analysis

    # Send a test email (you can replace this with a real recipient and content)
    # print("Sending a test email...")
    # test_email_content = "This is a test email from My Executive Assistant."
    # send_email(service, 'me', 'omiiyamu@gmail.com', 'Test Email from MEA', test_email_content)

    print("All tests completed.")

if __name__ == "__main__":
    main()
