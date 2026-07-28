#!/usr/bin/env python3
"""Cross-platform launcher for the repository-local hermes_agent package."""

from __future__ import annotations

import sys
import os
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = (
    REPOSITORY_ROOT
    / "skills"
    / "hermes-news-automation"
    / "scripts"
    / "runtime"
)
os.environ.setdefault("HERMES_NEWS_WORKSPACE", str(REPOSITORY_ROOT))
os.environ.setdefault(
    "HERMES_NEWS_CONFIG",
    str(REPOSITORY_ROOT / "Automation" / "config" / "sources.json"),
)
os.environ.setdefault(
    "HERMES_NEWS_DATA_DIR",
    str(REPOSITORY_ROOT / "Automation" / "data"),
)
sys.path.insert(0, str(SOURCE_DIR))

from hermes_agent.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
