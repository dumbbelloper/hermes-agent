"""Visa press release listing adapter."""

from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Iterable, List, Optional
from urllib.parse import urlencode, urlsplit, urlunsplit

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


class VisaReleaseNotesParser(HTMLParser):
    def __init__(self, source_uri: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source_uri = source_uri
        self._heading_tag: Optional[str] = None
        self._heading_parts: List[str] = []
        self._pending_month: Optional[str] = None
        self._capture_depth = 0
        self._description_parts: List[str] = []
        self.items: List[Candidate] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if tag == "h3":
            self._heading_tag = tag
            self._heading_parts = []
        if (
            tag == "div"
            and self._pending_month
            and self._capture_depth == 0
            and "spacer-medium" in attributes.get("class", "")
            and "vdc-text--primary" in attributes.get("class", "")
        ):
            self._capture_depth = 1
            self._description_parts = []
        elif tag == "div" and self._capture_depth:
            self._capture_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self._heading_tag == tag:
            heading = " ".join(self._heading_parts).strip()
            try:
                month = datetime.strptime(heading, "%B %Y")
            except ValueError:
                self._pending_month = None
            else:
                self._pending_month = month.strftime("%Y-%m")
            self._heading_tag = None
            self._heading_parts = []
        if tag == "div" and self._capture_depth:
            self._capture_depth -= 1
            if self._capture_depth == 0 and self._pending_month:
                month = self._pending_month
                self.items.append(
                    Candidate(
                        title="Visa Developer Release Notes — {}".format(month),
                        url=self._month_url(month),
                        published_at=month + "-01",
                        category="Developer release notes",
                        description=" ".join(self._description_parts),
                        external_id=month,
                        metadata={"date_precision": "month"},
                    )
                )
                self._pending_month = None
                self._description_parts = []

    def handle_data(self, data: str) -> None:
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self._heading_tag:
            self._heading_parts.append(value)
        if self._capture_depth:
            self._description_parts.append(value)

    def _month_url(self, month: str) -> str:
        parts = urlsplit(self.source_uri)
        query = urlencode({"month": month})
        return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


class VisaReleaseNotesAdapter:
    def parse(
        self,
        source: SourceConfig,
        response: FetchResult,
    ) -> Iterable[Candidate]:
        try:
            document = response.body.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise AdapterError("Visa release notes cannot be decoded") from error
        parser = VisaReleaseNotesParser(source.uri)
        parser.feed(document)
        parser.close()
        if not parser.items:
            raise AdapterError("Visa release notes contained no monthly entries")
        return parser.items
