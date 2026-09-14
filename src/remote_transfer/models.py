"""Transport-independent remote file metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class RemoteEntry:
    """Metadata for one file-system entry on a remote server."""

    path: str
    name: str
    is_directory: bool
    size: int
    modified_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path or "\x00" in self.path:
            raise ConfigurationError("remote entry path must be a non-empty string without NUL bytes")
        if not isinstance(self.name, str) or not self.name or "\x00" in self.name:
            raise ConfigurationError("remote entry name must be a non-empty string without NUL bytes")
        if isinstance(self.size, bool) or not isinstance(self.size, int) or self.size < 0:
            raise ConfigurationError("remote entry size must be a non-negative integer")
