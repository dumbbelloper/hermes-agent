"""Adapter protocol and registry."""

from __future__ import annotations

from typing import Dict, Iterable, Protocol, Type

from ..models import Candidate, FetchResult, SourceConfig


class AdapterError(ValueError):
    pass


class Adapter(Protocol):
    def parse(
        self,
        source: SourceConfig,
        response: FetchResult,
    ) -> Iterable[Candidate]:
        ...


class AdapterRegistry:
    def __init__(self) -> None:
        self._types: Dict[str, Type[Adapter]] = {}

    def register(self, name: str, adapter_type: Type[Adapter]) -> None:
        if name in self._types:
            raise ValueError("adapter already registered: {}".format(name))
        self._types[name] = adapter_type

    def create(self, name: str) -> Adapter:
        try:
            adapter_type = self._types[name]
        except KeyError as error:
            raise KeyError("unknown adapter: {}".format(name)) from error
        return adapter_type()

    def names(self):
        return tuple(sorted(self._types))


def built_in_adapters() -> AdapterRegistry:
    from .jcb import JcbJsonAdapter
    from .rss import RssAtomAdapter
    from .visa import VisaPressAdapter

    registry = AdapterRegistry()
    registry.register("jcb_json", JcbJsonAdapter)
    registry.register("rss_atom", RssAtomAdapter)
    registry.register("visa_press_html", VisaPressAdapter)
    return registry
