"""Simple wrapper around OpenAI's Chat Completions API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from openai import OpenAI

from .config import Settings


@dataclass
class ChatMessage:
    role: str
    content: str


class ChatGPTClient:
    """Interact with OpenAI's Chat Completions API."""

    def __init__(self, settings: Settings):
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def complete(self, messages: Iterable[ChatMessage], temperature: float = 0.2) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            temperature=temperature,
        )
        return response.choices[0].message.content
