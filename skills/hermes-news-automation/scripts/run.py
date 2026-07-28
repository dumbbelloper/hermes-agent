#!/usr/bin/env python3
"""Self-contained entrypoint for the Hermes news automation skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = SCRIPT_DIR / "runtime"
PACKAGE_DIR = RUNTIME_DIR / "hermes_agent"
DEFAULT_CONFIG = PACKAGE_DIR / "default_sources.json"


def _workspace(value: Optional[str] = None) -> Path:
    configured = value or os.environ.get("HERMES_NEWS_WORKSPACE", "")
    return Path(configured or ".").expanduser().resolve()


def _set_workspace(path: Path) -> None:
    os.environ["HERMES_NEWS_WORKSPACE"] = str(path)


def _initialize(arguments: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="run.py init")
    parser.add_argument("--workspace", required=True)
    options = parser.parse_args(arguments)
    workspace = _workspace(options.workspace)
    state_root = workspace / ".hermes-news"
    config = state_root / "config" / "sources.json"
    for path in (
        workspace / "Inbox",
        state_root / "data",
        state_root / "tmp",
        config.parent,
    ):
        path.mkdir(parents=True, exist_ok=True)
    created_config = not config.exists()
    if created_config:
        shutil.copyfile(DEFAULT_CONFIG, config)
    print(
        json.dumps(
            {
                "status": "initialized",
                "workspace": str(workspace),
                "config": str(config),
                "config_created": created_config,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _doctor(arguments: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="run.py doctor")
    parser.add_argument("--workspace")
    options = parser.parse_args(arguments)
    workspace = _workspace(options.workspace)
    config = workspace / ".hermes-news" / "config" / "sources.json"
    checks = {
        "python_3_9_or_newer": sys.version_info >= (3, 9),
        "runtime_present": (PACKAGE_DIR / "cli.py").is_file(),
        "workspace_exists": workspace.is_dir(),
        "inbox_exists": (workspace / "Inbox").is_dir(),
        "config_exists": config.is_file(),
        "telegram_bot_token_set": bool(
            os.environ.get("HERMES_TELEGRAM_BOT_TOKEN", "").strip()
        ),
        "telegram_chat_id_set": bool(
            os.environ.get("HERMES_TELEGRAM_CHAT_ID", "").strip()
        ),
    }
    status = "ok" if all(checks.values()) else "configuration_error"
    print(
        json.dumps(
            {
                "status": status,
                "workspace": str(workspace),
                "checks": checks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if status == "ok" else 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    if arguments and arguments[0] == "init":
        return _initialize(arguments[1:])
    if arguments and arguments[0] == "doctor":
        return _doctor(arguments[1:])

    workspace = _workspace()
    _set_workspace(workspace)
    sys.path.insert(0, str(RUNTIME_DIR))
    from hermes_agent.cli import main as runtime_main

    return runtime_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
