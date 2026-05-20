import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# The scope needed to create and modify calendar events
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def generate_token():
    """
    Runs the OAuth 2.0 flow to authenticate the user.
    Requires a 'credentials.json' file downloaded from Google Cloud Console.
    It will pop open your web browser, ask you to log in, and save a 'token.json' file.
    """
    creds = None
    
    # Check if we already have a token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        print("token.json already exists!")
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("\n[ERROR] credentials.json is missing!")
                print("1. Go to Google Cloud Console (console.cloud.google.com)")
                print("2. Enable the Google Calendar API")
                print("3. Go to APIs & Services > Credentials")
                print("4. Create OAuth client ID (Desktop Application)")
                print("5. Download JSON, rename to credentials.json, and place it in this folder.")
                return
                
            print("Starting browser OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("\n✅ Successfully generated token.json! The Django app can now create Calendar events.")

if __name__ == '__main__':
    generate_token()
