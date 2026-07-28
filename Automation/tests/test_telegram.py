from __future__ import annotations

import json
import unittest
import urllib.parse
from pathlib import Path
from tempfile import TemporaryDirectory

from hermes_agent.telegram import (
    TELEGRAM_MESSAGE_LIMIT,
    TelegramError,
    TelegramNotifier,
    load_telegram_credentials,
    split_message,
)


class RecordingTransport:
    def __init__(self, response=None) -> None:
        self.calls = []
        self.response = response or {"ok": True}

    def __call__(self, url: str, payload: bytes, timeout: float) -> bytes:
        self.calls.append((url, payload, timeout))
        return json.dumps(self.response).encode("utf-8")


class TelegramTests(unittest.TestCase):
    def test_load_credentials_from_utf8_json(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "telegram.json"
            path.write_text(
                json.dumps(
                    {
                        "bot_token": "secret-token",
                        "chat_id": "12345",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                ("secret-token", "12345"),
                load_telegram_credentials(path),
            )

    def test_load_credentials_rejects_missing_values(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "telegram.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(TelegramError):
                load_telegram_credentials(path)

    def test_split_preserves_document_exactly(self) -> None:
        text = ("frontmatter\n" + ("가" * 1000) + "\n") * 6
        chunks = split_message(text)
        self.assertEqual(text, "".join(chunks))
        self.assertTrue(
            all(len(chunk) <= TELEGRAM_MESSAGE_LIMIT for chunk in chunks)
        )

    def test_send_text_uses_multiple_messages_without_token_in_payload(self) -> None:
        transport = RecordingTransport()
        notifier = TelegramNotifier(
            "secret-token",
            "12345",
            transport=transport,
        )
        text = "x" * (TELEGRAM_MESSAGE_LIMIT + 10)
        self.assertEqual(2, notifier.send_text(text))
        sent_text = ""
        for url, payload, timeout in transport.calls:
            self.assertIn("secret-token", url)
            values = urllib.parse.parse_qs(payload.decode("utf-8"))
            self.assertEqual(["12345"], values["chat_id"])
            sent_text += values["text"][0]
            self.assertEqual(20.0, timeout)
        self.assertEqual(text, sent_text)

    def test_send_files_reads_utf8_content(self) -> None:
        transport = RecordingTransport()
        notifier = TelegramNotifier("token", "chat", transport=transport)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "note.md"
            path.write_text("# 제목\n\n본문", encoding="utf-8")
            self.assertEqual(1, notifier.send_files([path]))
        values = urllib.parse.parse_qs(
            transport.calls[0][1].decode("utf-8")
        )
        self.assertEqual(["# 제목\n\n본문"], values["text"])

    def test_rejected_response_does_not_expose_token(self) -> None:
        notifier = TelegramNotifier(
            "do-not-expose",
            "chat",
            transport=RecordingTransport({"ok": False}),
        )
        with self.assertRaises(TelegramError) as raised:
            notifier.send_text("test")
        self.assertNotIn("do-not-expose", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
