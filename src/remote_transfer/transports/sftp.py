"""Secure Paramiko-backed SFTP client."""

from __future__ import annotations

import errno
import posixpath
import stat
from datetime import datetime, timezone
from os import PathLike
from typing import Any, NoReturn

import paramiko

from ..base import TransferClient
from ..config import AuthenticationMode, Protocol, TransferConfig
from ..exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    HostKeyVerificationError,
    OperationError,
    RemoteFileNotFoundError,
    RemotePermissionError,
)
from ..models import RemoteEntry


class SFTPClient(TransferClient):
    """SFTP adapter that verifies host keys and translates transport errors."""

    def __init__(self, config: TransferConfig) -> None:
        if config.protocol is not Protocol.SFTP:
            raise ConfigurationError("SFTPClient requires an SFTP TransferConfig")
        self._config = config
        self._ssh_client: paramiko.SSHClient | None = None
        self._sftp_client: paramiko.SFTPClient | None = None

    def connect(self) -> None:
        """Connect and authenticate using the configuration's selected mode."""

        if self._sftp_client is not None:
            return

        ssh_client = paramiko.SSHClient()
        try:
            ssh_client.load_system_host_keys()
            if self._config.known_hosts_path is not None:
                ssh_client.load_host_keys(str(self._config.known_hosts_path))
            ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())
            ssh_client.connect(**self._connection_arguments())
            sftp_client = ssh_client.open_sftp()
            self._set_operation_timeout(sftp_client)
        except paramiko.BadHostKeyException:
            ssh_client.close()
            raise HostKeyVerificationError("SSH host key verification failed") from None
        except paramiko.AuthenticationException:
            ssh_client.close()
            raise AuthenticationError("SFTP authentication failed") from None
        except (paramiko.SSHException, OSError, TimeoutError):
            ssh_client.close()
            raise ConnectionError("Unable to connect to SFTP server") from None

        self._ssh_client = ssh_client
        self._sftp_client = sftp_client

    def close(self) -> None:
        """Close both SFTP and SSH resources; cleanup never leaks transport errors."""

        sftp_client, ssh_client = self._sftp_client, self._ssh_client
        self._sftp_client = None
        self._ssh_client = None
        if sftp_client is not None:
            try:
                sftp_client.close()
            except (paramiko.SSHException, OSError, RuntimeError):
                pass
        if ssh_client is not None:
            try:
                ssh_client.close()
            except (paramiko.SSHException, OSError, RuntimeError):
                pass

    def list(self, remote_path: str = ".") -> list[RemoteEntry]:
        """List remote entries with POSIX remote paths."""

        try:
            entries = self._sftp().listdir_attr(remote_path)
            return [self._to_remote_entry(remote_path, entry) for entry in entries]
        except (paramiko.SSHException, OSError, TimeoutError) as exc:
            self._raise_operation_error(exc)

    def download(self, remote_path: str, local_path: str | PathLike[str]) -> None:
        """Download a file using the configured operation timeout."""

        try:
            self._sftp().get(remote_path, str(local_path))
        except (paramiko.SSHException, OSError, TimeoutError) as exc:
            self._raise_operation_error(exc)

    def upload(self, local_path: str | PathLike[str], remote_path: str) -> None:
        """Upload a file using the configured operation timeout."""

        try:
            self._sftp().put(str(local_path), remote_path)
        except (paramiko.SSHException, OSError, TimeoutError) as exc:
            self._raise_operation_error(exc)

    def exists(self, remote_path: str) -> bool:
        """Return whether a remote path exists."""

        try:
            self._sftp().stat(remote_path)
            return True
        except (paramiko.SSHException, OSError, TimeoutError) as exc:
            if getattr(exc, "errno", None) == errno.ENOENT:
                return False
            self._raise_operation_error(exc)

    def mkdir(self, remote_path: str) -> None:
        """Create a remote directory."""

        try:
            self._sftp().mkdir(remote_path)
        except (paramiko.SSHException, OSError, TimeoutError) as exc:
            self._raise_operation_error(exc)

    def remove(self, remote_path: str) -> None:
        """Remove a file or an empty directory."""

        try:
            attributes = self._sftp().stat(remote_path)
            if stat.S_ISDIR(self._attribute_mode(attributes)):
                self._sftp().rmdir(remote_path)
            else:
                self._sftp().remove(remote_path)
        except (paramiko.SSHException, OSError, TimeoutError) as exc:
            self._raise_operation_error(exc)

    def _connection_arguments(self) -> dict[str, Any]:
        arguments: dict[str, Any] = {
            "hostname": self._config.host,
            "port": self._config.port,
            "username": self._config.username,
            "timeout": self._config.connection_timeout,
            "auth_timeout": self._config.authentication_timeout,
            "banner_timeout": self._config.connection_timeout,
            "look_for_keys": False,
            "allow_agent": False,
        }
        if self._config.authentication_mode is AuthenticationMode.PASSWORD:
            arguments["password"] = self._config.password
        elif self._config.authentication_mode is AuthenticationMode.PRIVATE_KEY:
            arguments["key_filename"] = str(self._config.private_key_path)
            arguments["passphrase"] = self._config.private_key_passphrase
        else:
            arguments["allow_agent"] = True
        return arguments

    def _sftp(self) -> paramiko.SFTPClient:
        if self._sftp_client is None:
            raise ConnectionError("SFTP client is not connected")
        self._set_operation_timeout(self._sftp_client)
        return self._sftp_client

    def _set_operation_timeout(self, sftp_client: paramiko.SFTPClient) -> None:
        channel = sftp_client.get_channel()
        if channel is None:
            raise paramiko.SSHException("SFTP channel is unavailable")
        channel.settimeout(self._config.operation_timeout)

    @staticmethod
    def _to_remote_entry(remote_path: str, attributes: paramiko.SFTPAttributes) -> RemoteEntry:
        name = attributes.filename
        modified_at = (
            datetime.fromtimestamp(attributes.st_mtime, tz=timezone.utc)
            if attributes.st_mtime is not None
            else None
        )
        return RemoteEntry(
            path=posixpath.join(remote_path, name),
            name=name,
            is_directory=stat.S_ISDIR(SFTPClient._attribute_mode(attributes)),
            size=SFTPClient._attribute_size(attributes),
            modified_at=modified_at,
        )

    @staticmethod
    def _attribute_mode(attributes: paramiko.SFTPAttributes) -> int:
        if attributes.st_mode is None:
            raise OperationError("SFTP entry metadata is incomplete")
        return attributes.st_mode

    @staticmethod
    def _attribute_size(attributes: paramiko.SFTPAttributes) -> int:
        if attributes.st_size is None:
            raise OperationError("SFTP entry metadata is incomplete")
        return attributes.st_size

    @staticmethod
    def _raise_operation_error(error: BaseException) -> NoReturn:
        error_number = getattr(error, "errno", None)
        if error_number == errno.ENOENT:
            raise RemoteFileNotFoundError("Remote path was not found") from None
        if error_number in (errno.EACCES, errno.EPERM):
            raise RemotePermissionError("Remote operation was denied") from None
        raise OperationError("SFTP operation failed") from None
