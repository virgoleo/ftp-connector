import errno
import stat
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import paramiko
import pytest

from remote_transfer import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    HostKeyVerificationError,
    OperationError,
    Protocol,
    RemoteFileNotFoundError,
    RemotePermissionError,
    SFTPClient,
    TransferConfig,
)


def _config(**overrides: object) -> TransferConfig:
    values: dict[str, object] = {
        "protocol": Protocol.SFTP,
        "host": "sftp.test",
        "username": "test-user",
        "password": "test-password",
        "connection_timeout": 11.0,
        "authentication_timeout": 12.0,
        "operation_timeout": 13.0,
    }
    values.update(overrides)
    return TransferConfig(**values)  # type: ignore[arg-type]


def _connect(client: SFTPClient) -> tuple[MagicMock, MagicMock, MagicMock]:
    ssh_client = MagicMock()
    sftp_client = MagicMock()
    channel = MagicMock()
    ssh_client.open_sftp.return_value = sftp_client
    sftp_client.get_channel.return_value = channel
    with patch("remote_transfer.transports.sftp.paramiko.SSHClient", return_value=ssh_client):
        client.connect()
    return ssh_client, sftp_client, channel


def test_password_authentication_uses_secure_ssh_defaults() -> None:
    client = SFTPClient(_config())
    ssh_client, _, channel = _connect(client)

    ssh_client.load_system_host_keys.assert_called_once_with()
    policy = ssh_client.set_missing_host_key_policy.call_args.args[0]
    assert isinstance(policy, paramiko.RejectPolicy)
    ssh_client.connect.assert_called_once_with(
        hostname="sftp.test",
        port=22,
        username="test-user",
        timeout=11.0,
        auth_timeout=12.0,
        banner_timeout=11.0,
        look_for_keys=False,
        allow_agent=False,
        password="test-password",
    )
    channel.settimeout.assert_called_with(13.0)


def test_private_key_authentication_without_passphrase() -> None:
    client = SFTPClient(_config(password=None, private_key_path=Path("test-key")))
    ssh_client, _, _ = _connect(client)

    assert ssh_client.connect.call_args.kwargs["key_filename"] == "test-key"
    assert ssh_client.connect.call_args.kwargs["passphrase"] is None
    assert ssh_client.connect.call_args.kwargs["allow_agent"] is False
    assert "password" not in ssh_client.connect.call_args.kwargs


def test_private_key_authentication_with_passphrase() -> None:
    client = SFTPClient(
        _config(
            password=None,
            private_key_path=Path("test-key"),
            private_key_passphrase="test-passphrase",
        )
    )
    ssh_client, _, _ = _connect(client)

    assert ssh_client.connect.call_args.kwargs["key_filename"] == "test-key"
    assert ssh_client.connect.call_args.kwargs["passphrase"] == "test-passphrase"


def test_ssh_agent_authentication() -> None:
    client = SFTPClient(_config(password=None, use_ssh_agent=True))
    ssh_client, _, _ = _connect(client)

    assert ssh_client.connect.call_args.kwargs["allow_agent"] is True
    assert ssh_client.connect.call_args.kwargs["look_for_keys"] is False
    assert "password" not in ssh_client.connect.call_args.kwargs
    assert "key_filename" not in ssh_client.connect.call_args.kwargs


def test_custom_known_hosts_is_loaded_and_unknown_keys_are_rejected() -> None:
    client = SFTPClient(_config(known_hosts_path=Path("known_hosts")))
    ssh_client, _, _ = _connect(client)

    ssh_client.load_host_keys.assert_called_once_with("known_hosts")
    policy = ssh_client.set_missing_host_key_policy.call_args.args[0]
    assert isinstance(policy, paramiko.RejectPolicy)
    assert not isinstance(policy, paramiko.AutoAddPolicy)

    with pytest.raises(HostKeyVerificationError, match="not trusted"):
        policy.missing_host_key(ssh_client, "unknown.sftp.test", MagicMock())


def test_bad_host_key_is_translated_without_transport_details() -> None:
    client = SFTPClient(_config())
    ssh_client = MagicMock()
    ssh_client.connect.side_effect = paramiko.BadHostKeyException(
        "sftp.test", MagicMock(), MagicMock()
    )

    with (
        patch("remote_transfer.transports.sftp.paramiko.SSHClient", return_value=ssh_client),
        pytest.raises(HostKeyVerificationError, match="host key verification failed"),
    ):
        client.connect()

    ssh_client.close.assert_called_once_with()


def test_authentication_and_connection_errors_are_translated() -> None:
    for transport_error, stable_error in [
        (paramiko.AuthenticationException(), AuthenticationError),
        (OSError("connection refused"), ConnectionError),
    ]:
        client = SFTPClient(_config())
        ssh_client = MagicMock()
        ssh_client.connect.side_effect = transport_error

        with (
            patch("remote_transfer.transports.sftp.paramiko.SSHClient", return_value=ssh_client),
            pytest.raises(stable_error),
        ):
            client.connect()


def test_private_key_loading_error_identifies_key_configuration() -> None:
    client = SFTPClient(_config(password=None, private_key_path=Path("test-key")))
    ssh_client = MagicMock()
    ssh_client.connect.side_effect = paramiko.PasswordRequiredException("passphrase required")

    with (
        patch("remote_transfer.transports.sftp.paramiko.SSHClient", return_value=ssh_client),
        pytest.raises(AuthenticationError, match="passphrase is required or incorrect"),
    ):
        client.connect()

    assert ssh_client.close.called


def test_missing_private_key_file_is_a_configuration_error() -> None:
    client = SFTPClient(_config(password=None, private_key_path=Path("missing-key")))
    ssh_client = MagicMock()
    ssh_client.connect.side_effect = FileNotFoundError("missing key")

    with (
        patch("remote_transfer.transports.sftp.paramiko.SSHClient", return_value=ssh_client),
        pytest.raises(ConfigurationError, match="private key file was not found"),
    ):
        client.connect()


def test_operation_timeout_is_reapplied_and_context_manager_closes_resources() -> None:
    client = SFTPClient(_config())
    ssh_client, sftp_client, channel = _connect(client)

    with client:
        assert client.exists("/remote.txt")

    assert channel.settimeout.call_count == 2
    sftp_client.close.assert_called_once_with()
    ssh_client.close.assert_called_once_with()


def test_list_returns_remote_metadata_using_posix_paths() -> None:
    client = SFTPClient(_config())
    _, sftp_client, _ = _connect(client)
    sftp_client.listdir_attr.return_value = [
        SimpleNamespace(
            filename="report.csv",
            st_mode=stat.S_IFREG,
            st_size=42,
            st_mtime=0,
        )
    ]

    entries = client.list("/incoming")

    assert entries[0].path == "/incoming/report.csv"
    assert entries[0].size == 42
    assert not entries[0].is_directory


@pytest.mark.parametrize(
    ("transport_error", "stable_error"),
    [
        (FileNotFoundError(errno.ENOENT, "missing"), RemoteFileNotFoundError),
        (PermissionError(errno.EACCES, "denied"), RemotePermissionError),
        (OSError("server failure"), OperationError),
    ],
)
def test_operation_errors_are_translated(
    transport_error: OSError, stable_error: type[Exception]
) -> None:
    client = SFTPClient(_config())
    _, sftp_client, _ = _connect(client)
    sftp_client.get.side_effect = transport_error

    with pytest.raises(stable_error):
        client.download("/remote.txt", Path("local.txt"))


def test_exists_returns_false_for_missing_remote_path() -> None:
    client = SFTPClient(_config())
    _, sftp_client, _ = _connect(client)
    sftp_client.stat.side_effect = FileNotFoundError(errno.ENOENT, "missing")

    assert not client.exists("/missing")


def test_remove_uses_rmdir_for_directories() -> None:
    client = SFTPClient(_config())
    _, sftp_client, _ = _connect(client)
    sftp_client.stat.return_value = SimpleNamespace(st_mode=stat.S_IFDIR)

    client.remove("/empty-directory")

    sftp_client.rmdir.assert_called_once_with("/empty-directory")
    sftp_client.remove.assert_not_called()
