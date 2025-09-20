"""Gmail API helpers."""

from __future__ import annotations

import base64
import email
from typing import Iterable, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import Settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailClient:
    """Wrapper around the Gmail REST API."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._service = self._build_service(settings)

    @staticmethod
    def _build_service(settings: Settings):
        creds: Optional[Credentials] = None
        if settings.gmail_token_file.exists():
            creds = Credentials.from_authorized_user_file(str(settings.gmail_token_file), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(settings.google_client_secret_file), SCOPES)
                creds = flow.run_local_server(port=0)
            settings.gmail_token_file.write_text(creds.to_json())
        return build("gmail", "v1", credentials=creds)

    def list_messages(self, query: str | None = None, max_results: int = 10) -> list[dict]:
        response = (
            self._service.users()
            .messages()
            .list(userId=self._settings.gmail_user_id, q=query, maxResults=max_results)
            .execute()
        )
        return response.get("messages", [])

    def get_message(self, message_id: str) -> dict:
        return (
            self._service.users()
            .messages()
            .get(userId=self._settings.gmail_user_id, id=message_id, format="full")
            .execute()
        )

    def send_message(self, to: str, subject: str, body: str) -> dict:
        message = email.message.EmailMessage()
        message["To"] = to
        message["From"] = self._settings.gmail_user_id
        message["Subject"] = subject
        message.set_content(body)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return (
            self._service.users()
            .messages()
            .send(userId=self._settings.gmail_user_id, body={"raw": encoded_message})
            .execute()
        )

    @staticmethod
    def extract_text_payload(parts: Iterable[dict]) -> str:
        """Extract the first text/plain payload from the Gmail API message parts."""

        for part in parts:
            mime_type = part.get("mimeType")
            if mime_type == "text/plain" and "data" in part.get("body", {}):
                data = part["body"]["data"]
                decoded = base64.urlsafe_b64decode(data.encode()).decode()
                return decoded
            if part.get("parts"):
                nested = GmailClient.extract_text_payload(part["parts"])
                if nested:
                    return nested
        return ""
