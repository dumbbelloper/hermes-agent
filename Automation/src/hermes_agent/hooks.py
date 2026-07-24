"""Small event boundary for future hooks, skills, telemetry, and notifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Mapping, Protocol

from .models import isoformat_utc, utc_now


@dataclass(frozen=True)
class Event:
    name: str
    source_id: str
    run_id: str
    occurred_at: str = field(default_factory=lambda: isoformat_utc(utc_now()))
    payload: Mapping[str, Any] = field(default_factory=dict)


class Hook(Protocol):
    def handle(self, event: Event) -> None:
        ...


class NullHook:
    def handle(self, event: Event) -> None:
        return None


class CompositeHook:
    def __init__(self, hooks: Iterable[Hook]) -> None:
        self._hooks = tuple(hooks)

    def handle(self, event: Event) -> None:
        for hook in self._hooks:
            hook.handle(event)

