"""Command-line interface for registry validation and collection runs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from .adapters.base import built_in_adapters
from .automation import AutomationError, UnattendedController
from .fetcher import FetchPolicy, HttpFetcher
from .note_index import VaultNoteIndex
from .pipeline import CollectorPipeline
from .registry import RegistryError, SourceRegistry
from .storage import FileStore
from .telegram import (
    TelegramError,
    TelegramNotifier,
    load_telegram_credentials,
    split_message,
)


DEFAULT_WORKSPACE = Path(
    os.environ.get("HERMES_NEWS_WORKSPACE", ".")
).expanduser().resolve()
WORKSPACE_CONFIG = (
    DEFAULT_WORKSPACE / ".hermes-news" / "config" / "sources.json"
)
DEFAULT_CONFIG = Path(
    os.getenv(
        "HERMES_NEWS_CONFIG",
        str(
            WORKSPACE_CONFIG
            if WORKSPACE_CONFIG.exists()
            else Path(__file__).with_name("default_sources.json")
        ),
    )
).expanduser()
DEFAULT_DATA_DIR = Path(
    os.getenv(
        "HERMES_NEWS_DATA_DIR",
        str(DEFAULT_WORKSPACE / ".hermes-news" / "data"),
    )
).expanduser()
DEFAULT_TELEGRAM_CONFIG = (
    DEFAULT_WORKSPACE / ".hermes-news" / "config" / "telegram.json"
)


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
        default=DEFAULT_WORKSPACE,
    )
    notes.set_defaults(handler=validate_notes)

    note_status = commands.add_parser(
        "note-status",
        help="decide whether a writer should create, skip, or queue an update",
    )
    note_status.add_argument(
        "--vault-dir",
        type=Path,
        default=DEFAULT_WORKSPACE,
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
        "--telegram-config",
        type=Path,
        default=DEFAULT_TELEGRAM_CONFIG,
    )
    telegram.add_argument(
        "--dry-run",
        action="store_true",
        help="validate files and report message chunks without sending",
    )
    telegram.set_defaults(handler=notify_telegram)

    automation_start = commands.add_parser(
        "automation-start",
        help="collect sources under a durable run lock and prepare agent work",
    )
    automation_start.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR
    )
    automation_start.add_argument(
        "--vault-dir", type=Path, default=DEFAULT_WORKSPACE
    )
    automation_start.add_argument("--source", action="append", default=[])
    automation_start.add_argument("--timeout", type=float, default=20.0)
    automation_start.add_argument("--max-response-mib", type=int, default=10)
    automation_start.add_argument("--max-items", type=int, default=5)
    automation_start.add_argument("--lock-ttl-minutes", type=int, default=180)
    automation_start.set_defaults(handler=automation_start_run)

    automation_next = commands.add_parser(
        "automation-next",
        help="claim the next pending item in an unattended run",
    )
    _automation_paths(automation_next)
    automation_next.add_argument("--run-id", required=True)
    automation_next.set_defaults(handler=automation_next_item)

    automation_reject = commands.add_parser(
        "automation-reject",
        help="finish a claimed item without publishing it",
    )
    _automation_paths(automation_reject)
    automation_reject.add_argument("--run-id", required=True)
    automation_reject.add_argument("--record-id", required=True)
    automation_reject.add_argument(
        "--disposition",
        required=True,
        choices=("irrelevant", "quarantined", "retryable"),
    )
    automation_reject.add_argument("--reason", required=True)
    automation_reject.set_defaults(handler=automation_reject_item)

    automation_submit = commands.add_parser(
        "automation-submit",
        help="validate an agent artifact and atomically write its Obsidian note",
    )
    _automation_paths(automation_submit)
    automation_submit.add_argument("--run-id", required=True)
    automation_submit.add_argument("--record-id", required=True)
    automation_submit.add_argument("--input", type=Path, required=True)
    automation_submit.set_defaults(handler=automation_submit_note)

    automation_notify = commands.add_parser(
        "automation-notify",
        help="send committed notes once using the Telegram delivery ledger",
    )
    _automation_paths(automation_notify)
    automation_notify.add_argument("--run-id", required=True)
    automation_notify.add_argument("--timeout", type=float, default=20.0)
    automation_notify.add_argument(
        "--telegram-config",
        type=Path,
        default=DEFAULT_TELEGRAM_CONFIG,
    )
    automation_notify.set_defaults(handler=automation_notify_run)

    automation_finish = commands.add_parser(
        "automation-finish",
        help="finalize a run after every queue item reaches a terminal state",
    )
    _automation_paths(automation_finish)
    automation_finish.add_argument("--run-id", required=True)
    automation_finish.set_defaults(handler=automation_finish_run)

    automation_status = commands.add_parser(
        "automation-status",
        help="show a durable unattended-run manifest and queue summary",
    )
    _automation_paths(automation_status)
    automation_status.add_argument("--run-id", required=True)
    automation_status.set_defaults(handler=automation_show_status)

    automation_abort = commands.add_parser(
        "automation-abort",
        help="abort an owned unattended run and release its logical lock",
    )
    _automation_paths(automation_abort)
    automation_abort.add_argument("--run-id", required=True)
    automation_abort.add_argument("--reason", required=True)
    automation_abort.set_defaults(handler=automation_abort_run)
    return root


def _automation_paths(command: argparse.ArgumentParser) -> None:
    command.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    command.add_argument("--vault-dir", type=Path, default=DEFAULT_WORKSPACE)


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

    bot_token, chat_id = load_telegram_credentials(arguments.telegram_config)
    notifier = TelegramNotifier(
        bot_token,
        chat_id,
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


def _controller(arguments: argparse.Namespace) -> UnattendedController:
    return UnattendedController(arguments.data_dir, arguments.vault_dir)


def automation_start_run(arguments: argparse.Namespace) -> int:
    adapters, registry = load_registry(arguments.config)
    sources = registry.select(arguments.source)
    controller = _controller(arguments)
    run_id = controller.open_run(arguments.lock_ttl_minutes)
    try:
        pipeline = CollectorPipeline(
            fetcher=HttpFetcher(
                FetchPolicy(
                    timeout_seconds=arguments.timeout,
                    max_response_bytes=(
                        arguments.max_response_mib * 1024 * 1024
                    ),
                )
            ),
            adapters=adapters,
            store=FileStore(arguments.data_dir),
        )
        reports = pipeline.run(sources)
        manifest = controller.prepare(
            run_id,
            sources,
            [item.to_dict() for item in reports],
            arguments.max_items,
        )
    except Exception as error:
        try:
            controller.abort(run_id, "automation start failed: {}".format(error))
        except AutomationError:
            pass
        raise
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def automation_next_item(arguments: argparse.Namespace) -> int:
    item = _controller(arguments).claim_next(arguments.run_id)
    print(
        json.dumps(
            {"status": "claimed", "item": item}
            if item is not None
            else {"status": "empty", "item": None},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def automation_reject_item(arguments: argparse.Namespace) -> int:
    item = _controller(arguments).reject(
        arguments.run_id,
        arguments.record_id,
        arguments.disposition,
        arguments.reason,
    )
    print(json.dumps({"status": "recorded", "item": item}, ensure_ascii=False, indent=2))
    return 0


def automation_submit_note(arguments: argparse.Namespace) -> int:
    try:
        artifact = json.loads(arguments.input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AutomationError("cannot read agent artifact JSON") from error
    if not isinstance(artifact, dict):
        raise AutomationError("agent artifact must be a JSON object")
    item = _controller(arguments).submit(
        arguments.run_id,
        arguments.record_id,
        artifact,
    )
    print(json.dumps({"status": "committed", "item": item}, ensure_ascii=False, indent=2))
    return 0


def automation_notify_run(arguments: argparse.Namespace) -> int:
    bot_token, chat_id = load_telegram_credentials(arguments.telegram_config)
    notifier = TelegramNotifier(
        bot_token,
        chat_id,
        timeout_seconds=arguments.timeout,
    )
    result = _controller(arguments).notify(arguments.run_id, notifier)
    print(json.dumps({"status": "processed", **result}, ensure_ascii=False, indent=2))
    return 0 if result["unknown_deliveries"] == 0 else 1


def automation_finish_run(arguments: argparse.Namespace) -> int:
    manifest = _controller(arguments).finish(arguments.run_id)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def automation_show_status(arguments: argparse.Namespace) -> int:
    result = _controller(arguments).status(arguments.run_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def automation_abort_run(arguments: argparse.Namespace) -> int:
    result = _controller(arguments).abort(arguments.run_id, arguments.reason)
    print(json.dumps(result, ensure_ascii=False, indent=2))
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
    except AutomationError as error:
        print(
            json.dumps(
                {
                    "status": "automation_error",
                    "message": str(error),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
