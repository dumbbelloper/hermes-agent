"""Fail-closed validation for normalized records and source configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List
from urllib.parse import urlsplit

from .models import Record, SourceConfig
from .normalize import hostname_allowed


SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    code: str
    message: str


def validate_source(source: SourceConfig) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not SOURCE_ID_PATTERN.fullmatch(source.id):
        issues.append(
            ValidationIssue("id", "invalid_format", "source id must be kebab-case")
        )
    parsed = urlsplit(source.uri)
    if parsed.scheme != "https" or not parsed.hostname:
        issues.append(
            ValidationIssue("uri", "invalid_https_uri", "source URI must use HTTPS")
        )
    elif not hostname_allowed(source.uri, source.allowed_domains):
        issues.append(
            ValidationIssue(
                "uri",
                "domain_not_allowed",
                "source URI is outside its domain allowlist",
            )
        )
    if not source.allowed_domains:
        issues.append(
            ValidationIssue(
                "allowed_domains",
                "missing",
                "at least one allowed domain is required",
            )
        )
    if source.priority < 1:
        issues.append(
            ValidationIssue("priority", "invalid_range", "priority must be positive")
        )
    if source.freshness_days < 1:
        issues.append(
            ValidationIssue(
                "freshness_days",
                "invalid_range",
                "freshness_days must be positive",
            )
        )
    return issues


def validate_record(
    source: SourceConfig,
    record: Record,
    today: date,
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not record.title:
        issues.append(ValidationIssue("title", "missing", "title is required"))
    if record.source_id != source.id:
        issues.append(
            ValidationIssue("source_id", "mismatch", "record source does not match")
        )
    if urlsplit(record.canonical_url).scheme != "https":
        issues.append(
            ValidationIssue(
                "canonical_url",
                "insecure",
                "official article URL must use HTTPS",
            )
        )
    if not hostname_allowed(record.canonical_url, source.allowed_domains):
        issues.append(
            ValidationIssue(
                "canonical_url",
                "domain_not_allowed",
                "article URL is outside the source allowlist",
            )
        )
    try:
        published = date.fromisoformat(record.published_at)
        if published > today + timedelta(days=1):
            issues.append(
                ValidationIssue(
                    "published_at",
                    "future_date",
                    "publication date is unexpectedly in the future",
                )
            )
    except ValueError:
        issues.append(
            ValidationIssue(
                "published_at",
                "invalid_date",
                "publication date must be YYYY-MM-DD",
            )
        )
    if record.official != source.official:
        issues.append(
            ValidationIssue(
                "official",
                "mismatch",
                "record official flag must match the source classification",
            )
        )
    return issues
