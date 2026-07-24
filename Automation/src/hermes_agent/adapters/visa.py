"""Visa press release listing adapter."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Iterable, List, Optional

from .base import AdapterError
from ..models import Candidate, FetchResult, SourceConfig


DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")


class VisaListingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture_paragraph = False
        self._paragraph_parts: List[str] = []
        self._capture_link = False
        self._link_parts: List[str] = []
        self._link_href: Optional[str] = None
        self._current_date: Optional[str] = None
        self.items: List[Candidate] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if tag == "p":
            self._capture_paragraph = True
            self._paragraph_parts = []
        if tag == "a":
            href = attributes.get("href", "")
            if "press-releases.releaseId." in href:
                self._capture_link = True
                self._link_href = href
                self._link_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._capture_paragraph:
            text = " ".join(self._paragraph_parts).strip()
            if DATE_PATTERN.fullmatch(text):
                self._current_date = text
            self._capture_paragraph = False
        if tag == "a" and self._capture_link:
            title = " ".join(self._link_parts).strip()
            if title and self._link_href and self._current_date:
                self.items.append(
                    Candidate(
                        title=title,
                        url=self._link_href,
                        published_at=self._current_date,
                        category="Press release",
                        external_id=self._external_id(self._link_href),
                    )
                )
            self._capture_link = False
            self._link_href = None
            self._link_parts = []

    def handle_data(self, data: str) -> None:
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self._capture_paragraph:
            self._paragraph_parts.append(value)
        if self._capture_link:
            self._link_parts.append(value)

    @staticmethod
    def _external_id(href: str) -> Optional[str]:
        match = re.search(r"releaseId\.([^.\/]+)", href)
        return match.group(1) if match else None


class VisaPressAdapter:
    def parse(
        self,
        source: SourceConfig,
        response: FetchResult,
    ) -> Iterable[Candidate]:
        charset = "utf-8"
        content_type = response.headers.get("content-type", "")
        match = re.search(r"charset=([^;\s]+)", content_type, re.IGNORECASE)
        if match:
            charset = match.group(1).strip("\"'")
        try:
            document = response.body.decode(charset, errors="strict")
        except (LookupError, UnicodeDecodeError) as error:
            raise AdapterError("Visa response cannot be decoded") from error
        parser = VisaListingParser()
        parser.feed(document)
        if not parser.items:
            raise AdapterError("Visa listing contained no press release items")
        return parser.items

