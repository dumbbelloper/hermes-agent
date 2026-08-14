from __future__ import annotations

import importlib.util
import io
import json
import math
import os
import subprocess
import sys
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).parents[2]
AUTONOMY_SCRIPT = REPOSITORY_ROOT / "Automation" / "autonomy.py"
WRAPPER_SCRIPT = REPOSITORY_ROOT / "Automation" / "hermes-news-autonomy-wrapper.py"
CRON_PROMPT = REPOSITORY_ROOT / "Automation" / "AUTONOMOUS_CRON_PROMPT.md"


def load_module():
    spec = importlib.util.spec_from_file_location("autonomy_under_test", AUTONOMY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Automation/autonomy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AutonomousOperationsTests(unittest.TestCase):
    @staticmethod
    def _git(directory: Path, *arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=str(directory),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
        return completed.stdout.strip()

    def test_cron_prompt_forbids_unattended_approval_waits(self) -> None:
        prompt = CRON_PROMPT.read_text(encoding="utf-8")

        self.assertIn("heredoc", prompt)
        self.assertIn("승인 대기", prompt)
        self.assertIn("즉시", prompt)
        self.assertIn("automation-abort", prompt)

    def test_cron_prompt_finishes_without_git_side_effects_when_no_note_is_published(self) -> None:
        prompt = CRON_PROMPT.read_text(encoding="utf-8")

        self.assertIn("게시할 Inbox 문서가 0건", prompt)
        self.assertIn("task log", prompt)
        self.assertIn("PR", prompt)
        self.assertIn("Telegram", prompt)
        self.assertIn("생성하지", prompt)
        self.assertIn("automation-finish", prompt)

    def test_quota_policy_allows_when_primary_usage_is_below_threshold(self) -> None:
        module = load_module()
        result = module.evaluate_quota(
            {
                "rateLimits": {
                    "primary": {"usedPercent": 9, "resetsAt": 1787014100},
                    "rateLimitReachedType": None,
                    "spendControlReached": False,
                }
            },
            maximum_used_percent=80,
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(91, result["remaining_percent"])
        self.assertEqual(1787014100, result["resets_at"])

    def test_quota_policy_blocks_at_configured_threshold(self) -> None:
        module = load_module()
        result = module.evaluate_quota(
            {
                "rateLimits": {
                    "primary": {"usedPercent": 80, "resetsAt": 1787014100},
                    "rateLimitReachedType": None,
                    "spendControlReached": False,
                }
            },
            maximum_used_percent=80,
        )
        self.assertFalse(result["allowed"])
        self.assertEqual("quota_threshold_reached", result["reason"])

    def test_quota_policy_fails_closed_when_live_window_is_missing(self) -> None:
        module = load_module()
        result = module.evaluate_quota(
            {"rateLimits": {"primary": None}},
            maximum_used_percent=80,
        )
        self.assertFalse(result["allowed"])
        self.assertEqual("quota_unavailable", result["reason"])

    def test_quota_policy_rejects_invalid_percentage_values(self) -> None:
        module = load_module()
        for value in (-1, 101, math.nan, True, "10"):
            with self.subTest(value=value):
                result = module.evaluate_quota(
                    {
                        "rateLimits": {
                            "primary": {"usedPercent": value, "resetsAt": None}
                        }
                    },
                    maximum_used_percent=80,
                )
                self.assertFalse(result["allowed"])
                self.assertEqual("invalid_primary_window", result["reason"])

    def test_quota_policy_rejects_malformed_spend_control_flag(self) -> None:
        module = load_module()
        for value in ("true", 1, [], {}):
            with self.subTest(value=value):
                result = module.evaluate_quota(
                    {
                        "rateLimits": {
                            "primary": {"usedPercent": 9, "resetsAt": None},
                            "spendControlReached": value,
                        }
                    },
                    maximum_used_percent=80,
                )
                self.assertFalse(result["allowed"])
                self.assertEqual("invalid_spend_control", result["reason"])

    def test_disabled_switch_never_wakes_agent(self) -> None:
        module = load_module()
        with TemporaryDirectory() as directory:
            config = Path(directory) / "autonomy.json"
            config.write_text(json.dumps({"enabled": False}), encoding="utf-8")
            self.assertFalse(module.is_enabled(config))

    def test_switch_write_is_atomic_and_owner_only(self) -> None:
        module = load_module()
        with TemporaryDirectory() as directory:
            config = Path(directory) / "config" / "autonomy.json"
            now = datetime(2026, 8, 11, tzinfo=timezone.utc)
            module.write_switch(config, enabled=True, now=now)
            self.assertTrue(module.is_enabled(config, now=now))
            if os.name != "nt":
                self.assertEqual(0o600, config.stat().st_mode & 0o777)

    @unittest.skipIf(os.name == "nt", "symlink creation requires elevated Windows access")
    def test_switch_write_does_not_follow_predictable_temporary_symlink(self) -> None:
        module = load_module()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "autonomy.json"
            victim = root / "victim.txt"
            victim.write_text("unchanged\n", encoding="utf-8")
            config.with_name(config.name + ".tmp").symlink_to(victim)
            module.write_switch(
                config,
                enabled=True,
                now=datetime(2026, 8, 11, tzinfo=timezone.utc),
            )
            self.assertEqual("unchanged\n", victim.read_text(encoding="utf-8"))

    def test_switch_fails_closed_after_standing_authorization_expires(self) -> None:
        module = load_module()
        with TemporaryDirectory() as directory:
            config = Path(directory) / "autonomy.json"
            config.write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "approved_until": "2026-08-12T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            expired = datetime(2026, 8, 13, tzinfo=timezone.utc)
            self.assertFalse(module.is_enabled(config, now=expired))

    def test_task_log_path_is_unique_and_partitioned_by_month(self) -> None:
        module = load_module()
        root = Path("/workspace")
        timestamp = datetime(2026, 8, 11, 2, 10, 41, 123456, tzinfo=timezone.utc)
        path = module.task_log_path(
            root,
            timestamp=timestamp,
            task_id="run/ABC 123",
            slug="MDES 문서 업데이트",
        )
        self.assertEqual(
            Path(
                "/workspace/Work Logs/2026/08/"
                "2026-08-11T021041.123456Z-run-abc-123-mdes.md"
            ),
            path,
        )

    def test_precheck_never_wakes_when_switch_is_off(self) -> None:
        module = load_module()
        result = module.decide_precheck(
            enabled=False,
            quota={"allowed": True, "remaining_percent": 91},
            repository_ready=True,
            queue_result={"wakeAgent": True, "context": {"run_id": "run-1"}},
        )
        self.assertEqual({"wakeAgent": False, "reason": "disabled"}, result)

    def test_macos_clamshell_probe_detects_closed_lid(self) -> None:
        module = load_module()

        def closed_lid_runner(command, **kwargs):
            return subprocess.CompletedProcess(
                command,
                returncode=0,
                stdout='  |   "AppleClamshellState" = Yes\n',
                stderr="",
            )

        self.assertTrue(
            module.macos_clamshell_is_closed(
                platform_name="darwin",
                command_runner=closed_lid_runner,
            )
        )

    def test_precheck_skips_closed_clamshell_before_external_gates(self) -> None:
        module = load_module()
        options = SimpleNamespace(
            workspace=str(REPOSITORY_ROOT),
            maximum_used_percent=80,
        )
        stdout = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(patch.object(module, "is_enabled", return_value=True))
            stack.enter_context(
                patch.object(module, "macos_clamshell_is_closed", return_value=True)
            )
            query_quota = stack.enter_context(patch.object(module, "query_quota"))
            repository_ready = stack.enter_context(
                patch.object(module, "_repository_ready")
            )
            news_precheck = stack.enter_context(patch.object(module, "_news_precheck"))
            stack.enter_context(redirect_stdout(stdout))
            return_code = module._precheck(options)

        self.assertEqual(0, return_code)
        self.assertEqual(
            {"wakeAgent": False, "reason": "clamshell_closed"},
            json.loads(stdout.getvalue()),
        )
        query_quota.assert_not_called()
        repository_ready.assert_not_called()
        news_precheck.assert_not_called()

    def test_precheck_injects_quota_into_wake_context(self) -> None:
        module = load_module()
        quota = {
            "allowed": True,
            "used_percent": 9,
            "remaining_percent": 91,
            "resets_at": 1787014100,
        }
        result = module.decide_precheck(
            enabled=True,
            quota=quota,
            repository_ready=True,
            queue_result={
                "wakeAgent": True,
                "context": {"run_id": "run-1", "queue_items": 1},
            },
        )
        self.assertTrue(result["wakeAgent"])
        self.assertEqual(quota, result["context"]["quota"])

    def test_autonomous_precheck_limits_each_quota_cycle_to_one_item(self) -> None:
        module = load_module()
        environment = module.autonomous_precheck_environment(
            Path("/workspace"),
            {"PATH": "/bin", "HERMES_NEWS_MAX_ITEMS": "99"},
        )
        self.assertEqual(
            str(Path("/workspace").resolve()),
            environment["HERMES_NEWS_WORKSPACE"],
        )
        self.assertEqual("1", environment["HERMES_NEWS_MAX_ITEMS"])

    def test_precheck_fails_closed_for_dirty_or_non_main_repository(self) -> None:
        module = load_module()
        result = module.decide_precheck(
            enabled=True,
            quota={"allowed": True},
            repository_ready=False,
            queue_result={"wakeAgent": True, "context": {"run_id": "run-1"}},
        )
        self.assertEqual(
            {"wakeAgent": False, "reason": "repository_not_ready"},
            result,
        )

    def test_precheck_preserves_no_change_result_without_waking(self) -> None:
        module = load_module()
        result = module.decide_precheck(
            enabled=True,
            quota={"allowed": True},
            repository_ready=True,
            queue_result={"wakeAgent": False, "reason": "no_changes"},
        )
        self.assertEqual({"wakeAgent": False, "reason": "no_changes"}, result)

    def test_repository_gate_requires_clean_main(self) -> None:
        module = load_module()
        self.assertTrue(module.repository_is_ready("main", ""))
        self.assertFalse(module.repository_is_ready("feature/topic", ""))
        self.assertFalse(module.repository_is_ready("main", " M README.md\n"))

    def test_remote_gate_allows_only_the_expected_repository(self) -> None:
        module = load_module()
        self.assertTrue(
            module.remote_is_allowed(
                "https://github.com/dumbbelloper/hermes-agent.git\n"
            )
        )
        self.assertTrue(
            module.remote_is_allowed("git@github.com:dumbbelloper/hermes-agent.git")
        )
        self.assertFalse(
            module.remote_is_allowed("https://github.com/attacker/hermes-agent.git")
        )

    def test_controller_is_bound_to_its_containing_repository(self) -> None:
        module = load_module()
        self.assertEqual(REPOSITORY_ROOT.resolve(), module.controller_workspace())

    def test_coordinator_sync_is_fetch_plus_ff_only_merge(self) -> None:
        module = load_module()
        self.assertEqual(
            [
                ["git", "fetch", "--quiet", "origin"],
                ["git", "merge", "--ff-only", "--quiet", "origin/main"],
            ],
            module.coordinator_sync_commands(),
        )

    def test_repository_sync_fast_forwards_clean_main(self) -> None:
        module = load_module()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "remote.git"
            seed = root / "seed"
            coordinator = root / "coordinator"
            remote.mkdir()
            self._git(remote, "init", "--bare")
            seed.mkdir()
            self._git(seed, "init")
            self._git(seed, "config", "user.name", "Autonomy Test")
            self._git(seed, "config", "user.email", "autonomy@example.invalid")
            (seed / "note.txt").write_text("one\n", encoding="utf-8")
            self._git(seed, "add", "note.txt")
            self._git(seed, "commit", "-m", "initial")
            self._git(seed, "branch", "-M", "main")
            self._git(seed, "remote", "add", "origin", str(remote))
            self._git(seed, "push", "-u", "origin", "main")
            self._git(root, "clone", "--branch", "main", str(remote), str(coordinator))
            (seed / "note.txt").write_text("two\n", encoding="utf-8")
            self._git(seed, "commit", "-am", "second")
            self._git(seed, "push", "origin", "main")

            self.assertTrue(
                module._repository_ready(
                    coordinator,
                    synchronize=True,
                    allowed_remote_urls=frozenset({str(remote)}),
                    expected_workspace=coordinator,
                )
            )
            self.assertEqual(
                self._git(seed, "rev-parse", "HEAD"),
                self._git(coordinator, "rev-parse", "HEAD"),
            )

            self._git(
                coordinator,
                "config",
                "remote.origin.pushurl",
                str(remote),
            )
            self._git(
                coordinator,
                "config",
                "--add",
                "remote.origin.pushurl",
                "https://github.com/attacker/hermes-agent.git",
            )
            self.assertFalse(
                module._repository_ready(
                    coordinator,
                    allowed_remote_urls=frozenset({str(remote)}),
                    expected_workspace=coordinator,
                )
            )
            self._git(coordinator, "config", "--unset-all", "remote.origin.pushurl")

            self._git(coordinator, "config", "user.name", "Autonomy Test")
            self._git(coordinator, "config", "user.email", "autonomy@example.invalid")
            (coordinator / "marker.txt").write_text("local only\n", encoding="utf-8")
            self._git(coordinator, "add", "marker.txt")
            self._git(coordinator, "commit", "-m", "local ahead")
            self.assertFalse(
                module._repository_ready(
                    coordinator,
                    synchronize=True,
                    allowed_remote_urls=frozenset({str(remote)}),
                    expected_workspace=coordinator,
                )
            )

    def test_enable_failure_leaves_switch_disabled(self) -> None:
        module = load_module()
        with TemporaryDirectory() as directory:
            switch = Path(directory) / "autonomy.json"

            def failing_runner(command, **kwargs):
                return subprocess.CompletedProcess(command, returncode=9)

            return_code = module.apply_control(
                enabled=True,
                switch_path=switch,
                job_name="Autonomous payment news",
                command_runner=failing_runner,
            )
            self.assertEqual(9, return_code)
            self.assertFalse(module.is_enabled(switch))

    def test_control_rejects_workspace_outside_controller_repository(self) -> None:
        module = load_module()
        with TemporaryDirectory() as directory:
            options = SimpleNamespace(
                workspace=directory,
                job_name="Autonomous payment news",
            )
            with patch.object(module, "apply_control") as apply_control:
                return_code = module._control(options, enabled=True)
            self.assertEqual(2, return_code)
            apply_control.assert_not_called()

    def test_json_command_wraps_launch_and_timeout_errors(self) -> None:
        module = load_module()
        with patch.object(
            module.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["probe"], 1),
        ):
            with self.assertRaisesRegex(RuntimeError, "command failed before completion"):
                module._json_command(["probe"], timeout=1)

    def test_news_precheck_failure_emits_skip_json_and_zero_exit(self) -> None:
        module = load_module()
        options = SimpleNamespace(workspace=str(REPOSITORY_ROOT), maximum_used_percent=80)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(patch.object(module, "is_enabled", return_value=True))
            stack.enter_context(
                patch.object(module, "macos_clamshell_is_closed", return_value=False)
            )
            stack.enter_context(
                patch.object(module, "query_quota", return_value={"allowed": True})
            )
            stack.enter_context(
                patch.object(module, "_repository_ready", return_value=True)
            )
            stack.enter_context(
                patch.object(
                    module,
                    "_news_precheck",
                    side_effect=RuntimeError("offline"),
                )
            )
            stack.enter_context(redirect_stdout(stdout))
            stack.enter_context(redirect_stderr(stderr))
            return_code = module._precheck(options)
        self.assertEqual(0, return_code)
        self.assertEqual(
            {"wakeAgent": False, "reason": "news_precheck_failed"},
            json.loads(stdout.getvalue()),
        )
        self.assertIn("offline", stderr.getvalue())

    def test_control_commands_pause_without_stopping_gateway(self) -> None:
        module = load_module()
        self.assertEqual(
            [["hermes", "cron", "pause", "Autonomous payment news"]],
            module.control_commands(False, "Autonomous payment news"),
        )

    def test_control_commands_start_gateway_before_resuming(self) -> None:
        module = load_module()
        self.assertEqual(
            [
                ["hermes", "gateway", "start"],
                ["hermes", "cron", "resume", "Autonomous payment news"],
            ],
            module.control_commands(True, "Autonomous payment news"),
        )

    def test_no_subcommand_defaults_to_cron_precheck(self) -> None:
        with TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(AUTONOMY_SCRIPT), "--workspace", directory],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(0, completed.returncode, msg=completed.stderr)
            self.assertEqual(
                {"wakeAgent": False, "reason": "disabled"},
                json.loads(completed.stdout),
            )

    def test_cron_wrapper_uses_configured_workspace_outside_scheduler_cwd(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scheduler_cwd = root / "scheduler"
            workspace = root / "workspace"
            scripts.mkdir()
            scheduler_cwd.mkdir()
            (workspace / "Automation").mkdir(parents=True)
            wrapper = scripts / "hermes-news-autonomy.py"
            wrapper.write_text(WRAPPER_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
            (scripts / "hermes-news-autonomy.workspace").write_text(
                str(workspace) + "\n",
                encoding="utf-8",
            )
            (workspace / "Automation" / "autonomy.py").write_text(
                "import json\n"
                "print(json.dumps({'wakeAgent': False, 'reason': 'workspace_loaded'}))\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [sys.executable, str(wrapper)],
                cwd=str(scheduler_cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
                check=False,
                env={key: value for key, value in os.environ.items() if key != "HERMES_NEWS_WORKSPACE"},
            )

            self.assertEqual(0, completed.returncode, msg=completed.stderr)
            self.assertEqual(
                {"wakeAgent": False, "reason": "workspace_loaded"},
                json.loads(completed.stdout),
            )


if __name__ == "__main__":
    unittest.main()
