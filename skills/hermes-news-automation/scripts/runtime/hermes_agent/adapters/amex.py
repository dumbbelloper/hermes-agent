"""American Express Newsroom AEM model adapter."""

from __future__ import annotations

import json
from typing import Iterable, Mapping, MutableSet
from urllib.parse import urljoin

from .base import AdapterError
from ..models import Candidate, FetchResult, SourceConfig


LIST_COMPONENT = "newsroom/components/content/list"


def _objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


class AmexNewsroomAdapter:
    def parse(
        self,
        source: SourceConfig,
        response: FetchResult,
    ) -> Iterable[Candidate]:
        try:
            document = json.loads(response.body.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AdapterError(
                "American Express response is not valid UTF-8 JSON"
            ) from error
        if not isinstance(document, dict):
            raise AdapterError("American Express response root must be an object")

        article_base_uri = str(
            source.options.get(
                "article_base_uri",
                "https://www.americanexpress.com/",
            )
        )
        seen: MutableSet[str] = set()
        candidates = []
        for component in _objects(document):
            if component.get(":type") != LIST_COMPONENT:
                continue
            items = component.get("items")
            if not isinstance(items, list):
                raise AdapterError("American Express list items must be an array")
            for item in items:
                if not isinstance(item, Mapping):
                    raise AdapterError(
                        "American Express article entry must be an object"
                    )
                raw_url = str(item.get("url", "")).strip()
                if not raw_url or raw_url in seen:
                    continue
                seen.add(raw_url)
                public_path = raw_url
                if public_path.startswith("/content/amex/"):
                    public_path = public_path[len("/content/amex") :]
                candidates.append(
                    Candidate(
                        title=str(item.get("title", "")),
                        url=urljoin(article_base_uri, public_path),
                        published_at=str(item.get("firstPublishDate", "")),
                        category=str(item.get("category", "")) or None,
                        description=str(item.get("description", "")) or None,
                        external_id=str(item.get("path", "")) or None,
                        metadata={
                            "last_modified_epoch_ms": item.get("lastModified"),
                        },
                    )
                )
        if not candidates:
            raise AdapterError(
                "American Express AEM model contained no newsroom items"
            )
        return candidates
