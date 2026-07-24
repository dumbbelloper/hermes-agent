"""Bounded HTTP fetching with explicit retry classification."""

from __future__ import annotations

import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping, Optional
from urllib.parse import urlsplit

from .models import FetchResult, SourceConfig, utc_now
from .normalize import hostname_allowed


@dataclass(frozen=True)
class FetchPolicy:
    timeout_seconds: float = 20.0
    max_response_bytes: int = 10 * 1024 * 1024
    user_agent: str = (
        "HermesAgent/0.1 "
        "(official-source collector; https://github.com/dumbbelloper/hermes-agent)"
    )


class FetchError(RuntimeError):
    def __init__(
        self,
        message: str,
        kind: str,
        retryable: bool,
        status: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.retryable = retryable
        self.status = status


class AllowlistRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_domains) -> None:
        super().__init__()
        self.allowed_domains = tuple(allowed_domains)

    def redirect_request(
        self,
        request,
        response,
        code,
        message,
        headers,
        new_url,
    ):
        if not _url_allowed(new_url, self.allowed_domains):
            raise FetchError(
                "redirect left the HTTPS source domain allowlist",
                kind="redirect_not_allowed",
                retryable=False,
                status=code,
            )
        return super().redirect_request(
            request,
            response,
            code,
            message,
            headers,
            new_url,
        )


def _url_allowed(url: str, allowed_domains) -> bool:
    return (
        urlsplit(url).scheme.lower() == "https"
        and hostname_allowed(url, allowed_domains)
    )


class HttpFetcher:
    def __init__(self, policy: Optional[FetchPolicy] = None) -> None:
        self.policy = policy or FetchPolicy()

    def fetch(self, source: SourceConfig) -> FetchResult:
        if not _url_allowed(source.uri, source.allowed_domains):
            raise FetchError(
                "source URI is outside the HTTPS domain allowlist",
                kind="source_not_allowed",
                retryable=False,
            )
        request = urllib.request.Request(
            source.uri,
            headers={
                "Accept": (
                    "application/json, application/rss+xml, "
                    "application/atom+xml, application/xml, text/html;q=0.9"
                ),
                "User-Agent": self.policy.user_agent,
            },
        )
        opener = urllib.request.build_opener(
            AllowlistRedirectHandler(source.allowed_domains)
        )
        try:
            with opener.open(
                request,
                timeout=self.policy.timeout_seconds,
            ) as response:
                final_url = response.geturl()
                if not _url_allowed(final_url, source.allowed_domains):
                    raise FetchError(
                        "final URL is outside the HTTPS source domain allowlist",
                        kind="redirect_not_allowed",
                        retryable=False,
                        status=response.status,
                    )
                body = response.read(self.policy.max_response_bytes + 1)
                if len(body) > self.policy.max_response_bytes:
                    raise FetchError(
                        "response exceeded configured byte limit",
                        kind="response_too_large",
                        retryable=False,
                        status=response.status,
                    )
                headers = {
                    key.lower(): value for key, value in response.headers.items()
                }
                return FetchResult(
                    requested_url=source.uri,
                    final_url=final_url,
                    status=response.status,
                    headers=headers,
                    body=body,
                    fetched_at=utc_now(),
                )
        except urllib.error.HTTPError as error:
            raise self._http_error(error) from error
        except (urllib.error.URLError, socket.timeout, TimeoutError) as error:
            raise FetchError(
                str(error),
                kind="network_transient",
                retryable=True,
            ) from error

    @staticmethod
    def _http_error(error: urllib.error.HTTPError) -> FetchError:
        status = error.code
        if status in {401, 403}:
            return FetchError(
                "source access was blocked",
                kind="access_blocked",
                retryable=False,
                status=status,
            )
        if status == 429 or 500 <= status <= 599:
            return FetchError(
                "source returned a transient HTTP error",
                kind="http_transient",
                retryable=True,
                status=status,
            )
        if status in {404, 410}:
            return FetchError(
                "source endpoint is unavailable",
                kind="source_unavailable",
                retryable=False,
                status=status,
            )
        return FetchError(
            "source returned HTTP {}".format(status),
            kind="http_error",
            retryable=False,
            status=status,
        )
