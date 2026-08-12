#!/usr/bin/env python3
"""Cron pre-run wrapper for the checked-out autonomous operations controller."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


workspace_value = os.environ.get("HERMES_NEWS_WORKSPACE", "").strip()
if not workspace_value:
    workspace_file = Path(__file__).with_suffix(".workspace")
    try:
        workspace_value = workspace_file.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        workspace_value = ""
workspace = Path(workspace_value or Path.cwd()).expanduser().resolve()
controller = workspace / "Automation" / "autonomy.py"
if not controller.is_file():
    print('{"wakeAgent":false,"reason":"controller_missing"}')
    raise SystemExit(0)
sys.argv = [str(controller), "--workspace", str(workspace), "precheck"]
runpy.run_path(str(controller), run_name="__main__")
