"""FastAPI application exposing Gmail and ChatGPT actions."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from .chatgpt_client import ChatGPTClient, ChatMessage
from .config import Settings, get_settings
from .gmail_client import GmailClient


class GmailMessage(BaseModel):
    id: str
    threadId: Optional[str] = None


class SummarizeRequest(BaseModel):
    message_id: str
    prompt: Optional[str] = None


class SummarizeResponse(BaseModel):
    message_id: str
    summary: str


class DraftEmail(BaseModel):
    to: str
    subject: str
    body: str


def create_app() -> FastAPI:
    app = FastAPI(title="Gmail MCP Service", version="0.1.0")

    def get_gmail_client(settings: Annotated[Settings, Depends(get_settings)]):
        return GmailClient(settings)

    def get_chatgpt_client(settings: Annotated[Settings, Depends(get_settings)]):
        return ChatGPTClient(settings)

    @app.get("/messages", response_model=list[GmailMessage])
    def list_messages(
        gmail_client: Annotated[GmailClient, Depends(get_gmail_client)],
        query: str | None = None,
        max_results: int = 10,
    ):
        messages = gmail_client.list_messages(query=query, max_results=max_results)
        return [GmailMessage(**message) for message in messages]

    @app.post("/summaries", response_model=SummarizeResponse)
    def summarize_message(
        payload: SummarizeRequest,
        gmail_client: Annotated[GmailClient, Depends(get_gmail_client)],
        chatgpt_client: Annotated[ChatGPTClient, Depends(get_chatgpt_client)],
    ):
        message = gmail_client.get_message(payload.message_id)
        if settings := get_settings().allowed_senders_list:
            headers = {header["name"].lower(): header["value"] for header in message.get("payload", {}).get("headers", [])}
            sender = headers.get("from", "").lower()
            if sender and sender not in settings:
                raise HTTPException(status_code=403, detail="Sender not allowed")
        parts = message.get("payload", {}).get("parts", [])
        body_text = gmail_client.extract_text_payload(parts) if parts else message.get("snippet", "")
        if not body_text:
            raise HTTPException(status_code=404, detail="Message body could not be extracted")
        system_prompt = "You are an assistant that summarizes Gmail messages for the user."
        user_prompt = payload.prompt or "Summarize this email concisely."
        summary = chatgpt_client.complete(
            [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=f"{user_prompt}\n\nEmail body:\n{body_text}"),
            ]
        )
        return SummarizeResponse(message_id=payload.message_id, summary=summary.strip())

    @app.post("/send", response_model=dict)
    def send_email(
        draft: DraftEmail,
        gmail_client: Annotated[GmailClient, Depends(get_gmail_client)],
        chatgpt_client: Annotated[ChatGPTClient, Depends(get_chatgpt_client)],
        personalize: bool = False,
    ):
        body = draft.body
        if personalize:
            body = chatgpt_client.complete(
                [
                    ChatMessage(role="system", content="You help polish outgoing emails before they are sent."),
                    ChatMessage(
                        role="user",
                        content=(
                            "Polish the following email for clarity and professionalism while keeping the intent intact:\n" + draft.body
                        ),
                    ),
                ]
            )
        result = gmail_client.send_message(draft.to, draft.subject, body)
        return {"id": result.get("id"), "threadId": result.get("threadId")}

    return app


app = create_app()
