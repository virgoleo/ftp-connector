"""Stable exception hierarchy exposed by :mod:`remote_transfer`."""


class RemoteTransferError(Exception):
    """Base class for all package-defined errors."""


class ConfigurationError(RemoteTransferError, ValueError):
    """Raised when transfer configuration is invalid."""


class ConnectionError(RemoteTransferError):
    """Raised when a connection cannot be established or maintained."""


class AuthenticationError(ConnectionError):
    """Raised when the remote server rejects authentication."""


class HostKeyVerificationError(ConnectionError):
    """Raised when an SSH server host key cannot be verified."""


class OperationError(RemoteTransferError):
    """Raised when a remote file operation fails."""


class RemoteFileNotFoundError(OperationError):
    """Raised when a requested remote path does not exist."""


class RemotePermissionError(OperationError):
    """Raised when the server denies a remote operation."""


class RemoteFileExistsError(OperationError):
    """Raised when an operation requires a path not to exist."""
