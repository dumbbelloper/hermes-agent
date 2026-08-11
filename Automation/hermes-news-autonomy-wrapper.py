#!/usr/bin/env python3
"""Cron pre-run wrapper for the checked-out autonomous operations controller."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


workspace = Path(
    os.environ.get("HERMES_NEWS_WORKSPACE", str(Path.cwd()))
).expanduser().resolve()
controller = workspace / "Automation" / "autonomy.py"
if not controller.is_file():
    print('{"wakeAgent":false,"reason":"controller_missing"}')
    raise SystemExit(0)
sys.argv = [str(controller), "--workspace", str(workspace), "precheck"]
runpy.run_path(str(controller), run_name="__main__")
