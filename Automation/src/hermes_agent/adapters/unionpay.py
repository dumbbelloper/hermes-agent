"""UnionPay International official news JSON adapter."""

from __future__ import annotations

import json
from typing import Iterable
from urllib.parse import urljoin

from .base import AdapterError
from ..models import Candidate, FetchResult, SourceConfig


class UnionPayNewsAdapter:
    def parse(
        self,
        source: SourceConfig,
        response: FetchResult,
    ) -> Iterable[Candidate]:
        try:
            document = json.loads(response.body.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AdapterError("UnionPay response is not valid UTF-8 JSON") from error
        if not isinstance(document, dict):
            raise AdapterError("UnionPay response root must be an object")
        items = document.get("newsList")
        if not isinstance(items, list):
            raise AdapterError("UnionPay response is missing newsList")

        article_base_uri = str(
            source.options.get(
                "article_base_uri",
                "https://www.unionpayintl.com/",
            )
        )
        candidates = []
        for item in items:
            if not isinstance(item, dict):
                raise AdapterError("UnionPay article entry must be an object")
            article_path = str(item.get("new_pcUrl", "")).strip()
            if not article_path:
                raise AdapterError("UnionPay article entry is missing new_pcUrl")
            candidates.append(
                Candidate(
                    title=str(item.get("new_title", "")),
                    url=urljoin(article_base_uri, article_path),
                    published_at=str(item.get("showTime", "")),
                    category=source.channel,
                    external_id=article_path.rsplit("/", 1)[-1].split(".", 1)[0],
                )
            )
        if not candidates:
            raise AdapterError("UnionPay newsList contained no items")
        return candidates
