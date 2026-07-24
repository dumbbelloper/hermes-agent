"""JCB official press JSON adapter."""

from __future__ import annotations

import json
from typing import Iterable
from urllib.parse import urljoin

from .base import AdapterError
from ..models import Candidate, FetchResult, SourceConfig


class JcbJsonAdapter:
    def parse(
        self,
        source: SourceConfig,
        response: FetchResult,
    ) -> Iterable[Candidate]:
        try:
            document = json.loads(response.body.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AdapterError("JCB response is not valid UTF-8 JSON") from error
        if not isinstance(document, list):
            raise AdapterError("JCB response root must be an array")

        article_base_uri = str(
            source.options.get(
                "article_base_uri",
                "https://www.global.jcb/en/press/",
            )
        )
        candidates = []
        for year_group in document:
            if not isinstance(year_group, dict):
                raise AdapterError("JCB year entry must be an object")
            year = str(year_group.get("year", "")).strip()
            items = year_group.get("yearList")
            if not year or not isinstance(items, list):
                raise AdapterError("JCB year entry is missing year or yearList")
            for item in items:
                if not isinstance(item, dict):
                    raise AdapterError("JCB article entry must be an object")
                filename = str(item.get("fileName", "")).strip()
                if not filename:
                    raise AdapterError("JCB article entry is missing fileName")
                article_url = urljoin(
                    article_base_uri.rstrip("/") + "/",
                    "{}/{}".format(year, filename),
                )
                candidates.append(
                    Candidate(
                        title=str(item.get("title", "")),
                        url=article_url,
                        published_at=str(item.get("date", "")),
                        category=str(item.get("category", "")) or None,
                        external_id=filename,
                        metadata={"year": year},
                    )
                )
        return candidates
