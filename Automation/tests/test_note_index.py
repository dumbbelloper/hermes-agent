from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hermes_agent.normalize import stable_record_id
from hermes_agent.note_index import VaultNoteIndex


SOURCE_ID = "visa-press"
URL = "https://usa.visa.com/article"
RECORD_ID = stable_record_id(SOURCE_ID, URL)
FINGERPRINT = "a" * 64


def note(
    record_id: str = RECORD_ID,
    fingerprint: str = FINGERPRINT,
    canonical_url: str = URL,
) -> str:
    return """---
note_schema_version: "1.0"
record_id: "{record_id}"
source_id: "{source_id}"
canonical_url: "{canonical_url}"
source_fingerprint: "{fingerprint}"
created_by: "manual"
status: "draft"
---

# Example
""".format(
        record_id=record_id,
        source_id=SOURCE_ID,
        canonical_url=canonical_url,
        fingerprint=fingerprint,
    )


class VaultNoteIndexTests(unittest.TestCase):
    def test_decides_create_skip_and_update_pending(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inbox = root / "Inbox"
            inbox.mkdir()
            (inbox / "existing.md").write_text(note(), encoding="utf-8")

            index = VaultNoteIndex.scan(root)

            self.assertFalse(index.issues)
            self.assertEqual(
                "skip",
                index.decision(RECORD_ID, FINGERPRINT).action,
            )
            self.assertEqual(
                "update_pending",
                index.decision(RECORD_ID, "b" * 64).action,
            )
            self.assertEqual(
                "create",
                index.decision("c" * 64, "d" * 64).action,
            )

    def test_detects_duplicate_record_id(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inbox = root / "Inbox"
            notes = root / "Notes"
            inbox.mkdir()
            notes.mkdir()
            (inbox / "first.md").write_text(note(), encoding="utf-8")
            (notes / "second.md").write_text(note(), encoding="utf-8")

            index = VaultNoteIndex.scan(root)

            self.assertEqual(
                2,
                sum(
                    issue.code == "duplicate_record_id"
                    for issue in index.issues
                ),
            )
            with self.assertRaisesRegex(ValueError, "multiple notes"):
                index.decision(RECORD_ID, FINGERPRINT)

    def test_detects_record_id_mismatch(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inbox = root / "Inbox"
            inbox.mkdir()
            (inbox / "invalid.md").write_text(
                note(record_id="e" * 64),
                encoding="utf-8",
            )

            index = VaultNoteIndex.scan(root)

            self.assertIn(
                "record_id_mismatch",
                {issue.code for issue in index.issues},
            )

    def test_requires_identity_frontmatter(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inbox = root / "Inbox"
            inbox.mkdir()
            (inbox / "legacy.md").write_text(
                "---\nsource_id: \"visa-press\"\n---\n",
                encoding="utf-8",
            )

            index = VaultNoteIndex.scan(root)

            self.assertEqual("missing_identity_fields", index.issues[0].code)
            with self.assertRaisesRegex(ValueError, "validation issues"):
                index.decision("c" * 64, "d" * 64)

    def test_rejects_noncanonical_url(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inbox = root / "Inbox"
            inbox.mkdir()
            (inbox / "tracking.md").write_text(
                note(canonical_url=URL + "?utm_source=test"),
                encoding="utf-8",
            )

            index = VaultNoteIndex.scan(root)

            self.assertIn(
                "noncanonical_url",
                {issue.code for issue in index.issues},
            )


if __name__ == "__main__":
    unittest.main()
