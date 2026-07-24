from __future__ import annotations

import unittest
import urllib.request

from hermes_agent.fetcher import (
    AllowlistRedirectHandler,
    FetchError,
    HttpFetcher,
)
from hermes_agent.models import SourceConfig


def source(uri: str = "https://official.example/feed") -> SourceConfig:
    return SourceConfig(
        id="official-feed",
        organization="Test",
        channel="news",
        uri=uri,
        adapter="rss_atom",
        enabled=True,
        priority=1,
        freshness_days=14,
        allowed_domains=("official.example",),
    )


class FetcherTests(unittest.TestCase):
    def test_rejects_initial_uri_before_network_access(self) -> None:
        with self.assertRaisesRegex(FetchError, "outside"):
            HttpFetcher().fetch(source("https://untrusted.example/feed"))

    def test_rejects_redirect_before_following_it(self) -> None:
        handler = AllowlistRedirectHandler(("official.example",))
        request = urllib.request.Request("https://official.example/feed")
        with self.assertRaisesRegex(FetchError, "redirect left"):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://untrusted.example/collect",
            )

    def test_allows_https_redirect_within_subdomains(self) -> None:
        handler = AllowlistRedirectHandler(("official.example",))
        request = urllib.request.Request("https://official.example/feed")
        redirected = handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://cdn.official.example/feed.xml",
        )
        self.assertEqual(
            "https://cdn.official.example/feed.xml",
            redirected.full_url,
        )


if __name__ == "__main__":
    unittest.main()
