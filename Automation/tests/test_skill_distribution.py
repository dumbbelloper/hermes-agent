from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).parents[2]
SKILL_SOURCE = REPOSITORY_ROOT / "skills" / "hermes-news-automation"
MARKDOWN_LINK = re.compile(r"\]\((?!https?://)([^)#]+)")


class SkillDistributionTests(unittest.TestCase):
    def test_skill_bundle_runs_without_repository_runtime(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "installed" / "hermes-news-automation"
            workspace = root / "workspace"
            shutil.copytree(SKILL_SOURCE, skill)
            runner = skill / "scripts" / "run.py"
            environment = os.environ.copy()
            environment.update(
                {
                    "HERMES_NEWS_WORKSPACE": str(workspace),
                }
            )

            initialized = self._run(
                runner,
                "init",
                "--workspace",
                str(workspace),
                environment=environment,
            )
            self.assertEqual("initialized", initialized["status"])
            self.assertTrue((workspace / "Inbox").is_dir())
            self.assertTrue(
                (workspace / ".hermes-news" / "config" / "sources.json").is_file()
            )
            (
                workspace / ".hermes-news" / "config" / "telegram.json"
            ).write_text(
                json.dumps(
                    {
                        "bot_token": "test-token",
                        "chat_id": "test-chat",
                    }
                ),
                encoding="utf-8",
            )

            doctor = self._run(
                runner,
                "doctor",
                "--workspace",
                str(workspace),
                environment=environment,
            )
            self.assertEqual("ok", doctor["status"])

            registry = self._run(
                runner,
                "validate-registry",
                environment=environment,
            )
            self.assertEqual(13, registry["enabled"])

    def test_skill_markdown_links_stay_inside_bundle(self) -> None:
        content = (SKILL_SOURCE / "SKILL.md").read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(content):
            target = (SKILL_SOURCE / match.group(1)).resolve()
            self.assertTrue(
                target == SKILL_SOURCE.resolve()
                or SKILL_SOURCE.resolve() in target.parents,
                msg="Skill link escapes bundle: {}".format(match.group(1)),
            )
            self.assertTrue(target.exists(), msg="Missing Skill link: {}".format(target))

    def test_skill_markdown_explicitly_links_every_runtime_file(self) -> None:
        content = (SKILL_SOURCE / "SKILL.md").read_text(encoding="utf-8")
        linked = {match.group(1) for match in MARKDOWN_LINK.finditer(content)}
        runtime = SKILL_SOURCE / "scripts" / "runtime"
        required = {
            path.relative_to(SKILL_SOURCE).as_posix()
            for path in runtime.rglob("*")
            if path.is_file()
        }
        self.assertEqual(set(), required - linked)
        self.assertTrue(
            {
                "scripts/run.py",
                "scripts/precheck.py",
                "references/artifact-schema.md",
            }.issubset(linked)
        )

    def test_skill_bundle_has_no_repository_or_user_path_dependency(self) -> None:
        forbidden = (
            "Automation/run.py",
            "Automation/src",
            "HERMES_NEWS_REPO",
            "/Users/dumbbelloper",
        )
        for path in SKILL_SOURCE.rglob("*"):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for value in forbidden:
                self.assertNotIn(value, content, msg="{} contains {}".format(path, value))

    def test_copied_precheck_locates_hub_installed_skill(self) -> None:
        with TemporaryDirectory() as directory:
            hermes_home = Path(directory) / "hermes"
            skill = hermes_home / "skills" / "hermes-news-automation"
            scripts = hermes_home / "scripts"
            shutil.copytree(SKILL_SOURCE, skill)
            scripts.mkdir(parents=True)
            precheck = scripts / "hermes-news-precheck.py"
            shutil.copyfile(skill / "scripts" / "precheck.py", precheck)
            spec = importlib.util.spec_from_file_location(
                "hermes_news_precheck_test",
                precheck,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with patch.dict(
                os.environ,
                {"HERMES_HOME": str(hermes_home)},
                clear=False,
            ):
                self.assertEqual(
                    (skill / "scripts" / "run.py").resolve(),
                    module._runner(),
                )

    @staticmethod
    def _run(
        runner: Path,
        *arguments: str,
        environment,
    ):
        completed = subprocess.run(
            [sys.executable, str(runner), *arguments],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "command failed ({}): {}".format(
                    completed.returncode,
                    completed.stderr,
                )
            )
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
