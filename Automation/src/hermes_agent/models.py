"""Data contracts shared by collectors, storage, and future consumers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "1.0"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class SourceConfig:
    """One trusted discovery endpoint in the Source Registry."""

    id: str
    organization: str
    channel: str
    uri: str
    adapter: str
    enabled: bool
    priority: int
    freshness_days: int
    allowed_domains: Tuple[str, ...]
    language: str = "en"
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Candidate:
    """Source-specific metadata before common normalization and validation."""

    title: str
    url: str
    published_at: str
    category: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FetchResult:
    requested_url: str
    final_url: str
    status: int
    headers: Mapping[str, str]
    body: bytes
    fetched_at: datetime


@dataclass(frozen=True)
class Record:
    """Stable normalized record consumed by storage, notes, and future APIs."""

    schema_version: str
    id: str
    source_id: str
    organization: str
    channel: str
    title: str
    url: str
    canonical_url: str
    published_at: str
    discovered_at: str
    language: str
    official: bool
    discovery_method: str
    category: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Record":
        data = dict(value)
        data.setdefault("metadata", {})
        return cls(**data)
