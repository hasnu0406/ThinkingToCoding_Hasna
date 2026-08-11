from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        SCOPES
    )
    # open_browser=True requires a desktop session
    creds = flow.run_local_server(port=0, open_browser=True)
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    print("Authentication Successful! You may close this window and return to VS Code.")

if __name__ == "__main__":
    authenticate()
