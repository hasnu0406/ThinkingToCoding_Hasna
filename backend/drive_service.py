import os
import io
from typing import Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from fastapi import HTTPException
from utils import logger
from config import GOOGLE_DRIVE_FOLDER_ID

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Initializes and returns the Google Drive API service."""
    from google.oauth2 import service_account
    
    # 1. Industry Standard: Try Service Account First (Server-to-Server Auth)
    service_account_path = os.path.join(os.path.dirname(__file__), 'service_account.json')
    if os.path.exists(service_account_path):
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES
        )
        try:
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to authenticate via Service Account: {str(e)}")

    # 2. Fallback: Local OAuth Token
    creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    
    if not os.path.exists(creds_path):
        raise HTTPException(status_code=500, detail="Google Drive credentials not found. Provide service_account.json or credentials.json.")
    
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception:
                raise HTTPException(status_code=401, detail="Google Drive token expired. Please run 'python authenticate_google.py' on the server to re-authenticate.")
        else:
            raise HTTPException(status_code=401, detail="Google Drive authentication required. Please run 'python authenticate_google.py' on the server.")

    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except RefreshError as e:
        raise HTTPException(status_code=401, detail="Google Drive authentication expired. Please run 'python authenticate_google.py'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to authenticate with Google Drive: {str(e)}")

def upload_to_drive(file_bytes: bytes, filename: str, mime_type: str = 'application/pdf', convert_to_doc: bool = False) -> dict[str, Any]:
    """
    Uploads a file to Google Drive.
    If convert_to_doc is True (for DOCX/DOC/TXT), Google Drive automatically converts it into
    a Google Doc preserving all original formatting, fonts, spacing, tables, and hyperlinks.
    """
    service = get_drive_service()
    
    # Check if a folder ID is set in the environment
    folder_id = GOOGLE_DRIVE_FOLDER_ID
    
    file_metadata = {'name': filename}
    if folder_id:
        file_metadata['parents'] = [folder_id]
        
    if convert_to_doc:
        file_metadata['mimeType'] = 'application/vnd.google-apps.document'
        
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, mimeType, name'
        ).execute()
        return {
            "id": file.get('id'),
            "web_view_link": file.get('webViewLink'),
            "mime_type": file.get('mimeType'),
            "name": file.get('name')
        }
    except HttpError as e:
        raise HTTPException(status_code=502, detail=f"Google Drive API error during upload: {e.reason}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during upload: {str(e)}")

def download_from_drive(file_id: str) -> io.BytesIO:
    """
    Downloads a file from Google Drive as a PDF stream.
    If the file is a Google Doc (converted from DOCX/Word/TXT), it uses Google Drive's
    native files.export API to render a pixel-perfect PDF with full layout, fonts,
    spacing, and clickable hyperlinks intact.
    """
    service = get_drive_service()
    try:
        file_meta = service.files().get(fileId=file_id, fields='mimeType, name').execute()
        mime_type = file_meta.get('mimeType', '')
        
        if mime_type == 'application/vnd.google-apps.document':
            # Export Google Doc as a formatted PDF
            request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
        else:
            # Standard PDF / binary download
            request = service.files().get_media(fileId=file_id)
            
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream
    except HttpError as e:
        if e.resp.status == 404:
            raise HTTPException(status_code=404, detail="File not found in Google Drive.")
        raise HTTPException(status_code=502, detail=f"Google Drive API error during download: {e.reason}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during download: {str(e)}")

def delete_from_drive(file_id: str):
    """Deletes a file from Google Drive."""
    service = get_drive_service()
    try:
        service.files().delete(fileId=file_id).execute()
    except HttpError as e:
        logger.warning(f"Warning: Google Drive API error deleting file {file_id}: {e.reason}")
    except Exception as e:
        logger.warning(f"Warning: Unexpected error deleting file {file_id}: {str(e)}")
