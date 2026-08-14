#!/usr/bin/env python3
"""Autonomous-operation gates and controls for the Hermes news workspace."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


DEFAULT_MAXIMUM_USED_PERCENT = 80.0
DEFAULT_JOB_NAME = "Hermes autonomous payment news PR"
ALLOWED_REMOTE_URLS = frozenset(
    {
        "https://github.com/dumbbelloper/hermes-agent.git",
        "https://github.com/dumbbelloper/hermes-agent",
        "git@github.com:dumbbelloper/hermes-agent.git",
    }
)


def controller_workspace() -> Path:
    """Bind this controller to the repository that contains its source file."""
    return Path(__file__).resolve().parents[1]


def evaluate_quota(
    payload: Mapping[str, Any],
    *,
    maximum_used_percent: float = DEFAULT_MAXIMUM_USED_PERCENT,
) -> dict[str, Any]:
    """Return a fail-closed decision from a provider-native rate-limit payload."""
    limits = payload.get("rateLimits")
    if not isinstance(limits, Mapping):
        return {"allowed": False, "reason": "quota_unavailable"}
    primary = limits.get("primary")
    if not isinstance(primary, Mapping):
        return {"allowed": False, "reason": "quota_unavailable"}
    used = primary.get("usedPercent")
    if not isinstance(used, (int, float)) or isinstance(used, bool):
        return {"allowed": False, "reason": "invalid_primary_window"}
    used_percent = float(used)
    if not math.isfinite(used_percent) or not 0.0 <= used_percent <= 100.0:
        return {"allowed": False, "reason": "invalid_primary_window"}
    if (
        not math.isfinite(maximum_used_percent)
        or not 0.0 < maximum_used_percent <= 100.0
    ):
        return {"allowed": False, "reason": "invalid_quota_policy"}
    spend_control = limits.get("spendControlReached")
    if spend_control is not None and not isinstance(spend_control, bool):
        return {"allowed": False, "reason": "invalid_spend_control"}
    if spend_control is True or limits.get("rateLimitReachedType"):
        return {
            "allowed": False,
            "reason": "provider_limit_reached",
            "used_percent": used,
            "remaining_percent": 100.0 - used_percent,
            "resets_at": primary.get("resetsAt"),
        }
    allowed = used_percent < maximum_used_percent
    return {
        "allowed": allowed,
        "reason": "below_quota_threshold" if allowed else "quota_threshold_reached",
        "used_percent": used,
        "remaining_percent": 100.0 - used_percent,
        "resets_at": primary.get("resetsAt"),
    }


def is_enabled(config_path: Path, *, now: Optional[datetime] = None) -> bool:
    """Read the local autonomy switch; missing or malformed files fail closed."""
    try:
        document = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if not isinstance(document, dict) or document.get("enabled") is not True:
        return False
    approved_until = document.get("approved_until")
    if not isinstance(approved_until, str):
        return False
    try:
        expiry = datetime.fromisoformat(approved_until)
    except ValueError:
        return False
    if expiry.tzinfo is None:
        return False
    instant = now or datetime.now(timezone.utc)
    return instant.astimezone(timezone.utc) < expiry.astimezone(timezone.utc)


def write_switch(
    config_path: Path,
    *,
    enabled: bool,
    now: Optional[datetime] = None,
) -> None:
    """Atomically persist the local switch without broadening file access."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    instant = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    approved_until = instant + timedelta(days=30)
    content = json.dumps(
        {
            "enabled": enabled,
            "approved_at": instant.isoformat(),
            "approved_until": approved_until.isoformat(),
        },
        ensure_ascii=False,
        indent=2,
    )
    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{config_path.name}.",
            suffix=".tmp",
            dir=str(config_path.parent),
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            if os.name != "nt":
                os.chmod(temporary_path, 0o600)
            temporary.write(content + "\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, config_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def macos_clamshell_is_closed(
    *,
    platform_name: str = sys.platform,
    command_runner: Any = None,
) -> bool:
    """Return whether a macOS portable reports a closed display clamshell."""
    if platform_name != "darwin":
        return False
    runner = command_runner or subprocess.run
    try:
        completed = runner(
            ["/usr/sbin/ioreg", "-r", "-k", "AppleClamshellState", "-d", "4"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if completed.returncode != 0:
        return False
    match = re.search(
        r'"AppleClamshellState"\s*=\s*(Yes|No)\b',
        completed.stdout,
    )
    return bool(match and match.group(1) == "Yes")


def decide_precheck(
    *,
    enabled: bool,
    quota: Mapping[str, Any],
    repository_ready: bool,
    queue_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Combine deterministic gates without performing any side effects."""
    if not enabled:
        return {"wakeAgent": False, "reason": "disabled"}
    if quota.get("allowed") is not True:
        return {
            "wakeAgent": False,
            "reason": str(quota.get("reason") or "quota_unavailable"),
        }
    if not repository_ready:
        return {"wakeAgent": False, "reason": "repository_not_ready"}
    if queue_result.get("wakeAgent") is not True:
        return {
            "wakeAgent": False,
            "reason": str(queue_result.get("reason") or "no_changes"),
        }
    context = queue_result.get("context")
    if not isinstance(context, Mapping):
        return {"wakeAgent": False, "reason": "invalid_queue_context"}
    merged_context = dict(context)
    merged_context["quota"] = dict(quota)
    return {"wakeAgent": True, "context": merged_context}


def repository_is_ready(branch: str, porcelain_status: str) -> bool:
    """Allow unattended writes only from an unmodified primary checkout."""
    return branch.strip() == "main" and not porcelain_status.strip()


def remote_is_allowed(
    remote_url: str,
    allowed_urls: frozenset[str] = ALLOWED_REMOTE_URLS,
) -> bool:
    """Require every configured URL to have the exact approved identity."""
    configured_urls = [line.strip() for line in remote_url.splitlines() if line.strip()]
    return bool(configured_urls) and all(url in allowed_urls for url in configured_urls)


def coordinator_sync_commands() -> list[list[str]]:
    """Return the only allowed coordinator update: fetch then fast-forward."""
    return [
        ["git", "fetch", "--quiet", "origin"],
        ["git", "merge", "--ff-only", "--quiet", "origin/main"],
    ]


def control_commands(enabled: bool, job_name: str) -> list[list[str]]:
    """Return the native Hermes lifecycle commands for the requested switch state."""
    if enabled:
        return [
            ["hermes", "gateway", "start"],
            ["hermes", "cron", "resume", job_name],
        ]
    return [["hermes", "cron", "pause", job_name]]


def _slug(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:48] or fallback


def task_log_path(
    workspace: Path,
    *,
    timestamp: datetime,
    task_id: str,
    slug: str,
) -> Path:
    """Return a collision-resistant Obsidian task log path."""
    instant = timestamp.astimezone(timezone.utc)
    stamp = instant.strftime("%Y-%m-%dT%H%M%S.%fZ")
    task_component = _slug(task_id, "task")
    slug_component = _slug(slug, "work")
    return (
        workspace
        / "Work Logs"
        / instant.strftime("%Y")
        / instant.strftime("%m")
        / f"{stamp}-{task_component}-{slug_component}.md"
    )


def _json_command(
    command: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    environment: Optional[Mapping[str, str]] = None,
    timeout: int = 3300,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd else None,
            env=dict(environment) if environment else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("command failed before completion") from error
    if completed.returncode != 0:
        message = completed.stderr.strip() or "command failed"
        raise RuntimeError(message)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("command returned invalid JSON") from error
    if not isinstance(result, dict):
        raise RuntimeError("command did not return a JSON object")
    return result


def _quota_script() -> Path:
    configured = os.environ.get("HERMES_CODEX_QUOTA_SCRIPT", "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())
    hermes_home = Path(
        os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    ).expanduser()
    candidates.append(
        hermes_home
        / "skills"
        / "productivity"
        / "ai-provider-usage-monitoring"
        / "scripts"
        / "codex_rate_limits.py"
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError("cannot locate the read-only Codex quota script")


def query_quota(maximum_used_percent: float) -> dict[str, Any]:
    payload = _json_command([sys.executable, str(_quota_script())], timeout=60)
    return evaluate_quota(
        payload,
        maximum_used_percent=maximum_used_percent,
    )


def _workspace(value: Optional[str]) -> Path:
    configured = value or os.environ.get("HERMES_NEWS_WORKSPACE", "")
    if not configured:
        configured = "."
    return Path(configured).expanduser().resolve()


def _repository_ready(
    workspace: Path,
    *,
    synchronize: bool = False,
    allowed_remote_urls: frozenset[str] = ALLOWED_REMOTE_URLS,
    expected_workspace: Optional[Path] = None,
) -> bool:
    expected = (expected_workspace or controller_workspace()).resolve()
    if workspace.resolve() != expected:
        return False
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
        check=False,
    )
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
        check=False,
    )
    push_remote = subprocess.run(
        ["git", "remote", "get-url", "--push", "--all", "origin"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
        check=False,
    )
    ready = (
        branch.returncode == 0
        and status.returncode == 0
        and remote.returncode == 0
        and push_remote.returncode == 0
        and repository_is_ready(branch.stdout, status.stdout)
        and remote_is_allowed(remote.stdout, allowed_remote_urls)
        and remote_is_allowed(push_remote.stdout, allowed_remote_urls)
    )
    if not ready or not synchronize:
        return ready
    for command in coordinator_sync_commands():
        completed = subprocess.run(
            command,
            cwd=str(workspace),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            return False
    final_status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
        check=False,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
        check=False,
    )
    origin_head = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
        check=False,
    )
    return (
        final_status.returncode == 0
        and not final_status.stdout.strip()
        and head.returncode == 0
        and origin_head.returncode == 0
        and head.stdout.strip() == origin_head.stdout.strip()
    )


def autonomous_precheck_environment(
    workspace: Path,
    base_environment: Mapping[str, str],
) -> dict[str, str]:
    """Build a quota-cycle environment with bounded per-run token growth."""
    environment = dict(base_environment)
    environment["HERMES_NEWS_WORKSPACE"] = str(workspace.resolve())
    environment["HERMES_NEWS_MAX_ITEMS"] = "1"
    return environment


def _news_precheck(workspace: Path) -> dict[str, Any]:
    skill_dir = os.environ.get("HERMES_NEWS_SKILL_DIR", "").strip()
    if not skill_dir:
        hermes_home = Path(
            os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
        ).expanduser()
        skill_dir = str(hermes_home / "skills" / "hermes-news-automation")
    script = Path(skill_dir).expanduser().resolve() / "scripts" / "precheck.py"
    if not script.is_file():
        raise RuntimeError("hermes-news-automation precheck.py is missing")
    environment = autonomous_precheck_environment(workspace, os.environ)
    return _json_command(
        [sys.executable, str(script)],
        cwd=workspace,
        environment=environment,
    )


def _precheck(options: argparse.Namespace) -> int:
    workspace = _workspace(options.workspace)
    switch = workspace / ".hermes-news" / "config" / "autonomy.json"
    enabled = is_enabled(switch)
    if not enabled:
        print(json.dumps({"wakeAgent": False, "reason": "disabled"}))
        return 0
    if macos_clamshell_is_closed():
        print(json.dumps({"wakeAgent": False, "reason": "clamshell_closed"}))
        return 0
    try:
        quota = query_quota(options.maximum_used_percent)
    except RuntimeError as error:
        print(
            json.dumps(
                {"wakeAgent": False, "reason": "quota_query_failed"}
            )
        )
        print(str(error), file=sys.stderr)
        return 0
    try:
        repository_ready = _repository_ready(workspace, synchronize=True)
    except (OSError, subprocess.TimeoutExpired) as error:
        repository_ready = False
        print(f"repository gate failed: {type(error).__name__}", file=sys.stderr)
    if quota.get("allowed") is not True or not repository_ready:
        result = decide_precheck(
            enabled=True,
            quota=quota,
            repository_ready=repository_ready,
            queue_result={"wakeAgent": False, "reason": "not_started"},
        )
        print(json.dumps(result))
        return 0
    try:
        queue_result = _news_precheck(workspace)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        print(json.dumps({"wakeAgent": False, "reason": "news_precheck_failed"}))
        return 0
    result = decide_precheck(
        enabled=True,
        quota=quota,
        repository_ready=True,
        queue_result=queue_result,
    )
    print(json.dumps(result))
    return 0


def apply_control(
    *,
    enabled: bool,
    switch_path: Path,
    job_name: str,
    command_runner: Any = subprocess.run,
) -> int:
    """Apply lifecycle commands while keeping the persisted gate fail-closed."""
    write_switch(switch_path, enabled=False)
    for command in control_commands(enabled, job_name):
        try:
            completed = command_runner(command, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return 1
        if completed.returncode != 0:
            return completed.returncode
    if enabled:
        write_switch(switch_path, enabled=True)
    return 0


def _control(options: argparse.Namespace, enabled: bool) -> int:
    workspace = _workspace(options.workspace)
    if workspace != controller_workspace():
        print("workspace does not match the controller repository", file=sys.stderr)
        return 2
    switch = workspace / ".hermes-news" / "config" / "autonomy.json"
    return_code = apply_control(
        enabled=enabled,
        switch_path=switch,
        job_name=options.job_name,
    )
    if return_code != 0:
        return return_code
    print(
        json.dumps(
            {"enabled": enabled, "job_name": options.job_name},
            ensure_ascii=False,
        )
    )
    return 0


def _status(options: argparse.Namespace) -> int:
    workspace = _workspace(options.workspace)
    switch = workspace / ".hermes-news" / "config" / "autonomy.json"
    try:
        quota = query_quota(options.maximum_used_percent)
    except RuntimeError:
        quota = {"allowed": False, "reason": "quota_query_failed"}
    print(
        json.dumps(
            {
                "enabled": is_enabled(switch),
                "repository_ready": _repository_ready(workspace),
                "quota": quota,
                "job_name": options.job_name,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _task_log(options: argparse.Namespace) -> int:
    workspace = _workspace(options.workspace)
    print(
        task_log_path(
            workspace,
            timestamp=datetime.now(timezone.utc),
            task_id=options.task_id,
            slug=options.slug,
        )
    )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="autonomy.py")
    parser.add_argument("--workspace")
    parser.add_argument("--job-name", default=DEFAULT_JOB_NAME)
    parser.add_argument(
        "--maximum-used-percent",
        type=float,
        default=DEFAULT_MAXIMUM_USED_PERCENT,
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("precheck")
    commands.add_parser("on")
    commands.add_parser("off")
    commands.add_parser("status")
    task_log = commands.add_parser("task-log")
    task_log.add_argument("--task-id", required=True)
    task_log.add_argument("--slug", required=True)
    options = parser.parse_args(argv)
    if options.command in (None, "precheck"):
        return _precheck(options)
    if options.command == "on":
        return _control(options, True)
    if options.command == "off":
        return _control(options, False)
    if options.command == "status":
        return _status(options)
    return _task_log(options)


if __name__ == "__main__":
    raise SystemExit(main())
