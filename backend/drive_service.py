import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from fastapi import HTTPException
from config import GOOGLE_DRIVE_FOLDER_ID

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Initializes and returns the Google Drive API service using OAuth 2.0."""
    creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    
    if not os.path.exists(creds_path):
        raise HTTPException(status_code=500, detail="Google Drive credentials.json not found on server.")
    
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            # This requires a local browser and blocks until authenticated
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to authenticate with Google Drive: {str(e)}")

def upload_to_drive(file_bytes: bytes, filename: str, mime_type: str = 'application/pdf') -> str:
    """Uploads a file to Google Drive and returns the file ID."""
    service = get_drive_service()
    
    # Check if a folder ID is set in the environment
    folder_id = GOOGLE_DRIVE_FOLDER_ID
    
    file_metadata = {'name': filename}
    if folder_id:
        file_metadata['parents'] = [folder_id]
        
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)
    
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to Google Drive: {str(e)}")

def download_from_drive(file_id: str) -> io.BytesIO:
    """Downloads a file from Google Drive and returns it as a BytesIO stream."""
    service = get_drive_service()
    try:
        request = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to download file from Google Drive: {str(e)}")

def delete_from_drive(file_id: str):
    """Deletes a file from Google Drive."""
    service = get_drive_service()
    try:
        service.files().delete(fileId=file_id).execute()
    except Exception as e:
        print(f"Warning: Failed to delete file {file_id} from Google Drive: {str(e)}")
