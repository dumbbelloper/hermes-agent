"""Common normalization rules applied after source-specific parsing."""

from __future__ import annotations

import email.utils
import hashlib
import html
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Iterable, List, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from .models import Candidate, Record, SCHEMA_VERSION, SourceConfig, isoformat_utc


TRACKING_QUERY_NAMES = {
    "dclid",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "msclkid",
}


class NormalizationError(ValueError):
    pass


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    unescaped = html.unescape(value)
    if "<" in unescaped and ">" in unescaped:
        parser = _TextExtractor()
        parser.feed(unescaped)
        parser.close()
        unescaped = " ".join(parser.parts)
    normalized = re.sub(r"\s+", " ", unescaped).strip()
    normalized = re.sub(r"\s+([.,;:!?])", r"\1", normalized)
    return normalized or None


def canonicalize_url(value: str, base_url: Optional[str] = None) -> str:
    absolute = urljoin(base_url or "", value.strip())
    parts = urlsplit(absolute)
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"}:
        raise NormalizationError("URL scheme must be http or https")
    hostname = (parts.hostname or "").lower()
    if not hostname:
        raise NormalizationError("URL hostname is missing")

    netloc = hostname
    if parts.port and not (
        (scheme == "http" and parts.port == 80)
        or (scheme == "https" and parts.port == 443)
    ):
        netloc = "{}:{}".format(hostname, parts.port)

    path = re.sub(r"/+$", "", parts.path) or "/"
    query = []
    for key, item_value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_QUERY_NAMES:
            continue
        query.append((key, item_value))

    return urlunsplit(
        (scheme, netloc, path, urlencode(sorted(query)), "")
    )


def hostname_allowed(url: str, allowed_domains: Iterable[str]) -> bool:
    hostname = (urlsplit(url).hostname or "").lower()
    for allowed in allowed_domains:
        normalized = allowed.lower().strip(".")
        if hostname == normalized or hostname.endswith("." + normalized):
            return True
    return False


def parse_date(value: str) -> str:
    normalized = re.sub(r",\s*", ", ", value.strip())
    normalized = re.sub(r"\s+", " ", normalized)
    iso_value = normalized
    if iso_value.endswith(("Z", "z")):
        iso_value = iso_value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(iso_value).date().isoformat()
    except ValueError:
        pass
    formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%b, %d, %Y",
        "%B, %d, %Y",
    )
    for date_format in formats:
        try:
            return datetime.strptime(normalized.title(), date_format).date().isoformat()
        except ValueError:
            pass
    try:
        return email.utils.parsedate_to_datetime(normalized).date().isoformat()
    except (TypeError, ValueError, OverflowError) as error:
        raise NormalizationError(
            "unsupported publication date: {!r}".format(value)
        ) from error


def stable_record_id(source_id: str, canonical_url: str) -> str:
    identity = "{}\n{}".format(source_id, canonical_url)
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def normalize_candidate(
    source: SourceConfig,
    candidate: Candidate,
    discovered_at: datetime,
) -> Record:
    title = clean_text(candidate.title)
    if not title:
        raise NormalizationError("title is missing")
    canonical_url = canonicalize_url(candidate.url, source.uri)
    if not hostname_allowed(canonical_url, source.allowed_domains):
        raise NormalizationError("article URL is outside allowed domains")

    return Record(
        schema_version=SCHEMA_VERSION,
        id=stable_record_id(source.id, canonical_url),
        source_id=source.id,
        organization=source.organization,
        channel=source.channel,
        title=title,
        url=canonical_url,
        canonical_url=canonical_url,
        published_at=parse_date(candidate.published_at),
        discovered_at=isoformat_utc(discovered_at),
        language=source.language,
        official=True,
        discovery_method=source.adapter,
        category=clean_text(candidate.category),
        description=clean_text(candidate.description),
        external_id=clean_text(candidate.external_id),
        metadata=dict(candidate.metadata),
    )
