"""Wise Platform public changelog JSON adapter."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List
from urllib.parse import quote

from .base import AdapterError
from ..models import Candidate, FetchResult, SourceConfig


class WiseChangelogAdapter:
    def parse(
        self,
        source: SourceConfig,
        response: FetchResult,
    ) -> Iterable[Candidate]:
        try:
            document = json.loads(response.body.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AdapterError("Wise response is not valid UTF-8 JSON") from error
        if not isinstance(document, dict):
            raise AdapterError("Wise response root must be an object")

        article_base_uri = str(
            source.options.get("article_base_uri", "https://docs.wise.com/changelog")
        ).rstrip("#")
        entries = self._changelog_entries(document)
        candidates = []
        for entry in entries:
            attributes = entry.get("attributes")
            if not isinstance(attributes, dict):
                raise AdapterError("Wise changelog entry is missing attributes")
            published_at = str(attributes.get("date", "")).strip()
            external_id = str(attributes.get("id", "")).strip()
            if not published_at or not external_id:
                raise AdapterError("Wise changelog entry is missing date or id")
            description = self._text(entry.get("children", []))
            candidates.append(
                Candidate(
                    title="Wise Platform API changelog — {}".format(published_at),
                    url="{}?entry={}".format(
                        article_base_uri,
                        quote(external_id, safe=""),
                    ),
                    published_at=published_at,
                    category="api-changelog",
                    description=description or None,
                    external_id=external_id,
                )
            )
        if not candidates:
            raise AdapterError("Wise changelog contained no entries")
        return candidates

    @classmethod
    def _changelog_entries(cls, value: Any) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        if isinstance(value, dict):
            if value.get("name") == "ChangelogEntry":
                entries.append(value)
            for child in value.values():
                entries.extend(cls._changelog_entries(child))
        elif isinstance(value, list):
            for child in value:
                entries.extend(cls._changelog_entries(child))
        return entries

    @classmethod
    def _text(cls, value: Any) -> str:
        fragments = cls._text_fragments(value)
        return re.sub(r"\s+", " ", "".join(fragments)).strip()

    @classmethod
    def _text_fragments(cls, value: Any) -> List[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            fragments: List[str] = []
            for child in value:
                fragments.extend(cls._text_fragments(child))
            return fragments
        if isinstance(value, dict):
            return cls._text_fragments(value.get("children", []))
        return []
