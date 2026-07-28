"""Command-line interface for registry validation and collection runs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from .adapters.base import built_in_adapters
from .fetcher import FetchPolicy, HttpFetcher
from .note_index import VaultNoteIndex
from .pipeline import CollectorPipeline
from .registry import RegistryError, SourceRegistry
from .storage import FileStore
from .telegram import TelegramError, TelegramNotifier, split_message


DEFAULT_CONFIG = Path(__file__).with_name("default_sources.json")
DEFAULT_DATA_DIR = Path("Automation/data")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="hermes-collector",
        description="Collect trusted payment ecosystem source metadata.",
    )
    root.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Source Registry JSON path",
    )
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser(
        "validate-registry",
        help="validate configuration without network access",
    )
    validate.set_defaults(handler=validate_registry)

    collect = commands.add_parser(
        "collect",
        help="fetch and persist enabled sources",
    )
    collect.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
    )
    collect.add_argument(
        "--source",
        action="append",
        default=[],
        help="source id to run; repeat to select multiple",
    )
    collect.add_argument("--timeout", type=float, default=20.0)
    collect.add_argument(
        "--max-response-mib",
        type=int,
        default=10,
    )
    collect.set_defaults(handler=collect_sources)

    state = commands.add_parser(
        "show-state",
        help="show persisted health and checkpoint state",
    )
    state.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
    )
    state.add_argument("--source", required=True)
    state.set_defaults(handler=show_state)

    notes = commands.add_parser(
        "validate-notes",
        help="validate note identity fields and duplicate record ids",
    )
    notes.add_argument(
        "--vault-dir",
        type=Path,
        default=Path("."),
    )
    notes.set_defaults(handler=validate_notes)

    note_status = commands.add_parser(
        "note-status",
        help="decide whether a writer should create, skip, or queue an update",
    )
    note_status.add_argument(
        "--vault-dir",
        type=Path,
        default=Path("."),
    )
    note_status.add_argument("--record-id", required=True)
    note_status.add_argument("--source-fingerprint", required=True)
    note_status.set_defaults(handler=show_note_status)

    telegram = commands.add_parser(
        "notify-telegram",
        help="send complete Markdown documents through the Telegram Bot API",
    )
    telegram.add_argument(
        "--file",
        action="append",
        type=Path,
        required=True,
        help="UTF-8 Markdown file to send; repeat for multiple documents",
    )
    telegram.add_argument("--timeout", type=float, default=20.0)
    telegram.add_argument(
        "--dry-run",
        action="store_true",
        help="validate files and report message chunks without sending",
    )
    telegram.set_defaults(handler=notify_telegram)
    return root


def load_registry(path: Path):
    adapters = built_in_adapters()
    return adapters, SourceRegistry.load(path, adapters)


def validate_registry(arguments: argparse.Namespace) -> int:
    _, registry = load_registry(arguments.config)
    print(
        json.dumps(
            {
                "schema_version": registry.schema_version,
                "sources": len(registry.sources),
                "enabled": sum(source.enabled for source in registry.sources),
                "source_ids": [source.id for source in registry.sources],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def collect_sources(arguments: argparse.Namespace) -> int:
    adapters, registry = load_registry(arguments.config)
    sources = registry.select(arguments.source)
    policy = FetchPolicy(
        timeout_seconds=arguments.timeout,
        max_response_bytes=arguments.max_response_mib * 1024 * 1024,
    )
    pipeline = CollectorPipeline(
        fetcher=HttpFetcher(policy),
        adapters=adapters,
        store=FileStore(arguments.data_dir),
    )
    reports = pipeline.run(sources)
    print(
        json.dumps(
            {
                "sources_requested": len(sources),
                "succeeded": sum(item.status == "success" for item in reports),
                "failed": sum(item.status == "failed" for item in reports),
                "reports": [item.to_dict() for item in reports],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if any(item.status == "failed" for item in reports) else 0


def show_state(arguments: argparse.Namespace) -> int:
    store = FileStore(arguments.data_dir)
    state = store.load_state(arguments.source)
    if not state:
        print(
            json.dumps(
                {
                    "source_id": arguments.source,
                    "status": "not_collected",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def validate_notes(arguments: argparse.Namespace) -> int:
    index = VaultNoteIndex.scan(arguments.vault_dir)
    print(json.dumps(index.to_dict(), ensure_ascii=False, indent=2))
    return 1 if index.issues else 0


def show_note_status(arguments: argparse.Namespace) -> int:
    index = VaultNoteIndex.scan(arguments.vault_dir)
    if index.issues:
        print(
            json.dumps(index.to_dict(), ensure_ascii=False, indent=2),
            file=sys.stderr,
        )
        return 2
    try:
        decision = index.decision(
            arguments.record_id,
            arguments.source_fingerprint,
        )
    except ValueError as error:
        print(
            json.dumps(
                {
                    "status": "invalid_identity",
                    "message": str(error),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2))
    return 0


def notify_telegram(arguments: argparse.Namespace) -> int:
    if arguments.dry_run:
        documents = []
        total_chunks = 0
        for path in arguments.file:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                raise TelegramError(
                    "cannot read Telegram document: {}".format(path)
                ) from error
            chunks = len(split_message(content))
            documents.append({"path": str(path), "chunks": chunks})
            total_chunks += chunks
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "documents": documents,
                    "messages": total_chunks,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    notifier = TelegramNotifier(
        os.environ.get("HERMES_TELEGRAM_BOT_TOKEN", ""),
        os.environ.get("HERMES_TELEGRAM_CHAT_ID", ""),
        timeout_seconds=arguments.timeout,
    )
    messages = notifier.send_files(arguments.file)
    print(
        json.dumps(
            {
                "status": "sent",
                "documents": len(arguments.file),
                "messages": messages,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        return int(arguments.handler(arguments))
    except RegistryError as error:
        print(
            json.dumps(
                {
                    "status": "configuration_error",
                    "message": str(error),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    except TelegramError as error:
        print(
            json.dumps(
                {
                    "status": "telegram_error",
                    "message": str(error),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
