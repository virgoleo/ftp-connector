"""Public API for the remote file transfer kit."""

from .base import TransferClient
from .config import AuthenticationMode, Protocol, TransferConfig
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    HostKeyVerificationError,
    OperationError,
    RemoteFileExistsError,
    RemoteFileNotFoundError,
    RemotePermissionError,
    RemoteTransferError,
)
from .models import RemoteEntry
from .transports.sftp import SFTPClient

__all__ = [
    "AuthenticationError",
    "AuthenticationMode",
    "ConfigurationError",
    "ConnectionError",
    "HostKeyVerificationError",
    "OperationError",
    "Protocol",
    "RemoteEntry",
    "RemoteFileExistsError",
    "RemoteFileNotFoundError",
    "RemotePermissionError",
    "RemoteTransferError",
    "SFTPClient",
    "TransferClient",
    "TransferConfig",
]
