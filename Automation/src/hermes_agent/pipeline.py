"""End-to-end collection pipeline with fail-closed state transitions."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .adapters.base import AdapterError, AdapterRegistry
from .fetcher import FetchError
from .hooks import Event, Hook, NullHook
from .models import Candidate, Record, SourceConfig, utc_now
from .normalize import NormalizationError, normalize_candidate
from .storage import ChangeSummary, FileStore
from .validation import ValidationIssue, validate_record


class QualityGateError(RuntimeError):
    def __init__(self, message: str, kind: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class SourceReport:
    source_id: str
    run_id: str
    status: str
    fetched_candidates: int = 0
    accepted_records: int = 0
    quarantined_records: int = 0
    duplicate_records: int = 0
    changes: Optional[ChangeSummary] = None
    error_kind: Optional[str] = None
    error_message: Optional[str] = None
    retryable: bool = False

    def to_dict(self) -> Mapping[str, Any]:
        value = asdict(self)
        if self.changes is not None:
            value["changes"] = asdict(self.changes)
        return value


class CollectorPipeline:
    def __init__(
        self,
        fetcher: Any,
        adapters: AdapterRegistry,
        store: FileStore,
        hook: Optional[Hook] = None,
    ) -> None:
        self.fetcher = fetcher
        self.adapters = adapters
        self.store = store
        self.hook = hook or NullHook()

    def run(self, sources: Iterable[SourceConfig]) -> Sequence[SourceReport]:
        return tuple(self.collect(source) for source in sources)

    def collect(self, source: SourceConfig) -> SourceReport:
        run_id = self._run_id()
        self._emit("before_fetch", source, run_id)
        try:
            response = self.fetcher.fetch(source)
            raw = self.store.save_raw(source, run_id, response)
            self._emit(
                "after_fetch",
                source,
                run_id,
                {
                    "status": response.status,
                    "bytes": len(response.body),
                    "body_sha256": raw["body_sha256"],
                },
            )
            adapter = self.adapters.create(source.adapter)
            candidates = list(adapter.parse(source, response))
            records, quarantine, duplicate_count = self._normalize(
                source,
                candidates,
            )
            self.store.save_quarantine(source.id, run_id, quarantine)
            self._quality_gate(source, candidates, records, quarantine)
            changes = self.store.commit_success(
                source,
                run_id,
                records,
                raw_sha256=raw["body_sha256"],
                quarantined=len(quarantine),
            )
            report = SourceReport(
                source_id=source.id,
                run_id=run_id,
                status="success",
                fetched_candidates=len(candidates),
                accepted_records=len(records),
                quarantined_records=len(quarantine),
                duplicate_records=duplicate_count,
                changes=changes,
            )
            self._emit("source_succeeded", source, run_id, report.to_dict())
            return report
        except Exception as error:
            kind, retryable = self._classify_error(error)
            self.store.record_failure(
                source,
                run_id,
                kind=kind,
                message=str(error),
                retryable=retryable,
            )
            report = SourceReport(
                source_id=source.id,
                run_id=run_id,
                status="failed",
                error_kind=kind,
                error_message=str(error),
                retryable=retryable,
            )
            self._emit("source_failed", source, run_id, report.to_dict())
            return report

    def _normalize(
        self,
        source: SourceConfig,
        candidates: Sequence[Candidate],
    ):
        discovered_at = utc_now()
        records_by_id: Dict[str, Record] = {}
        quarantine: List[Mapping[str, Any]] = []
        duplicate_count = 0
        for index, candidate in enumerate(candidates):
            try:
                record = normalize_candidate(source, candidate, discovered_at)
                issues = validate_record(source, record, date.today())
                if issues:
                    quarantine.append(
                        self._quarantine_row(index, candidate, issues)
                    )
                    continue
                if record.id in records_by_id:
                    duplicate_count += 1
                    continue
                records_by_id[record.id] = record
            except NormalizationError as error:
                quarantine.append(
                    {
                        "candidate_index": index,
                        "candidate": asdict(candidate),
                        "issues": [
                            {
                                "field": "candidate",
                                "code": "normalization_error",
                                "message": str(error),
                            }
                        ],
                    }
                )
        return tuple(records_by_id.values()), quarantine, duplicate_count

    @staticmethod
    def _quarantine_row(
        index: int,
        candidate: Candidate,
        issues: Sequence[ValidationIssue],
    ) -> Mapping[str, Any]:
        return {
            "candidate_index": index,
            "candidate": asdict(candidate),
            "issues": [asdict(issue) for issue in issues],
        }

    @staticmethod
    def _quality_gate(
        source: SourceConfig,
        candidates: Sequence[Candidate],
        records: Sequence[Record],
        quarantine: Sequence[Mapping[str, Any]],
    ) -> None:
        if not candidates:
            raise QualityGateError(
                "adapter returned an empty snapshot",
                kind="unexpected_empty_snapshot",
            )
        if not records:
            raise QualityGateError(
                "all candidates were quarantined",
                kind="all_records_quarantined",
            )
        maximum_ratio = float(
            source.options.get("max_quarantine_ratio", 0.10)
        )
        ratio = len(quarantine) / len(candidates)
        if ratio > maximum_ratio:
            raise QualityGateError(
                "quarantine ratio {:.1%} exceeds {:.1%}".format(
                    ratio, maximum_ratio
                ),
                kind="quarantine_ratio_exceeded",
            )

    @staticmethod
    def _classify_error(error: Exception):
        if isinstance(error, FetchError):
            return error.kind, error.retryable
        if isinstance(error, QualityGateError):
            return error.kind, False
        if isinstance(error, AdapterError):
            return "adapter_degraded", False
        return "unexpected_error", False

    def _emit(
        self,
        name: str,
        source: SourceConfig,
        run_id: str,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.hook.handle(
            Event(
                name=name,
                source_id=source.id,
                run_id=run_id,
                payload=payload or {},
            )
        )

    @staticmethod
    def _run_id() -> str:
        timestamp = utc_now().strftime("%Y%m%dT%H%M%S%fZ")
        return "{}-{}".format(timestamp, uuid.uuid4().hex[:8])
