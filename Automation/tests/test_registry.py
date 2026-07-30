from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hermes_agent.adapters.base import built_in_adapters
from hermes_agent.registry import RegistryError, SourceRegistry


CONFIG = Path(__file__).parents[1] / "config" / "sources.json"


class RegistryTests(unittest.TestCase):
    def test_packaged_registry_matches_project_registry(self) -> None:
        packaged = (
            Path(__file__).parents[2]
            / "skills"
            / "hermes-news-automation"
            / "scripts"
            / "runtime"
            / "hermes_agent"
            / "default_sources.json"
        )
        self.assertEqual(
            json.loads(CONFIG.read_text(encoding="utf-8")),
            json.loads(packaged.read_text(encoding="utf-8")),
        )

    def test_project_registry(self) -> None:
        registry = SourceRegistry.load(CONFIG, built_in_adapters())
        self.assertEqual("1.0", registry.schema_version)
        self.assertEqual(13, len(registry.sources))
        self.assertEqual(
            [
                "amex-newsroom",
                "banking-dive",
                "emvco-news",
                "jcb-press",
                "payments-dive",
                "pci-blog",
                "pymnts",
                "techcrunch-fintech",
                "unionpay-company-news",
                "unionpay-market-news",
                "visa-acceptance-devices-ios-releases",
                "visa-developer-release-notes",
                "visa-press",
            ],
            sorted(source.id for source in registry.select()),
        )
        editorial = {
            source.id: source.official
            for source in registry.sources
            if source.priority == 2
        }
        self.assertEqual(
            {
                "banking-dive": False,
                "payments-dive": False,
                "pymnts": False,
                "techcrunch-fintech": False,
            },
            editorial,
        )

    def test_selection_rejects_unknown_source(self) -> None:
        registry = SourceRegistry.load(CONFIG, built_in_adapters())
        with self.assertRaisesRegex(ValueError, "unknown source ids"):
            registry.select(["missing-source"])

    def test_enabled_must_be_boolean(self) -> None:
        document = json.loads(CONFIG.read_text(encoding="utf-8"))
        document["sources"][0]["enabled"] = "false"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(
                RegistryError,
                "enabled must be a boolean",
            ):
                SourceRegistry.load(path, built_in_adapters())

    def test_source_uri_must_match_allowlist(self) -> None:
        document = json.loads(CONFIG.read_text(encoding="utf-8"))
        document["sources"][0]["uri"] = "https://untrusted.example/feed"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(
                RegistryError,
                "uri:domain_not_allowed",
            ):
                SourceRegistry.load(path, built_in_adapters())

    def test_official_must_be_boolean(self) -> None:
        document = json.loads(CONFIG.read_text(encoding="utf-8"))
        document["sources"][0]["official"] = "false"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(
                RegistryError,
                "official must be a boolean",
            ):
                SourceRegistry.load(path, built_in_adapters())

    def test_article_extractor_must_be_supported(self) -> None:
        document = json.loads(CONFIG.read_text(encoding="utf-8"))
        document["sources"][0].setdefault("options", {})[
            "article_extractor"
        ] = "browser_automation"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(
                RegistryError,
                "options.article_extractor:unsupported",
            ):
                SourceRegistry.load(path, built_in_adapters())


if __name__ == "__main__":
    unittest.main()
