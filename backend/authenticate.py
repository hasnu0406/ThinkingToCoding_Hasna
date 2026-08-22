import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    
    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found.")
        return
        
    print("Starting Google Drive Authentication...")
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
        
    print(f"Successfully authenticated! Token saved to {token_path}")

if __name__ == '__main__':
    authenticate()
