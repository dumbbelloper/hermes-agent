"""Telegram Bot API notification support without third-party dependencies."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, List, Optional


TELEGRAM_MESSAGE_LIMIT = 4096


class TelegramError(RuntimeError):
    pass


def split_message(
    text: str,
    limit: int = TELEGRAM_MESSAGE_LIMIT,
) -> List[str]:
    if limit < 1:
        raise ValueError("message limit must be positive")
    if not text:
        return []

    chunks = []
    remaining = text
    while len(remaining) > limit:
        boundary = remaining.rfind("\n", 0, limit + 1)
        if boundary < 1:
            boundary = limit
        else:
            boundary += 1
        chunks.append(remaining[:boundary])
        remaining = remaining[boundary:]
    if remaining:
        chunks.append(remaining)
    return chunks


class TelegramNotifier:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        timeout_seconds: float = 20.0,
        transport: Optional[Callable[[str, bytes, float], bytes]] = None,
    ) -> None:
        if not bot_token.strip():
            raise TelegramError("HERMES_TELEGRAM_BOT_TOKEN is required")
        if not chat_id.strip():
            raise TelegramError("HERMES_TELEGRAM_CHAT_ID is required")
        self._bot_token = bot_token.strip()
        self._chat_id = chat_id.strip()
        self._timeout_seconds = timeout_seconds
        self._transport = transport or self._post

    def send_text(self, text: str) -> int:
        chunks = split_message(text)
        if not chunks:
            raise TelegramError("Telegram message is empty")
        for chunk in chunks:
            payload = urllib.parse.urlencode(
                {
                    "chat_id": self._chat_id,
                    "text": chunk,
                    "disable_web_page_preview": "true",
                }
            ).encode("utf-8")
            endpoint = "https://api.telegram.org/bot{}/sendMessage".format(
                self._bot_token
            )
            try:
                raw_response = self._transport(
                    endpoint,
                    payload,
                    self._timeout_seconds,
                )
                response = json.loads(raw_response.decode("utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise TelegramError("Telegram API request failed") from error
            if not isinstance(response, dict) or response.get("ok") is not True:
                raise TelegramError("Telegram API rejected the message")
        return len(chunks)

    def send_files(self, paths: Iterable[Path]) -> int:
        sent = 0
        for path in paths:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                raise TelegramError(
                    "cannot read Telegram document: {}".format(path)
                ) from error
            sent += self.send_text(content)
        return sent

    @staticmethod
    def _post(url: str, payload: bytes, timeout_seconds: float) -> bytes:
        request = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "hermes-agent/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout_seconds,
            ) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            raise TelegramError(
                "Telegram API request failed with HTTP {}".format(error.code)
            ) from error
        except urllib.error.URLError as error:
            raise TelegramError("Telegram API network request failed") from error
