"""Load and validate the versioned Source Registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence

from .adapters.base import AdapterRegistry
from .models import SourceConfig
from .validation import validate_source


class RegistryError(ValueError):
    pass


class SourceRegistry:
    def __init__(
        self,
        schema_version: str,
        sources: Sequence[SourceConfig],
    ) -> None:
        self.schema_version = schema_version
        self.sources = tuple(sources)

    @classmethod
    def load(
        cls,
        path: Path,
        adapters: AdapterRegistry,
    ) -> "SourceRegistry":
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RegistryError("cannot read Source Registry: {}".format(path)) from error
        if not isinstance(document, dict):
            raise RegistryError("Source Registry root must be an object")
        schema_version = str(document.get("schema_version", ""))
        if schema_version != "1.0":
            raise RegistryError(
                "unsupported Source Registry schema: {}".format(schema_version)
            )
        raw_sources = document.get("sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise RegistryError("Source Registry must contain sources")

        sources: List[SourceConfig] = []
        seen = set()
        adapter_names = set(adapters.names())
        for raw in raw_sources:
            if not isinstance(raw, dict):
                raise RegistryError("source entry must be an object")
            source = cls._parse_source(raw)
            if source.id in seen:
                raise RegistryError("duplicate source id: {}".format(source.id))
            seen.add(source.id)
            if source.adapter not in adapter_names:
                raise RegistryError(
                    "source {} uses unknown adapter {}".format(
                        source.id, source.adapter
                    )
                )
            issues = validate_source(source)
            if issues:
                details = ", ".join(
                    "{}:{}".format(issue.field, issue.code) for issue in issues
                )
                raise RegistryError(
                    "invalid source {}: {}".format(source.id, details)
                )
            sources.append(source)
        return cls(schema_version, sources)

    @staticmethod
    def _parse_source(raw: Mapping[str, object]) -> SourceConfig:
        required = (
            "id",
            "organization",
            "channel",
            "uri",
            "adapter",
            "enabled",
            "priority",
            "freshness_days",
            "allowed_domains",
        )
        missing = [key for key in required if key not in raw]
        if missing:
            raise RegistryError(
                "source entry missing fields: {}".format(", ".join(missing))
            )
        domains = raw["allowed_domains"]
        if not isinstance(domains, list):
            raise RegistryError("allowed_domains must be an array")
        if not domains or not all(
            isinstance(item, str) and item.strip() for item in domains
        ):
            raise RegistryError(
                "allowed_domains must contain non-empty strings"
            )
        if not isinstance(raw["enabled"], bool):
            raise RegistryError("enabled must be a boolean")
        official = raw.get("official", True)
        if not isinstance(official, bool):
            raise RegistryError("official must be a boolean")
        for field_name in ("priority", "freshness_days"):
            value = raw[field_name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise RegistryError("{} must be an integer".format(field_name))
        for field_name in ("id", "organization", "channel", "uri", "adapter"):
            value = raw[field_name]
            if not isinstance(value, str) or not value.strip():
                raise RegistryError(
                    "{} must be a non-empty string".format(field_name)
                )
        language = raw.get("language", "en")
        if not isinstance(language, str) or not language.strip():
            raise RegistryError("language must be a non-empty string")
        options = raw.get("options", {})
        if not isinstance(options, dict):
            raise RegistryError("options must be an object")
        return SourceConfig(
            id=raw["id"],
            organization=raw["organization"],
            channel=raw["channel"],
            uri=raw["uri"],
            adapter=raw["adapter"],
            enabled=raw["enabled"],
            priority=raw["priority"],
            freshness_days=raw["freshness_days"],
            allowed_domains=tuple(domains),
            language=language,
            official=official,
            options=options,
        )

    def select(
        self,
        source_ids: Optional[Iterable[str]] = None,
    ) -> Sequence[SourceConfig]:
        requested = set(source_ids or ())
        if requested:
            known = {source.id for source in self.sources}
            unknown = sorted(requested - known)
            if unknown:
                raise RegistryError(
                    "unknown source ids: {}".format(", ".join(unknown))
                )
        return tuple(
            sorted(
                (
                    source
                    for source in self.sources
                    if source.enabled and (not requested or source.id in requested)
                ),
                key=lambda source: (source.priority, source.id),
            )
        )
