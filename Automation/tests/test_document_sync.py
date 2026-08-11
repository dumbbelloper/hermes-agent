from __future__ import annotations

import configparser
import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote


REPOSITORY_ROOT = Path(__file__).parents[2]
LOCAL_MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\((?![a-z]+:)([^)#]+)")


class DocumentSyncTests(unittest.TestCase):
    def test_local_markdown_links_exist(self) -> None:
        missing = []
        for document in REPOSITORY_ROOT.rglob("*.md"):
            if ".git" in document.parts:
                continue
            content = document.read_text(encoding="utf-8")
            for match in LOCAL_MARKDOWN_LINK.finditer(content):
                raw_target = match.group(1).strip().strip("<>")
                target = (document.parent / unquote(raw_target)).resolve()
                if not target.exists():
                    missing.append(
                        "{} -> {}".format(
                            document.relative_to(REPOSITORY_ROOT),
                            raw_target,
                        )
                    )
        self.assertEqual([], missing)

    def test_version_status_is_synchronized(self) -> None:
        package = configparser.ConfigParser()
        package.read(REPOSITORY_ROOT / "setup.cfg", encoding="utf-8")
        version = package["metadata"]["version"]
        self.assertEqual("0.1.0", version)
        for relative_path in (
            "PROJECT_PLAN.md",
            "Automation/README.md",
            "SKILL_DISTRIBUTION_GUIDE.md",
            "HERMES_AUTOMATION_GUIDE.md",
        ):
            content = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn("v{}".format(version), content, msg=relative_path)

    def test_current_counts_are_synchronized(self) -> None:
        registry = json.loads(
            (REPOSITORY_ROOT / "Automation/config/sources.json").read_text(
                encoding="utf-8"
            )
        )
        source_count = sum(source["enabled"] for source in registry["sources"])
        digest_count = len(list((REPOSITORY_ROOT / "Digests").glob("*.md")))

        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        catalog = (REPOSITORY_ROOT / "SOURCE_CATALOG.md").read_text(encoding="utf-8")
        plan = (REPOSITORY_ROOT / "PROJECT_PLAN.md").read_text(encoding="utf-8")
        record_count = re.search(
            r"누적 정상 레코드는 ([0-9,]+)건",
            catalog,
        )

        self.assertIn("총 {}개 출처".format(source_count), readme)
        self.assertIn("총 {}개다".format(source_count), catalog)
        self.assertIsNotNone(record_count)
        self.assertIn("문서 수는 `Inbox/*.md`에서 계산한다", plan)
        self.assertIn("초기 수집 결과 Digest {}개 생성".format(digest_count), plan)

    def test_deployment_status_records_verified_path_and_tap_limit(self) -> None:
        guide = (REPOSITORY_ROOT / "SKILL_DISTRIBUTION_GUIDE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("skills.sh identifier를 우선 사용", guide)
        self.assertIn("Hermes 0.19.0", guide)
        self.assertIn("검색 제약", guide)

    def test_parallel_work_logs_use_unique_task_files(self) -> None:
        agents = (REPOSITORY_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        index = REPOSITORY_ROOT / "Work Logs" / "README.md"
        self.assertIn("Work Logs/YYYY/MM/", agents)
        self.assertIn("루트 `WORK_LOG.md`는 과거 기록 archive", agents)
        self.assertIn("[Work Logs](./Work%20Logs/README.md)", readme)
        self.assertTrue(index.is_file())


if __name__ == "__main__":
    unittest.main()
