"""RSS 2.0 and Atom feed adapter using the Python standard library."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Iterable, Optional

from .base import AdapterError
from ..models import Candidate, FetchResult, SourceConfig


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_text(element: ET.Element, *names: str) -> Optional[str]:
    expected = {name.lower() for name in names}
    for child in element:
        if local_name(child.tag) in expected and child.text:
            return child.text.strip()
    return None


def atom_link(element: ET.Element) -> Optional[str]:
    fallback = None
    for child in element:
        if local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if not href:
            continue
        relation = child.attrib.get("rel", "alternate")
        if relation == "alternate":
            return href
        fallback = fallback or href
    return fallback


class RssAtomAdapter:
    def parse(
        self,
        source: SourceConfig,
        response: FetchResult,
    ) -> Iterable[Candidate]:
        try:
            root = ET.fromstring(response.body)
        except ET.ParseError as error:
            raise AdapterError("feed response is not valid XML") from error

        root_name = local_name(root.tag)
        if root_name == "rss":
            return self._parse_rss(root)
        if root_name == "feed":
            return self._parse_atom(root)
        raise AdapterError("unsupported feed root: {}".format(root_name))

    def _parse_rss(self, root: ET.Element):
        items = [
            element
            for element in root.iter()
            if local_name(element.tag) == "item"
        ]
        candidates = []
        for item in items:
            link = child_text(item, "link")
            guid = child_text(item, "guid")
            candidates.append(
                Candidate(
                    title=child_text(item, "title") or "",
                    url=link or guid or "",
                    published_at=child_text(
                        item, "pubDate", "published", "date"
                    )
                    or "",
                    category=child_text(item, "category"),
                    description=child_text(
                        item, "description", "summary", "encoded"
                    ),
                    external_id=guid,
                )
            )
        return candidates

    def _parse_atom(self, root: ET.Element):
        entries = [
            element
            for element in root
            if local_name(element.tag) == "entry"
        ]
        candidates = []
        for entry in entries:
            candidates.append(
                Candidate(
                    title=child_text(entry, "title") or "",
                    url=atom_link(entry) or child_text(entry, "id") or "",
                    published_at=child_text(
                        entry, "published", "updated"
                    )
                    or "",
                    category=self._atom_category(entry),
                    description=child_text(entry, "summary", "content"),
                    external_id=child_text(entry, "id"),
                )
            )
        return candidates

    @staticmethod
    def _atom_category(entry: ET.Element) -> Optional[str]:
        for child in entry:
            if local_name(child.tag) == "category":
                return child.attrib.get("term") or child.text
        return None

