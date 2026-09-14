"""Common interface implemented by protocol adapters."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from os import PathLike
from types import TracebackType

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .models import RemoteEntry


class TransferClient(ABC):
    """Abstract interface for remote file transfer clients."""

    @abstractmethod
    def connect(self) -> None:
        """Establish and authenticate the remote connection."""

    @abstractmethod
    def close(self) -> None:
        """Close the connection and release transport resources."""

    @abstractmethod
    def list(self, remote_path: str = ".") -> list[RemoteEntry]:
        """List entries below a remote path."""

    @abstractmethod
    def download(self, remote_path: str, local_path: str | PathLike[str]) -> None:
        """Download a remote file to a local path."""

    @abstractmethod
    def upload(self, local_path: str | PathLike[str], remote_path: str) -> None:
        """Upload a local file to a remote path."""

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """Return whether a remote path exists."""

    @abstractmethod
    def mkdir(self, remote_path: str) -> None:
        """Create a remote directory."""

    @abstractmethod
    def remove(self, remote_path: str) -> None:
        """Remove a remote file or empty directory."""

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
