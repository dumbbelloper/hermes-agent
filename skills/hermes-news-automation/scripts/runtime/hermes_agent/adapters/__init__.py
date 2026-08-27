"""Built-in source adapters."""

from .jcb import JcbJsonAdapter
from .rss import RssAtomAdapter
from .visa import VisaPressAdapter
from .wise import WiseChangelogAdapter

__all__ = [
    "JcbJsonAdapter",
    "RssAtomAdapter",
    "VisaPressAdapter",
    "WiseChangelogAdapter",
]
