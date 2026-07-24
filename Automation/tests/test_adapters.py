from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from hermes_agent.adapters.jcb import JcbJsonAdapter
from hermes_agent.adapters.rss import RssAtomAdapter
from hermes_agent.adapters.visa import VisaPressAdapter
from hermes_agent.models import FetchResult, SourceConfig


FIXTURES = Path(__file__).parent / "fixtures"


def source(
    source_id: str,
    uri: str,
    adapter: str,
    allowed_domain: str,
    options=None,
) -> SourceConfig:
    return SourceConfig(
        id=source_id,
        organization="Test",
        channel="news",
        uri=uri,
        adapter=adapter,
        enabled=True,
        priority=1,
        freshness_days=14,
        allowed_domains=(allowed_domain,),
        options=options or {},
    )


def response(path: Path, url: str, content_type: str) -> FetchResult:
    return FetchResult(
        requested_url=url,
        final_url=url,
        status=200,
        headers={"content-type": content_type},
        body=path.read_bytes(),
        fetched_at=datetime(2026, 7, 24, tzinfo=timezone.utc),
    )


class AdapterTests(unittest.TestCase):
    def test_jcb_json(self) -> None:
        config = source(
            "jcb-press",
            "https://www.global.jcb/en/press/news_file.json",
            "jcb_json",
            "www.global.jcb",
            {"article_base_uri": "https://www.global.jcb/en/press/"},
        )
        items = list(
            JcbJsonAdapter().parse(
                config,
                response(
                    FIXTURES / "jcb.json",
                    config.uri,
                    "application/json",
                ),
            )
        )
        self.assertEqual(2, len(items))
        self.assertEqual("2026-07-14", self._normalized_date(items[0].published_at))
        self.assertEqual(
            "https://www.global.jcb/en/press/2026/202607141000_products.html",
            items[0].url,
        )
        self.assertEqual("202607141000_products.html", items[0].external_id)

    def test_rss(self) -> None:
        config = source(
            "emvco-news",
            "https://www.emvco.com/news/feed/",
            "rss_atom",
            "www.emvco.com",
        )
        items = list(
            RssAtomAdapter().parse(
                config,
                response(FIXTURES / "rss.xml", config.uri, "application/rss+xml"),
            )
        )
        self.assertEqual(1, len(items))
        self.assertEqual("Payment Standard Updated", items[0].title)
        self.assertEqual("Specifications", items[0].category)
        self.assertEqual("emvco-test-1", items[0].external_id)

    def test_atom(self) -> None:
        config = source(
            "pci-blog",
            "https://blog.pcisecuritystandards.org/rss.xml",
            "rss_atom",
            "blog.pcisecuritystandards.org",
        )
        items = list(
            RssAtomAdapter().parse(
                config,
                response(FIXTURES / "atom.xml", config.uri, "application/atom+xml"),
            )
        )
        self.assertEqual(1, len(items))
        self.assertEqual(
            "https://blog.pcisecuritystandards.org/security-guidance",
            items[0].url,
        )
        self.assertEqual("Guidance", items[0].category)

    def test_visa_html(self) -> None:
        config = source(
            "visa-press",
            "https://usa.visa.com/about-visa/newsroom/press-releases-listing.html",
            "visa_press_html",
            "usa.visa.com",
        )
        items = list(
            VisaPressAdapter().parse(
                config,
                response(FIXTURES / "visa.html", config.uri, "text/html; charset=utf-8"),
            )
        )
        self.assertEqual(2, len(items))
        self.assertEqual("22596", items[0].external_id)
        self.assertEqual("22/07/2026", items[0].published_at)

    @staticmethod
    def _normalized_date(value: str) -> str:
        return datetime.strptime(value.title(), "%b %d, %Y").date().isoformat()


if __name__ == "__main__":
    unittest.main()

