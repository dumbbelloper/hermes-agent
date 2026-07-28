"""Obsidian note identity index and idempotent writer decisions."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .normalize import canonicalize_url, stable_record_id


NOTE_SCHEMA_VERSION = "1.0"
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
FRONTMATTER_FIELD = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")
REQUIRED_IDENTITY_FIELDS = (
    "note_schema_version",
    "record_id",
    "source_id",
    "canonical_url",
    "source_fingerprint",
    "created_by",
    "status",
)


@dataclass(frozen=True)
class NoteIssue:
    path: str
    code: str
    message: str


@dataclass(frozen=True)
class NoteEntry:
    path: str
    note_schema_version: str
    record_id: str
    source_id: str
    canonical_url: str
    source_fingerprint: str
    created_by: str
    status: str


@dataclass(frozen=True)
class NoteDecision:
    action: str
    record_id: str
    source_fingerprint: str
    path: Optional[str] = None
    created_by: Optional[str] = None
    status: Optional[str] = None

    def to_dict(self) -> Mapping[str, Optional[str]]:
        return asdict(self)


@dataclass(frozen=True)
class VaultNoteIndex:
    root: Path
    entries: Tuple[NoteEntry, ...]
    issues: Tuple[NoteIssue, ...]

    @classmethod
    def scan(
        cls,
        root: Path,
        directories: Sequence[str] = ("Inbox", "Notes"),
    ) -> "VaultNoteIndex":
        root = root.resolve()
        entries: List[NoteEntry] = []
        issues: List[NoteIssue] = []
        for path in _markdown_paths(root, directories):
            relative = path.relative_to(root).as_posix()
            fields, parsing_issue = _read_frontmatter(path)
            if parsing_issue is not None:
                issues.append(
                    NoteIssue(relative, "invalid_frontmatter", parsing_issue)
                )
                continue
            missing = [
                name
                for name in REQUIRED_IDENTITY_FIELDS
                if not fields.get(name)
            ]
            if missing:
                issues.append(
                    NoteIssue(
                        relative,
                        "missing_identity_fields",
                        "missing required fields: {}".format(
                            ", ".join(sorted(missing))
                        ),
                    )
                )
                continue
            entry = NoteEntry(
                path=relative,
                note_schema_version=fields["note_schema_version"],
                record_id=fields["record_id"],
                source_id=fields["source_id"],
                canonical_url=fields["canonical_url"],
                source_fingerprint=fields["source_fingerprint"],
                created_by=fields["created_by"],
                status=fields["status"],
            )
            entries.append(entry)
            issues.extend(_validate_entry(entry))

        by_record: Dict[str, List[NoteEntry]] = {}
        for entry in entries:
            by_record.setdefault(entry.record_id, []).append(entry)
        for record_id, matches in sorted(by_record.items()):
            if len(matches) < 2:
                continue
            paths = ", ".join(item.path for item in matches)
            for entry in matches:
                issues.append(
                    NoteIssue(
                        entry.path,
                        "duplicate_record_id",
                        "record_id {} is used by: {}".format(record_id, paths),
                    )
                )
        return cls(root, tuple(entries), tuple(issues))

    def decision(
        self,
        record_id: str,
        source_fingerprint: str,
    ) -> NoteDecision:
        _require_sha256("record_id", record_id)
        _require_sha256("source_fingerprint", source_fingerprint)
        matches = [item for item in self.entries if item.record_id == record_id]
        if len(matches) > 1:
            raise ValueError(
                "record_id {} exists in multiple notes".format(record_id)
            )
        if self.issues:
            raise ValueError(
                "vault note index contains validation issues"
            )
        if not matches:
            return NoteDecision(
                action="create",
                record_id=record_id,
                source_fingerprint=source_fingerprint,
            )
        entry = matches[0]
        action = (
            "skip"
            if entry.source_fingerprint == source_fingerprint
            else "update_pending"
        )
        return NoteDecision(
            action=action,
            record_id=record_id,
            source_fingerprint=source_fingerprint,
            path=entry.path,
            created_by=entry.created_by,
            status=entry.status,
        )

    def to_dict(self) -> Mapping[str, object]:
        return {
            "vault": str(self.root),
            "status": "ok" if not self.issues else "invalid",
            "notes": len(self.entries),
            "issues": [asdict(item) for item in self.issues],
        }


def _markdown_paths(root: Path, directories: Sequence[str]) -> Iterable[Path]:
    for directory in directories:
        base = root / directory
        if not base.is_dir():
            continue
        yield from sorted(
            path for path in base.rglob("*.md") if path.is_file()
        )


def _read_frontmatter(path: Path):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return {}, "cannot read note: {}".format(error)
    if not lines or lines[0].strip() != "---":
        return {}, "note must start with YAML frontmatter"
    try:
        closing = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        return {}, "frontmatter closing delimiter is missing"

    fields: Dict[str, str] = {}
    for line in lines[1:closing]:
        if not line or line[0].isspace():
            continue
        match = FRONTMATTER_FIELD.fullmatch(line)
        if not match:
            continue
        name, raw_value = match.groups()
        fields[name] = _scalar(raw_value or "")
    return fields, None


def _scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, str) else str(parsed)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def _validate_entry(entry: NoteEntry) -> Iterable[NoteIssue]:
    issues: List[NoteIssue] = []
    if entry.note_schema_version != NOTE_SCHEMA_VERSION:
        issues.append(
            NoteIssue(
                entry.path,
                "unsupported_note_schema",
                "expected note_schema_version {}".format(NOTE_SCHEMA_VERSION),
            )
        )
    for name, value in (
        ("record_id", entry.record_id),
        ("source_fingerprint", entry.source_fingerprint),
    ):
        if not HEX_SHA256.fullmatch(value):
            issues.append(
                NoteIssue(
                    entry.path,
                    "invalid_{}".format(name),
                    "{} must be a lowercase SHA-256 hex digest".format(name),
                )
            )
    try:
        canonical = canonicalize_url(entry.canonical_url)
    except ValueError as error:
        issues.append(
            NoteIssue(
                entry.path,
                "invalid_canonical_url",
                str(error),
            )
        )
    else:
        if canonical != entry.canonical_url:
            issues.append(
                NoteIssue(
                    entry.path,
                    "noncanonical_url",
                    "canonical_url must already be normalized",
                )
            )
        expected = stable_record_id(entry.source_id, canonical)
        if expected != entry.record_id:
            issues.append(
                NoteIssue(
                    entry.path,
                    "record_id_mismatch",
                    "record_id does not match source_id and canonical_url",
                )
            )
    return issues


def _require_sha256(name: str, value: str) -> None:
    if not HEX_SHA256.fullmatch(value):
        raise ValueError(
            "{} must be a lowercase SHA-256 hex digest".format(name)
        )
