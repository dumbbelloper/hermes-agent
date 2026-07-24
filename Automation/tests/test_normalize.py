from __future__ import annotations

import unittest
from datetime import datetime, timezone

from hermes_agent.models import Candidate, SourceConfig
from hermes_agent.normalize import (
    NormalizationError,
    canonicalize_url,
    clean_text,
    normalize_candidate,
    parse_date,
)


class NormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceConfig(
            id="visa-press",
            organization="Visa",
            channel="press",
            uri="https://usa.visa.com/news/",
            adapter="visa_press_html",
            enabled=True,
            priority=1,
            freshness_days=14,
            allowed_domains=("usa.visa.com",),
        )

    def test_canonical_url_removes_tracking_but_preserves_semantics(self) -> None:
        value = canonicalize_url(
            "HTTPS://USA.VISA.COM:443/item/?b=2&utm_source=x&a=1#section"
        )
        self.assertEqual("https://usa.visa.com/item?a=1&b=2", value)

    def test_semantic_queries_remain_distinct(self) -> None:
        first = canonicalize_url("https://example.com/item?id=1")
        second = canonicalize_url("https://example.com/item?id=2")
        self.assertNotEqual(first, second)

    def test_canonicalization_is_idempotent(self) -> None:
        value = "https://Example.com/path/?utm_medium=email&x=1"
        once = canonicalize_url(value)
        self.assertEqual(once, canonicalize_url(once))

    def test_date_formats(self) -> None:
        self.assertEqual("2026-07-22", parse_date("22/07/2026"))
        self.assertEqual("2026-07-14", parse_date("JUL 14, 2026"))
        self.assertEqual(
            "2026-07-15",
            parse_date("Wed, 15 Jul 2026 09:00:00 +0000"),
        )
        self.assertEqual(
            "2026-07-24",
            parse_date("2026-07-24T10:30:00Z"),
        )
        self.assertEqual("2024-02-05", parse_date("FEB, 05,2024"))

    def test_clean_text_removes_feed_markup(self) -> None:
        self.assertEqual(
            "Payment security update",
            clean_text("<p>Payment <strong>security</strong> update</p>"),
        )

    def test_normalize_rejects_non_official_domain(self) -> None:
        with self.assertRaises(NormalizationError):
            normalize_candidate(
                self.source,
                Candidate(
                    title="Unexpected mirror",
                    url="https://example.net/article",
                    published_at="2026-07-22",
                ),
                datetime(2026, 7, 24, tzinfo=timezone.utc),
            )

    def test_record_id_is_stable(self) -> None:
        candidate = Candidate(
            title="Official item",
            url="/item?utm_source=test",
            published_at="2026-07-22",
        )
        timestamp = datetime(2026, 7, 24, tzinfo=timezone.utc)
        first = normalize_candidate(self.source, candidate, timestamp)
        second = normalize_candidate(self.source, candidate, timestamp)
        self.assertEqual(first.id, second.id)
        self.assertEqual("https://usa.visa.com/item", first.canonical_url)


if __name__ == "__main__":
    unittest.main()
