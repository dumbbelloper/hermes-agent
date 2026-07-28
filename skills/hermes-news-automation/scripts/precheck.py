#!/usr/bin/env python3
"""Hermes cron wakeAgent gate for the payment-news automation skill."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _runner() -> Path:
    configured = os.environ.get("HERMES_NEWS_SKILL_DIR", "").strip()
    candidates = []
    if configured:
        value = Path(configured).expanduser()
        candidates.extend((value / "scripts" / "run.py", value / "run.py"))
    candidates.append(Path(__file__).resolve().parent / "run.py")
    hermes_home = Path(
        os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    ).expanduser()
    candidates.append(
        hermes_home
        / "skills"
        / "hermes-news-automation"
        / "scripts"
        / "run.py"
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError(
        "cannot locate hermes-news-automation scripts/run.py; "
        "set HERMES_NEWS_SKILL_DIR"
    )


def _command(workspace: Path, runner: Path, *arguments: str):
    environment = os.environ.copy()
    environment["HERMES_NEWS_WORKSPACE"] = str(workspace)
    return subprocess.run(
        [sys.executable, str(runner), *arguments],
        cwd=str(workspace),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=3300,
        check=False,
    )


def _json_output(completed: subprocess.CompletedProcess):
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("automation command returned invalid JSON") from error
    if not isinstance(value, dict):
        raise RuntimeError("automation command did not return a JSON object")
    return value


def main() -> int:
    configured = os.environ.get("HERMES_NEWS_WORKSPACE", "").strip()
    if not configured:
        print("HERMES_NEWS_WORKSPACE is required", file=sys.stderr)
        return 2
    workspace = Path(configured).expanduser().resolve()
    if not (workspace / "Inbox").is_dir():
        print(
            "HERMES_NEWS_WORKSPACE is not initialized; run scripts/run.py init",
            file=sys.stderr,
        )
        return 2
    try:
        runner = _runner()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2

    maximum = os.environ.get("HERMES_NEWS_MAX_ITEMS", "5").strip()
    start = _command(
        workspace,
        runner,
        "automation-start",
        "--max-items",
        maximum,
    )
    if start.returncode != 0:
        try:
            error = json.loads(start.stderr)
        except json.JSONDecodeError:
            error = {}
        message = str(error.get("message", ""))
        if "owns the automation lock" in message:
            print(json.dumps({"wakeAgent": False, "reason": "run_active"}))
            return 0
        sys.stderr.write(start.stderr or "automation-start failed\n")
        return start.returncode

    manifest = _json_output(start)
    run_id = str(manifest["run_id"])
    queue_items = int(manifest.get("queue_items", 0))
    if queue_items:
        print(
            json.dumps(
                {
                    "wakeAgent": True,
                    "context": {
                        "run_id": run_id,
                        "queue_items": queue_items,
                    },
                }
            )
        )
        return 0

    finish = _command(
        workspace,
        runner,
        "automation-finish",
        "--run-id",
        run_id,
    )
    if finish.returncode != 0:
        sys.stderr.write(finish.stderr or "automation-finish failed\n")
        return finish.returncode
    print(json.dumps({"wakeAgent": False, "reason": "no_changes"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
