from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from hermes_agent.adapters.jcb import JcbJsonAdapter
from hermes_agent.adapters.rss import RssAtomAdapter
from hermes_agent.adapters.amex import AmexNewsroomAdapter
from hermes_agent.adapters.unionpay import UnionPayNewsAdapter
from hermes_agent.adapters.visa import VisaPressAdapter, VisaReleaseNotesAdapter
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

    def test_visa_release_notes_html(self) -> None:
        config = source(
            "visa-developer-release-notes",
            "https://developer.visa.com/site/release_notes",
            "visa_release_notes_html",
            "developer.visa.com",
        )
        items = list(
            VisaReleaseNotesAdapter().parse(
                config,
                response(
                    FIXTURES / "visa_release_notes.html",
                    config.uri,
                    "text/html; charset=utf-8",
                ),
            )
        )
        self.assertEqual(2, len(items))
        self.assertEqual("2026-04-01", items[0].published_at)
        self.assertEqual(
            "https://developer.visa.com/site/release_notes?month=2026-04",
            items[0].url,
        )
        self.assertIn("Intelligent Commerce", items[0].description)
        self.assertEqual("month", items[0].metadata["date_precision"])

    def test_unionpay_json(self) -> None:
        config = source(
            "unionpay-company-news",
            "https://www.unionpayintl.com/wap/newsList/en_companyNews.json",
            "unionpay_news_json",
            "www.unionpayintl.com",
        )
        items = list(
            UnionPayNewsAdapter().parse(
                config,
                response(
                    FIXTURES / "unionpay.json",
                    config.uri,
                    "application/json",
                ),
            )
        )
        self.assertEqual(2, len(items))
        self.assertEqual("3016449", items[0].external_id)
        self.assertEqual(
            "https://www.unionpayintl.com/en/mediaCenter/newsCenter/companyNews/3016449.shtml",
            items[0].url,
        )

    def test_amex_aem_json_deduplicates_lists(self) -> None:
        config = source(
            "amex-newsroom",
            "https://www.americanexpress.com/en-us/newsroom/index.model.json",
            "amex_newsroom_json",
            "www.americanexpress.com",
        )
        items = list(
            AmexNewsroomAdapter().parse(
                config,
                response(
                    FIXTURES / "amex.json",
                    config.uri,
                    "application/json",
                ),
            )
        )
        self.assertEqual(1, len(items))
        self.assertEqual(
            "https://www.americanexpress.com/en-us/newsroom/articles/financial-news/second-quarter-results.html",
            items[0].url,
        )
        self.assertEqual(
            "2026-07-24T13:00:00.000+01:00",
            items[0].published_at,
        )

    @staticmethod
    def _normalized_date(value: str) -> str:
        return datetime.strptime(value.title(), "%b %d, %Y").date().isoformat()


if __name__ == "__main__":
    unittest.main()
