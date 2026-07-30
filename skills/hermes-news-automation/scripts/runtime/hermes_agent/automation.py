"""Durable unattended-run state, agent artifact validation, and note delivery."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlsplit

from .models import Record, SourceConfig, isoformat_utc, utc_now
from .note_index import VaultNoteIndex
from .storage import FileStore, record_fingerprint
from .telegram import TelegramError, TelegramNotifier

try:
    import fcntl
except ImportError:  # pragma: no cover - unavailable on native Windows.
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - unavailable on POSIX.
    msvcrt = None


AUTOMATION_SCHEMA_VERSION = "1.0"
GENERATOR_VERSION = "0.2.0"
QUEUE_STATES = {
    "pending",
    "processing",
    "irrelevant",
    "quarantined",
    "retryable",
    "committed",
    "notified",
    "notify_unknown",
}
FINAL_DECISIONS = {"irrelevant", "quarantined"}
SAFE_EVENT_KEY = re.compile(r"^[a-z0-9][a-z0-9._-]{7,127}$")
HANGUL = re.compile(r"[가-힣]")
FORBIDDEN_OUTPUT = (
    "HERMES_TELEGRAM_BOT_TOKEN",
    "HERMES_TELEGRAM_CHAT_ID",
    "BEGIN PRIVATE KEY",
    " ".join(("ignore", "previous", "instructions")),
    "reveal the system prompt",
)


class AutomationError(RuntimeError):
    pass


class RunBusyError(AutomationError):
    pass


class ArtifactValidationError(AutomationError):
    def __init__(self, issues: Sequence[str]) -> None:
        super().__init__("agent artifact validation failed: " + "; ".join(issues))
        self.issues = tuple(issues)


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}.".format(path.name),
        dir=str(path.parent),
    )
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AutomationError("invalid automation state: {}".format(path)) from error


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


def _queue_key(record_id: str, fingerprint: str) -> str:
    value = "{}\n{}".format(record_id, fingerprint).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _yaml_string(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _bounded_text(
    value: Any,
    name: str,
    minimum: int,
    maximum: int,
    issues: List[str],
    require_korean: bool = False,
) -> str:
    if not isinstance(value, str):
        issues.append("{} must be a string".format(name))
        return ""
    text = value.strip()
    if len(text) < minimum or len(text) > maximum:
        issues.append(
            "{} length must be between {} and {}".format(name, minimum, maximum)
        )
    if require_korean and not HANGUL.search(text):
        issues.append("{} must contain Korean text".format(name))
    return text


@contextmanager
def _state_mutex(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:
            handle.seek(0)
            if not handle.read(1):
                handle.seek(0)
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            raise AutomationError("filesystem locking is unavailable")
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            else:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


class AutomationStore:
    """Atomic state store shared by short-lived Hermes CLI invocations."""

    def __init__(self, data_dir: Path) -> None:
        self.root = data_dir / "automation"
        self.mutex_path = self.root / ".state.lock"
        self.active_path = self.root / "active-run.json"
        self.decisions_path = self.root / "decisions.json"
        self.deliveries_path = self.root / "deliveries.json"
        self.events_path = self.root / "events.json"

    def run_dir(self, run_id: str) -> Path:
        if not re.fullmatch(r"[0-9A-Za-z._-]+", run_id):
            raise AutomationError("unsafe run id")
        return self.root / "runs" / run_id

    def manifest_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "manifest.json"

    def queue_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "queue.json"

    def artifact_path(self, run_id: str, record_id: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{64}", record_id):
            raise AutomationError("unsafe record id")
        return self.run_dir(run_id) / "artifacts" / (record_id + ".json")

    def acquire(self, run_id: str, ttl_minutes: int) -> None:
        now = utc_now()
        with _state_mutex(self.mutex_path):
            active = _load_json(self.active_path, {})
            if active:
                expires_at = _parse_time(str(active["expires_at"]))
                if expires_at > now:
                    raise RunBusyError(
                        "run {} owns the automation lock until {}".format(
                            active.get("run_id"), active.get("expires_at")
                        )
                    )
                stale_id = str(active.get("run_id", ""))
                if stale_id:
                    stale = _load_json(self.manifest_path(stale_id), {})
                    if stale:
                        stale["status"] = "abandoned"
                        stale["finished_at"] = isoformat_utc(now)
                        stale["error"] = "logical run lock expired"
                        _atomic_write(
                            self.manifest_path(stale_id), _json_bytes(stale)
                        )
            _atomic_write(
                self.active_path,
                _json_bytes(
                    {
                        "run_id": run_id,
                        "acquired_at": isoformat_utc(now),
                        "expires_at": isoformat_utc(
                            now + timedelta(minutes=ttl_minutes)
                        ),
                    }
                ),
            )

    def assert_owner(self, run_id: str) -> None:
        active = _load_json(self.active_path, {})
        if active.get("run_id") != run_id:
            raise AutomationError("run does not own the active automation lock")

    def release(self, run_id: str) -> None:
        with _state_mutex(self.mutex_path):
            active = _load_json(self.active_path, {})
            if not active:
                return
            if active.get("run_id") != run_id:
                raise AutomationError("cannot release another run's lock")
            self.active_path.unlink()

    def save_manifest(self, run_id: str, value: Mapping[str, Any]) -> None:
        _atomic_write(self.manifest_path(run_id), _json_bytes(value))

    def load_manifest(self, run_id: str) -> Dict[str, Any]:
        value = _load_json(self.manifest_path(run_id), {})
        if not value:
            raise AutomationError("unknown run: {}".format(run_id))
        return dict(value)

    def save_queue(self, run_id: str, items: Sequence[Mapping[str, Any]]) -> None:
        _atomic_write(self.queue_path(run_id), _json_bytes(list(items)))

    def load_queue(self, run_id: str) -> List[Dict[str, Any]]:
        value = _load_json(self.queue_path(run_id), [])
        if not isinstance(value, list):
            raise AutomationError("run queue must be a JSON array")
        return [dict(item) for item in value]

    def save_artifact(
        self,
        run_id: str,
        record_id: str,
        value: Mapping[str, Any],
    ) -> str:
        path = self.artifact_path(run_id, record_id)
        _atomic_write(path, _json_bytes(value))
        return path.relative_to(self.run_dir(run_id)).as_posix()

    def mutate_queue(self, run_id: str, mutator):
        with _state_mutex(self.mutex_path):
            self.assert_owner(run_id)
            queue = self.load_queue(run_id)
            result = mutator(queue)
            self.save_queue(run_id, queue)
            return result

    def decisions(self) -> Dict[str, Any]:
        return dict(_load_json(self.decisions_path, {}))

    def record_decision(
        self,
        item: Mapping[str, Any],
        status: str,
        reason: str,
    ) -> None:
        with _state_mutex(self.mutex_path):
            values = self.decisions()
            values[str(item["item_key"])] = {
                "record_id": item["record"]["id"],
                "source_fingerprint": item["source_fingerprint"],
                "status": status,
                "reason": reason,
                "decided_at": isoformat_utc(utc_now()),
            }
            _atomic_write(self.decisions_path, _json_bytes(values))

    def reserve_delivery(self, key: str, item: Mapping[str, Any]) -> bool:
        with _state_mutex(self.mutex_path):
            deliveries = dict(_load_json(self.deliveries_path, {}))
            if key in deliveries:
                return False
            deliveries[key] = {
                "status": "sending",
                "record_id": item["record"]["id"],
                "source_fingerprint": item["source_fingerprint"],
                "reserved_at": isoformat_utc(utc_now()),
            }
            _atomic_write(self.deliveries_path, _json_bytes(deliveries))
            return True

    def finish_delivery(
        self,
        key: str,
        status: str,
        messages: int = 0,
        error: Optional[str] = None,
    ) -> None:
        with _state_mutex(self.mutex_path):
            deliveries = dict(_load_json(self.deliveries_path, {}))
            entry = dict(deliveries.get(key, {}))
            if not entry:
                raise AutomationError("delivery was not reserved")
            entry.update(
                {
                    "status": status,
                    "finished_at": isoformat_utc(utc_now()),
                    "messages": messages,
                }
            )
            if error:
                entry["error"] = error
            deliveries[key] = entry
            _atomic_write(self.deliveries_path, _json_bytes(deliveries))

    def reserve_event(
        self,
        event_key: str,
        item: Mapping[str, Any],
    ) -> Optional[Mapping[str, Any]]:
        with _state_mutex(self.mutex_path):
            events = dict(_load_json(self.events_path, {}))
            existing = events.get(event_key)
            if existing and existing.get("record_id") != item["record"]["id"]:
                return dict(existing)
            events[event_key] = {
                "status": "reserved",
                "record_id": item["record"]["id"],
                "source_fingerprint": item["source_fingerprint"],
                "reserved_at": isoformat_utc(utc_now()),
            }
            _atomic_write(self.events_path, _json_bytes(events))
            return None

    def finish_event(
        self,
        event_key: str,
        item: Mapping[str, Any],
        note_path: str,
    ) -> None:
        with _state_mutex(self.mutex_path):
            events = dict(_load_json(self.events_path, {}))
            entry = dict(events.get(event_key, {}))
            if entry.get("record_id") != item["record"]["id"]:
                raise AutomationError("event reservation owner changed")
            entry.update(
                {
                    "status": "committed",
                    "source_fingerprint": item["source_fingerprint"],
                    "note_path": note_path,
                    "finished_at": isoformat_utc(utc_now()),
                }
            )
            events[event_key] = entry
            _atomic_write(self.events_path, _json_bytes(events))

    def release_event(self, event_key: str, record_id: str) -> None:
        with _state_mutex(self.mutex_path):
            events = dict(_load_json(self.events_path, {}))
            entry = events.get(event_key)
            if (
                entry
                and entry.get("record_id") == record_id
                and entry.get("status") == "reserved"
            ):
                events.pop(event_key)
                _atomic_write(self.events_path, _json_bytes(events))


class AgentArtifact:
    """Validated semantic output produced by Curator, Writer, and Verifier."""

    REQUIRED_CHECKS = (
        "facts_supported",
        "entities_match",
        "dates_match",
        "numbers_match",
        "source_type_clear",
        "no_unsupported_claims",
        "prompt_injection_ignored",
    )

    def __init__(self, value: Mapping[str, Any], item: Mapping[str, Any]) -> None:
        self.value = dict(value)
        self.item = item
        self.issues: List[str] = []
        self.record = Record.from_dict(item["record"])
        self._validate()
        if self.issues:
            raise ArtifactValidationError(self.issues)

    def _validate(self) -> None:
        if self.value.get("artifact_schema_version") != AUTOMATION_SCHEMA_VERSION:
            self.issues.append("artifact_schema_version must be 1.0")
        if self.value.get("record_id") != self.record.id:
            self.issues.append("record_id does not match the claimed item")
        if self.value.get("source_fingerprint") != self.item["source_fingerprint"]:
            self.issues.append("source_fingerprint does not match the claimed item")

        curation = self.value.get("curation")
        if not isinstance(curation, dict):
            self.issues.append("curation must be an object")
            curation = {}
        if curation.get("relevant") is not True:
            self.issues.append("curation.relevant must be true")
        self._confidence(curation.get("confidence"), "curation.confidence", 0.80)
        event_key = curation.get("event_key")
        if not isinstance(event_key, str) or not SAFE_EVENT_KEY.fullmatch(event_key):
            self.issues.append("curation.event_key must be a stable lowercase key")
        if curation.get("importance") not in {"high", "medium", "low"}:
            self.issues.append("curation.importance must be high, medium, or low")
        _bounded_text(
            curation.get("reason"),
            "curation.reason",
            20,
            1000,
            self.issues,
            require_korean=True,
        )

        document = self.value.get("document")
        if not isinstance(document, dict):
            self.issues.append("document must be an object")
            document = {}
        if document.get("title") != self.record.title:
            self.issues.append("document.title must preserve the source title")
        _bounded_text(
            document.get("summary"),
            "document.summary",
            80,
            4000,
            self.issues,
            require_korean=True,
        )
        _bounded_text(
            document.get("why_important"),
            "document.why_important",
            50,
            3000,
            self.issues,
            require_korean=True,
        )
        self._validate_string_list(document.get("topics"), "document.topics", 1, 8)
        self._validate_string_list(
            document.get("follow_up"), "document.follow_up", 1, 8
        )
        self._validate_keywords(document.get("keywords"))
        self._validate_evidence(document.get("evidence"))

        verification = self.value.get("verification")
        if not isinstance(verification, dict):
            self.issues.append("verification must be an object")
            verification = {}
        if verification.get("verdict") != "pass":
            self.issues.append("verification.verdict must be pass")
        self._confidence(
            verification.get("confidence"),
            "verification.confidence",
            0.85,
        )
        checks = verification.get("checks")
        if not isinstance(checks, dict):
            self.issues.append("verification.checks must be an object")
            checks = {}
        for name in self.REQUIRED_CHECKS:
            if checks.get(name) is not True:
                self.issues.append("verification.checks.{} must be true".format(name))
        if verification.get("issues") not in ([], None):
            self.issues.append("verification.issues must be empty")

        serialized = json.dumps(self.value, ensure_ascii=False)
        lowered = serialized.lower()
        for marker in FORBIDDEN_OUTPUT:
            if marker.lower() in lowered:
                self.issues.append(
                    "generated output contains forbidden marker: {}".format(marker)
                )

    def _confidence(self, value: Any, name: str, threshold: float) -> None:
        if not isinstance(value, (float, int)) or isinstance(value, bool):
            self.issues.append("{} must be a number".format(name))
            return
        if not threshold <= float(value) <= 1.0:
            self.issues.append("{} must be between {} and 1".format(name, threshold))

    def _validate_string_list(
        self,
        value: Any,
        name: str,
        minimum: int,
        maximum: int,
    ) -> None:
        if not isinstance(value, list) or not minimum <= len(value) <= maximum:
            self.issues.append(
                "{} must contain {} to {} strings".format(name, minimum, maximum)
            )
            return
        if any(not isinstance(item, str) or not item.strip() for item in value):
            self.issues.append("{} contains an invalid string".format(name))

    def _validate_keywords(self, value: Any) -> None:
        if not isinstance(value, list) or not 1 <= len(value) <= 8:
            self.issues.append("document.keywords must contain 1 to 8 entries")
            return
        for entry in value:
            if not isinstance(entry, dict):
                self.issues.append("document.keywords entries must be objects")
                continue
            _bounded_text(
                entry.get("name"),
                "document.keywords.name",
                2,
                80,
                self.issues,
            )
            _bounded_text(
                entry.get("reason"),
                "document.keywords.reason",
                10,
                300,
                self.issues,
                require_korean=True,
            )

    def _validate_evidence(self, value: Any) -> None:
        if not isinstance(value, list) or not 1 <= len(value) <= 12:
            self.issues.append("document.evidence must contain 1 to 12 entries")
            return
        has_primary = False
        for entry in value:
            if not isinstance(entry, dict):
                self.issues.append("document.evidence entries must be objects")
                continue
            _bounded_text(
                entry.get("claim"),
                "document.evidence.claim",
                10,
                800,
                self.issues,
                require_korean=True,
            )
            source_url = entry.get("source_url")
            if (
                not isinstance(source_url, str)
                or urlsplit(source_url).scheme.lower() != "https"
            ):
                self.issues.append("document.evidence.source_url must use HTTPS")
            if source_url == self.record.canonical_url:
                has_primary = True
        if not has_primary:
            self.issues.append(
                "document.evidence must reference the collected canonical URL"
            )

    @property
    def curation(self) -> Mapping[str, Any]:
        return self.value["curation"]

    @property
    def document(self) -> Mapping[str, Any]:
        return self.value["document"]

    @property
    def verification(self) -> Mapping[str, Any]:
        return self.value["verification"]


def render_note(artifact: AgentArtifact, now: Optional[datetime] = None) -> str:
    now = now or utc_now()
    record = artifact.record
    document = artifact.document
    curation = artifact.curation
    source_type = "official-channel" if record.official else "editorial-media"
    lines = [
        "---",
        'note_schema_version: "1.0"',
        "record_id: {}".format(_yaml_string(record.id)),
        "source_fingerprint: {}".format(
            _yaml_string(artifact.item["source_fingerprint"])
        ),
        "source: {}".format(_yaml_string(record.organization)),
        "source_id: {}".format(_yaml_string(record.source_id)),
        "source_type: {}".format(_yaml_string(source_type)),
        "canonical_url: {}".format(_yaml_string(record.canonical_url)),
        "original_url: {}".format(_yaml_string(record.url)),
        "published_at: {}".format(_yaml_string(record.published_at[:10])),
        "collected_at: {}".format(_yaml_string(record.discovered_at)),
        "first_collected_at: {}".format(_yaml_string(record.discovered_at)),
        "last_checked_at: {}".format(_yaml_string(isoformat_utc(now))),
        "language: {}".format(_yaml_string(record.language)),
        "discovery_method: {}".format(_yaml_string(record.discovery_method)),
        'verification_status: "agent-verified"',
        'created_by: "hermes-agent"',
        'generator: "hermes-news-automation"',
        "generator_version: {}".format(_yaml_string(GENERATOR_VERSION)),
        "event_key: {}".format(_yaml_string(curation["event_key"])),
        "topics: {}".format(json.dumps(document["topics"], ensure_ascii=False)),
        "importance: {}".format(_yaml_string(curation["importance"])),
        'status: "published"',
        "---",
        "",
        "# {}".format(record.title),
        "",
        "## 원문",
        "",
        "- [원문 보기]({})".format(record.canonical_url),
        "- 발행: {}".format(record.published_at[:10]),
        "- 출처: {} / {}".format(record.organization, record.channel),
        "- 검증: Curator와 독립 Verifier가 원문 근거를 대조하고 자동 검증 통과",
        "",
        "## 요약",
        "",
        str(document["summary"]).strip(),
        "",
        "## 왜 중요한가",
        "",
        str(document["why_important"]).strip(),
        "",
        "## 기술 학습 키워드",
        "",
    ]
    for keyword in document["keywords"]:
        lines.append(
            "- [[{}]] — {}".format(
                str(keyword["name"]).strip(),
                str(keyword["reason"]).strip(),
            )
        )
    lines.extend(["", "## 근거", ""])
    for evidence in document["evidence"]:
        lines.append(
            "- {} — [근거 원문]({})".format(
                str(evidence["claim"]).strip(),
                evidence["source_url"],
            )
        )
    lines.extend(["", "## 확인할 점", ""])
    for item in document["follow_up"]:
        lines.append("- {}".format(str(item).strip()))
    lines.extend(
        [
            "",
            "## 자동 검증",
            "",
            "- 관련성 confidence: {:.2f}".format(
                float(curation["confidence"])
            ),
            "- 사실 검증 confidence: {:.2f}".format(
                float(artifact.verification["confidence"])
            ),
            "- 판정 근거: {}".format(str(curation["reason"]).strip()),
            "",
        ]
    )
    return "\n".join(lines)


def note_filename(record: Record) -> str:
    title = re.sub(r'[/:*?"<>|\\\x00-\x1f]', " ", record.title)
    title = re.sub(r"\s+", " ", title).strip().rstrip(".")
    title = title[:120].strip() or record.id[:12]
    return "{} {}.md".format(record.published_at[:10], title)


class UnattendedController:
    def __init__(
        self,
        data_dir: Path,
        vault_dir: Path,
        collection_store: Optional[FileStore] = None,
    ) -> None:
        self.data_dir = data_dir
        self.vault_dir = vault_dir.resolve()
        self.state = AutomationStore(data_dir)
        self.collection_store = collection_store or FileStore(data_dir)

    @staticmethod
    def new_run_id() -> str:
        return "{}-{}".format(
            utc_now().strftime("%Y%m%dT%H%M%S%fZ"),
            uuid.uuid4().hex[:8],
        )

    def begin(
        self,
        sources: Sequence[SourceConfig],
        reports: Sequence[Mapping[str, Any]],
        max_items: int,
        ttl_minutes: int,
        run_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        run_id = self.open_run(ttl_minutes, run_id)
        return self.prepare(run_id, sources, reports, max_items)

    def open_run(
        self,
        ttl_minutes: int,
        run_id: Optional[str] = None,
    ) -> str:
        if ttl_minutes < 1:
            raise AutomationError("ttl_minutes must be positive")
        run_id = run_id or self.new_run_id()
        self.state.acquire(run_id, ttl_minutes)
        self.state.save_manifest(
            run_id,
            {
                "schema_version": AUTOMATION_SCHEMA_VERSION,
                "run_id": run_id,
                "status": "collecting",
                "started_at": isoformat_utc(utc_now()),
                "reports": [],
            },
        )
        return run_id

    def prepare(
        self,
        run_id: str,
        sources: Sequence[SourceConfig],
        reports: Sequence[Mapping[str, Any]],
        max_items: int,
    ) -> Mapping[str, Any]:
        if max_items < 1:
            raise AutomationError("max_items must be positive")
        self.state.assert_owner(run_id)
        manifest = self.state.load_manifest(run_id)
        manifest.update({"status": "preparing", "reports": list(reports)})
        self.state.save_manifest(run_id, manifest)
        try:
            queue, suppressed, manual_updates = self._build_queue(
                sources, reports, max_items
            )
            self.state.save_queue(run_id, queue)
            manifest.update(
                {
                    "status": "ready",
                    "queue_items": len(queue),
                    "suppressed_by_ledger": suppressed,
                    "manual_updates_quarantined": manual_updates,
                }
            )
            self.state.save_manifest(run_id, manifest)
            return manifest
        except Exception as error:
            manifest.update(
                {
                    "status": "failed",
                    "finished_at": isoformat_utc(utc_now()),
                    "error": str(error),
                }
            )
            self.state.save_manifest(run_id, manifest)
            self.state.release(run_id)
            raise

    def _build_queue(
        self,
        sources: Sequence[SourceConfig],
        reports: Sequence[Mapping[str, Any]],
        max_items: int,
    ) -> Tuple[List[Mapping[str, Any]], int, int]:
        note_index = VaultNoteIndex.scan(self.vault_dir)
        if note_index.issues:
            raise AutomationError("vault contains invalid note identities")
        report_by_source = {
            str(report["source_id"]): report for report in reports
        }
        decisions = self.state.decisions()
        candidates: List[Tuple[int, str, Mapping[str, Any]]] = []
        suppressed = 0
        manual_updates = 0
        now = utc_now()
        for source in sources:
            report = report_by_source.get(source.id)
            if not report or report.get("status") != "success":
                continue
            cutoff = now - timedelta(days=source.freshness_days)
            for record in self.collection_store.load_current(source.id):
                try:
                    published = _parse_time(record.published_at)
                except ValueError:
                    continue
                if published < cutoff:
                    continue
                fingerprint = record_fingerprint(record)
                decision = note_index.decision(record.id, fingerprint)
                if decision.action == "skip":
                    continue
                key = _queue_key(record.id, fingerprint)
                if decisions.get(key, {}).get("status") in FINAL_DECISIONS:
                    suppressed += 1
                    continue
                if (
                    decision.action == "update_pending"
                    and decision.created_by != "hermes-agent"
                ):
                    self.state.record_decision(
                        {
                            "item_key": key,
                            "record": record.to_dict(),
                            "source_fingerprint": fingerprint,
                        },
                        "quarantined",
                        "legacy manual note changed; automatic overwrite forbidden",
                    )
                    manual_updates += 1
                    continue
                item = {
                    "item_key": key,
                    "record": record.to_dict(),
                    "source_fingerprint": fingerprint,
                    "action": (
                        "create" if decision.action == "create" else "update"
                    ),
                    "note_path": decision.path,
                    "state": "pending",
                    "attempts": 0,
                    "created_at": isoformat_utc(now),
                }
                candidates.append(
                    (source.priority, record.published_at, item)
                )
        candidates.sort(key=lambda value: (value[0], value[1]), reverse=False)
        # Within a priority, newest records must be handled first.
        ordered: List[Mapping[str, Any]] = []
        for priority in sorted({value[0] for value in candidates}):
            group = [value for value in candidates if value[0] == priority]
            group.sort(key=lambda value: value[1], reverse=True)
            ordered.extend(value[2] for value in group)
        return ordered[:max_items], suppressed, manual_updates

    def claim_next(self, run_id: str) -> Optional[Mapping[str, Any]]:
        def mutate(queue):
            for item in queue:
                if item["state"] != "pending":
                    continue
                item["state"] = "processing"
                item["attempts"] = int(item.get("attempts", 0)) + 1
                item["claimed_at"] = isoformat_utc(utc_now())
                return dict(item)
            return None

        return self.state.mutate_queue(run_id, mutate)

    def processing_item(
        self,
        run_id: str,
        record_id: str,
    ) -> Mapping[str, Any]:
        self.state.assert_owner(run_id)
        queue = self.state.load_queue(run_id)
        return dict(self._processing_item(queue, record_id))

    def reject(
        self,
        run_id: str,
        record_id: str,
        disposition: str,
        reason: str,
    ) -> Mapping[str, Any]:
        if disposition not in {"irrelevant", "quarantined", "retryable"}:
            raise AutomationError("unsupported disposition")
        if len(reason.strip()) < 10:
            raise AutomationError("rejection reason is too short")

        def mutate(queue):
            item = self._processing_item(queue, record_id)
            item["state"] = disposition
            item["reason"] = reason.strip()
            item["finished_at"] = isoformat_utc(utc_now())
            return dict(item)

        item = self.state.mutate_queue(run_id, mutate)
        if disposition in FINAL_DECISIONS:
            self.state.record_decision(item, disposition, reason.strip())
        return item

    def submit(
        self,
        run_id: str,
        record_id: str,
        artifact_value: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        queue = self.state.load_queue(run_id)
        item = self._processing_item(queue, record_id)
        artifact = AgentArtifact(artifact_value, item)
        event_key = str(artifact.curation["event_key"])
        duplicate = self.state.reserve_event(event_key, item)
        if duplicate:
            raise AutomationError(
                "event {} is already represented by record {}".format(
                    event_key, duplicate.get("record_id")
                )
            )
        content = render_note(artifact)
        try:
            path, previous = self._write_note(item, artifact.record, content)
            index = VaultNoteIndex.scan(self.vault_dir)
            if index.issues:
                self._rollback_note(path, previous)
                raise AutomationError(
                    "generated note failed vault identity validation"
                )
        except Exception:
            self.state.release_event(event_key, record_id)
            raise
        relative_path = path.relative_to(self.vault_dir).as_posix()
        self.state.finish_event(event_key, item, relative_path)
        artifact_path = self.state.save_artifact(
            run_id, record_id, artifact.value
        )

        def mutate(values):
            current = self._processing_item(values, record_id)
            current["state"] = "committed"
            current["note_path"] = relative_path
            current["event_key"] = event_key
            current["artifact_path"] = artifact_path
            current["committed_at"] = isoformat_utc(utc_now())
            return dict(current)

        return self.state.mutate_queue(run_id, mutate)

    def _write_note(
        self,
        item: Mapping[str, Any],
        record: Record,
        content: str,
    ) -> Tuple[Path, Optional[bytes]]:
        if item["action"] == "update":
            relative = item.get("note_path")
            if not relative:
                raise AutomationError("update item has no note path")
            path = (self.vault_dir / str(relative)).resolve()
            if self.vault_dir not in path.parents:
                raise AutomationError("update path left the vault")
            previous = path.read_bytes()
        else:
            path = self.vault_dir / "Inbox" / note_filename(record)
            if path.exists():
                path = path.with_name(
                    "{} {}.md".format(path.stem, record.id[:10])
                )
            previous = None
        _atomic_write(path, content.encode("utf-8"))
        return path, previous

    @staticmethod
    def _rollback_note(path: Path, previous: Optional[bytes]) -> None:
        if previous is None:
            path.unlink(missing_ok=True)
        else:
            _atomic_write(path, previous)

    def notify(
        self,
        run_id: str,
        notifier: TelegramNotifier,
    ) -> Mapping[str, Any]:
        self.state.assert_owner(run_id)
        index = VaultNoteIndex.scan(self.vault_dir)
        if index.issues:
            raise AutomationError("vault validation failed before notification")
        queue = self.state.load_queue(run_id)
        sent = 0
        skipped = 0
        unknown = 0
        for item in queue:
            if item["state"] != "committed":
                continue
            key = "{}:{}:telegram".format(
                item["record"]["id"], item["source_fingerprint"]
            )
            if not self.state.reserve_delivery(key, item):
                skipped += 1
                self._set_item_state(run_id, item["record"]["id"], "notified")
                continue
            path = self.vault_dir / item["note_path"]
            try:
                messages = notifier.send_files([path])
            except TelegramError as error:
                self.state.finish_delivery(
                    key,
                    "unknown",
                    error=str(error),
                )
                self._set_item_state(
                    run_id, item["record"]["id"], "notify_unknown"
                )
                unknown += 1
                continue
            self.state.finish_delivery(key, "sent", messages=messages)
            self._set_item_state(run_id, item["record"]["id"], "notified")
            sent += 1
        return {
            "sent_documents": sent,
            "already_reserved": skipped,
            "unknown_deliveries": unknown,
        }

    def finish(self, run_id: str) -> Mapping[str, Any]:
        self.state.assert_owner(run_id)
        queue = self.state.load_queue(run_id)
        unfinished = [
            item
            for item in queue
            if item["state"] in {"pending", "processing", "committed"}
        ]
        if unfinished:
            raise AutomationError(
                "{} queue items are unfinished".format(len(unfinished))
            )
        counts: Dict[str, int] = {}
        for item in queue:
            counts[item["state"]] = counts.get(item["state"], 0) + 1
        manifest = self.state.load_manifest(run_id)
        source_failures = sum(
            report.get("status") == "failed"
            for report in manifest.get("reports", [])
        )
        manifest.update(
            {
                "status": (
                    "completed"
                    if not source_failures
                    and not counts.get("retryable")
                    and not counts.get("quarantined")
                    and not counts.get("notify_unknown")
                    else "completed_with_exceptions"
                ),
                "finished_at": isoformat_utc(utc_now()),
                "outcomes": counts,
                "source_failures": source_failures,
            }
        )
        self.state.save_manifest(run_id, manifest)
        self.state.release(run_id)
        return manifest

    def abort(self, run_id: str, reason: str) -> Mapping[str, Any]:
        self.state.assert_owner(run_id)
        manifest = self.state.load_manifest(run_id)
        manifest.update(
            {
                "status": "aborted",
                "finished_at": isoformat_utc(utc_now()),
                "error": reason.strip() or "aborted",
            }
        )
        self.state.save_manifest(run_id, manifest)
        self.state.release(run_id)
        return manifest

    def status(self, run_id: str) -> Mapping[str, Any]:
        manifest = self.state.load_manifest(run_id)
        counts: Dict[str, int] = {}
        for item in self.state.load_queue(run_id):
            counts[item["state"]] = counts.get(item["state"], 0) + 1
        value = dict(manifest)
        value["queue_outcomes"] = counts
        return value

    @staticmethod
    def _processing_item(
        queue: Sequence[Mapping[str, Any]],
        record_id: str,
    ) -> Dict[str, Any]:
        matches = [
            item
            for item in queue
            if item["record"]["id"] == record_id
            and item["state"] == "processing"
        ]
        if len(matches) != 1:
            raise AutomationError(
                "record must identify exactly one processing queue item"
            )
        return matches[0]  # type: ignore[return-value]

    def _set_item_state(
        self,
        run_id: str,
        record_id: str,
        state: str,
    ) -> None:
        if state not in QUEUE_STATES:
            raise AutomationError("unsupported queue state")

        def mutate(queue):
            matches = [
                item for item in queue if item["record"]["id"] == record_id
            ]
            if len(matches) != 1:
                raise AutomationError("record is not unique in run queue")
            matches[0]["state"] = state
            matches[0]["state_changed_at"] = isoformat_utc(utc_now())

        self.state.mutate_queue(run_id, mutate)
