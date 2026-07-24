from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from hermes_agent.adapters.base import built_in_adapters
from hermes_agent.fetcher import FetchError
from hermes_agent.hooks import Event
from hermes_agent.models import FetchResult, SourceConfig
from hermes_agent.pipeline import CollectorPipeline
from hermes_agent.storage import FileStore


FIXTURE = Path(__file__).parent / "fixtures" / "jcb.json"


def config() -> SourceConfig:
    return SourceConfig(
        id="jcb-press",
        organization="JCB",
        channel="press",
        uri="https://www.global.jcb/en/press/news_file.json",
        adapter="jcb_json",
        enabled=True,
        priority=1,
        freshness_days=21,
        allowed_domains=("www.global.jcb",),
        options={
            "article_base_uri": "https://www.global.jcb/en/press/",
            "max_quarantine_ratio": 0.1,
        },
    )


class FakeFetcher:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.error = None

    def fetch(self, source: SourceConfig) -> FetchResult:
        if self.error:
            raise self.error
        return FetchResult(
            requested_url=source.uri,
            final_url=source.uri,
            status=200,
            headers={"content-type": "application/json"},
            body=self.body,
            fetched_at=datetime(2026, 7, 24, tzinfo=timezone.utc),
        )


class RecordingHook:
    def __init__(self) -> None:
        self.events = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class PipelineTests(unittest.TestCase):
    def test_repeat_update_and_failure_preserve_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fetcher = FakeFetcher(FIXTURE.read_bytes())
            hook = RecordingHook()
            store = FileStore(Path(directory))
            pipeline = CollectorPipeline(
                fetcher,
                built_in_adapters(),
                store,
                hook,
            )

            first = pipeline.collect(config())
            self.assertEqual("success", first.status)
            self.assertEqual(2, first.changes.new)
            self.assertEqual(2, first.changes.current_total)

            second = pipeline.collect(config())
            self.assertEqual(2, second.changes.unchanged)
            self.assertEqual(0, second.changes.new)

            fetcher.body = fetcher.body.replace(
                b"JCB Tests a New Payment Capability",
                b"JCB Tests an Updated Payment Capability",
            )
            third = pipeline.collect(config())
            self.assertEqual(1, third.changes.updated)
            self.assertEqual(1, third.changes.unchanged)

            current_before_failure = store.current_path("jcb-press").read_bytes()
            fetcher.error = FetchError(
                "blocked",
                kind="access_blocked",
                retryable=False,
                status=403,
            )
            failed = pipeline.collect(config())
            self.assertEqual("failed", failed.status)
            self.assertEqual("access_blocked", failed.error_kind)
            self.assertEqual(
                current_before_failure,
                store.current_path("jcb-press").read_bytes(),
            )
            state = store.load_state("jcb-press")
            self.assertEqual("degraded", state["status"])
            self.assertEqual(1, state["consecutive_failures"])
            self.assertTrue(
                any(event.name == "source_failed" for event in hook.events)
            )

    def test_empty_snapshot_does_not_replace_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fetcher = FakeFetcher(FIXTURE.read_bytes())
            store = FileStore(Path(directory))
            pipeline = CollectorPipeline(
                fetcher,
                built_in_adapters(),
                store,
            )
            self.assertEqual("success", pipeline.collect(config()).status)
            current = store.current_path("jcb-press").read_bytes()

            fetcher.body = b'[{"year":"2026","yearList":[]}]'
            report = pipeline.collect(config())
            self.assertEqual("failed", report.status)
            self.assertEqual("unexpected_empty_snapshot", report.error_kind)
            self.assertEqual(
                current,
                store.current_path("jcb-press").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()

