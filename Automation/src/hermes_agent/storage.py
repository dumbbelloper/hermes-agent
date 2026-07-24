"""Atomic filesystem storage for raw responses, records, quarantine, and state."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .models import FetchResult, Record, SourceConfig, isoformat_utc, utc_now


SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _jsonl_bytes(values: Iterable[Mapping[str, Any]]) -> bytes:
    return "".join(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
        for value in values
    ).encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}.".format(path.name),
        dir=str(path.parent),
    )
    try:
        with os.fdopen(file_descriptor, "wb") as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def record_fingerprint(record: Record) -> str:
    value = record.to_dict()
    value.pop("discovered_at", None)
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChangeSummary:
    new: int
    updated: int
    unchanged: int
    missing_from_snapshot: int
    current_total: int


class FileStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    @staticmethod
    def _safe(value: str) -> str:
        if not SAFE_NAME.fullmatch(value):
            raise ValueError("unsafe storage name: {!r}".format(value))
        return value

    def save_raw(
        self,
        source: SourceConfig,
        run_id: str,
        response: FetchResult,
    ) -> Mapping[str, str]:
        source_id = self._safe(source.id)
        run_name = self._safe(run_id)
        extension = self._extension(response.headers.get("content-type", ""))
        raw_path = self.root / "raw" / source_id / (run_name + extension)
        metadata_path = self.root / "raw" / source_id / (run_name + ".meta.json")
        digest = hashlib.sha256(response.body).hexdigest()
        _atomic_write(raw_path, response.body)
        _atomic_write(
            metadata_path,
            _json_bytes(
                {
                    "source_id": source.id,
                    "requested_url": response.requested_url,
                    "final_url": response.final_url,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "fetched_at": isoformat_utc(response.fetched_at),
                    "body_bytes": len(response.body),
                    "body_sha256": digest,
                }
            ),
        )
        return {
            "raw_path": str(raw_path),
            "metadata_path": str(metadata_path),
            "body_sha256": digest,
        }

    @staticmethod
    def _extension(content_type: str) -> str:
        lowered = content_type.lower()
        if "json" in lowered:
            return ".json"
        if "xml" in lowered or "rss" in lowered or "atom" in lowered:
            return ".xml"
        if "html" in lowered:
            return ".html"
        return ".bin"

    def current_path(self, source_id: str) -> Path:
        return (
            self.root
            / "normalized"
            / "current"
            / (self._safe(source_id) + ".jsonl")
        )

    def state_path(self, source_id: str) -> Path:
        return self.root / "state" / (self._safe(source_id) + ".json")

    def load_current(self, source_id: str) -> Sequence[Record]:
        path = self.current_path(source_id)
        if not path.exists():
            return ()
        records = []
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line:
                continue
            try:
                records.append(Record.from_dict(json.loads(line)))
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                raise ValueError(
                    "invalid current state {} at line {}".format(
                        path, line_number
                    )
                ) from error
        return tuple(records)

    def load_state(self, source_id: str) -> Mapping[str, Any]:
        path = self.state_path(source_id)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def commit_success(
        self,
        source: SourceConfig,
        run_id: str,
        incoming_records: Sequence[Record],
        raw_sha256: str,
        quarantined: int,
    ) -> ChangeSummary:
        previous = {record.id: record for record in self.load_current(source.id)}
        incoming = {record.id: record for record in incoming_records}
        merged: Dict[str, Record] = dict(previous)
        new_count = 0
        updated_count = 0
        unchanged_count = 0
        for record_id, record in incoming.items():
            old = previous.get(record_id)
            if old is None:
                new_count += 1
                merged[record_id] = record
            elif record_fingerprint(old) == record_fingerprint(record):
                unchanged_count += 1
                merged[record_id] = old
            else:
                updated_count += 1
                merged[record_id] = replace(
                    record,
                    discovered_at=old.discovered_at,
                )

        missing_count = len(set(previous) - set(incoming))
        snapshot_values = [
            record.to_dict() for record in self._sort_records(incoming.values())
        ]
        current_values = [
            record.to_dict() for record in self._sort_records(merged.values())
        ]
        snapshot_content = _jsonl_bytes(snapshot_values)
        current_content = _jsonl_bytes(current_values)
        snapshot_path = (
            self.root
            / "normalized"
            / "snapshots"
            / self._safe(source.id)
            / (self._safe(run_id) + ".jsonl")
        )
        _atomic_write(snapshot_path, snapshot_content)
        _atomic_write(self.current_path(source.id), current_content)

        previous_state = dict(self.load_state(source.id))
        state = {
            "source_id": source.id,
            "status": "healthy",
            "last_success_at": isoformat_utc(utc_now()),
            "last_run_id": run_id,
            "consecutive_failures": 0,
            "snapshot_records": len(incoming_records),
            "current_records": len(merged),
            "quarantined_records": quarantined,
            "snapshot_sha256": hashlib.sha256(snapshot_content).hexdigest(),
            "raw_sha256": raw_sha256,
            "previous_failure": previous_state.get("last_failure"),
        }
        _atomic_write(self.state_path(source.id), _json_bytes(state))
        return ChangeSummary(
            new=new_count,
            updated=updated_count,
            unchanged=unchanged_count,
            missing_from_snapshot=missing_count,
            current_total=len(merged),
        )

    def record_failure(
        self,
        source: SourceConfig,
        run_id: str,
        kind: str,
        message: str,
        retryable: bool,
    ) -> Mapping[str, Any]:
        old_state = dict(self.load_state(source.id))
        failures = int(old_state.get("consecutive_failures", 0)) + 1
        state = dict(old_state)
        state.update(
            {
                "source_id": source.id,
                "status": "unhealthy" if failures >= 3 else "degraded",
                "last_run_id": run_id,
                "consecutive_failures": failures,
                "last_failure": {
                    "at": isoformat_utc(utc_now()),
                    "kind": kind,
                    "message": message,
                    "retryable": retryable,
                },
            }
        )
        _atomic_write(self.state_path(source.id), _json_bytes(state))
        return state

    def save_quarantine(
        self,
        source_id: str,
        run_id: str,
        rows: Sequence[Mapping[str, Any]],
    ) -> None:
        if not rows:
            return
        path = (
            self.root
            / "quarantine"
            / self._safe(source_id)
            / (self._safe(run_id) + ".jsonl")
        )
        _atomic_write(path, _jsonl_bytes(rows))

    @staticmethod
    def _sort_records(records: Iterable[Record]) -> List[Record]:
        return sorted(
            records,
            key=lambda item: (item.published_at, item.id),
            reverse=True,
        )

