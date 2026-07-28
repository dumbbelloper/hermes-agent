"""Hermes Agent official-source collector."""

from .models import Record, SourceConfig
from .note_index import NoteDecision, NoteEntry, VaultNoteIndex

__all__ = [
    "NoteDecision",
    "NoteEntry",
    "Record",
    "SourceConfig",
    "VaultNoteIndex",
]
__version__ = "0.1.0"
