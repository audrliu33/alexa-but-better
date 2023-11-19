import google.auth

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import openai


# Function to authenticate and create a Gmail API service
def gmail_authenticate():
    creds = None
    # token.pickle stores the user's credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no valid credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', 
                scopes=['https://www.googleapis.com/auth/gmail.readonly']
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


# Function to read emails
def get_emails(service, user_id='me'):
    # Call the Gmail API
    results = service.users().messages().list(userId=user_id, labelIds=['INBOX']).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return
    print("Message snippets:")
    for message in messages:
        msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
        print(msg['snippet'])


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
def analyze_email(content):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=content,
      max_tokens=50
    )
    return response.choices[0].text.strip()



# Main logic
def main():
    service = gmail_authenticate()
    # Read emails
    # Analyze with OpenAI API
    # Send responses or perform actions

if __name__ == "__main__":
    main()
