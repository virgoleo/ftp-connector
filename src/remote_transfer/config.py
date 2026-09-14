"""Protocol-independent connection configuration."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .exceptions import ConfigurationError


class Protocol(str, Enum):
    """Supported remote file transfer protocols."""

    FTP = "ftp"
    FTPS_EXPLICIT = "ftps_explicit"
    FTPS_IMPLICIT = "ftps_implicit"
    SFTP = "sftp"


class AuthenticationMode(str, Enum):
    """Authentication mode selected by a validated configuration."""

    PASSWORD = "password"
    PRIVATE_KEY = "private_key"
    SSH_AGENT = "ssh_agent"


_DEFAULT_PORTS = {
    Protocol.FTP: 21,
    Protocol.FTPS_EXPLICIT: 21,
    Protocol.FTPS_IMPLICIT: 990,
    Protocol.SFTP: 22,
}


@dataclass(frozen=True, slots=True)
class TransferConfig:
    """Connection settings shared by all transport adapters.

    Passwords and private-key passphrases are deliberately excluded from the
    generated representation so diagnostic output cannot expose them.
    """

    protocol: Protocol
    host: str
    username: str
    port: int | None = None
    password: str | None = field(default=None, repr=False)
    private_key_path: Path | None = None
    private_key_passphrase: str | None = field(default=None, repr=False)
    use_ssh_agent: bool = False
    known_hosts_path: Path | None = None
    connection_timeout: float = 10.0
    authentication_timeout: float = 10.0
    operation_timeout: float = 30.0

    def __post_init__(self) -> None:
        try:
            protocol = Protocol(self.protocol)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("Unsupported transfer protocol") from exc

        object.__setattr__(self, "protocol", protocol)
        object.__setattr__(self, "host", self._required_text("host", self.host))
        object.__setattr__(self, "username", self._required_text("username", self.username))

        port = _DEFAULT_PORTS[protocol] if self.port is None else self.port
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ConfigurationError("port must be an integer between 1 and 65535")
        object.__setattr__(self, "port", port)

        self._validate_timeout("connection_timeout", self.connection_timeout)
        self._validate_timeout("authentication_timeout", self.authentication_timeout)
        self._validate_timeout("operation_timeout", self.operation_timeout)

        if self.private_key_path is not None:
            object.__setattr__(self, "private_key_path", Path(self.private_key_path))
        if self.known_hosts_path is not None:
            object.__setattr__(self, "known_hosts_path", Path(self.known_hosts_path))

        if protocol is Protocol.SFTP:
            self._validate_sftp_authentication()
        else:
            self._validate_password_authentication()

    @property
    def authentication_mode(self) -> AuthenticationMode:
        """Return the single authentication mode selected by validation."""

        if self.use_ssh_agent:
            return AuthenticationMode.SSH_AGENT
        if self.private_key_path is not None:
            return AuthenticationMode.PRIVATE_KEY
        return AuthenticationMode.PASSWORD

    @staticmethod
    def _required_text(name: str, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ConfigurationError(f"{name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _validate_timeout(name: str, value: object) -> None:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ConfigurationError(f"{name} must be a finite positive number")

    def _validate_sftp_authentication(self) -> None:
        has_password = self.password is not None and self.password != ""
        has_key = self.private_key_path is not None
        selected_modes = sum((has_password, has_key, self.use_ssh_agent))
        if selected_modes != 1:
            raise ConfigurationError("SFTP configuration must select exactly one authentication mode")
        if self.password == "":
            raise ConfigurationError("password must not be empty")
        if self.private_key_passphrase is not None and not has_key:
            raise ConfigurationError("A private-key passphrase requires a private key")
        if self.private_key_passphrase == "":
            raise ConfigurationError("private-key passphrase must not be empty")

    def _validate_password_authentication(self) -> None:
        if self.password is None or self.password == "":
            raise ConfigurationError("FTP and FTPS require password authentication")
        if self.private_key_path is not None or self.private_key_passphrase is not None:
            raise ConfigurationError("SSH private-key settings are only valid for SFTP")
        if self.use_ssh_agent:
            raise ConfigurationError("SSH agent authentication is only valid for SFTP")
        if self.known_hosts_path is not None:
            raise ConfigurationError("known_hosts settings are only valid for SFTP")
