from pathlib import Path

import pytest

from remote_transfer import AuthenticationMode, ConfigurationError, Protocol, TransferConfig


@pytest.mark.parametrize(
    ("protocol", "port"),
    [
        (Protocol.FTP, 21),
        (Protocol.FTPS_EXPLICIT, 21),
        (Protocol.FTPS_IMPLICIT, 990),
        (Protocol.SFTP, 22),
    ],
)
def test_default_port_for_each_protocol(protocol: Protocol, port: int) -> None:
    config = TransferConfig(protocol=protocol, host="example.test", username="user", password="pw")

    assert config.port == port


@pytest.mark.parametrize(
    ("kwargs", "mode"),
    [
        ({"password": "pw"}, AuthenticationMode.PASSWORD),
        ({"private_key_path": Path("id_ed25519")}, AuthenticationMode.PRIVATE_KEY),
        (
            {"private_key_path": Path("id_ed25519"), "private_key_passphrase": "phrase"},
            AuthenticationMode.PRIVATE_KEY,
        ),
        ({"use_ssh_agent": True}, AuthenticationMode.SSH_AGENT),
    ],
)
def test_sftp_authentication_modes(kwargs: dict[str, object], mode: AuthenticationMode) -> None:
    config = TransferConfig(
        protocol=Protocol.SFTP,
        host="example.test",
        username="user",
        **kwargs,
    )

    assert config.authentication_mode is mode


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"password": "pw", "private_key_path": Path("key")},
        {"password": "pw", "use_ssh_agent": True},
        {"private_key_path": Path("key"), "use_ssh_agent": True},
        {"private_key_passphrase": "phrase"},
        {"password": ""},
    ],
)
def test_sftp_requires_exactly_one_complete_authentication_mode(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ConfigurationError):
        TransferConfig(
            protocol=Protocol.SFTP,
            host="example.test",
            username="user",
            **kwargs,
        )


@pytest.mark.parametrize("protocol", [Protocol.FTP, Protocol.FTPS_EXPLICIT, Protocol.FTPS_IMPLICIT])
def test_ftp_protocols_require_password(protocol: Protocol) -> None:
    with pytest.raises(ConfigurationError):
        TransferConfig(protocol=protocol, host="example.test", username="user")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("host", ""),
        ("username", "  "),
        ("port", 0),
        ("port", 65536),
        ("connection_timeout", 0),
        ("authentication_timeout", float("inf")),
        ("operation_timeout", -1),
    ],
)
def test_invalid_connection_values_are_rejected(field: str, value: object) -> None:
    kwargs: dict[str, object] = {
        "protocol": Protocol.SFTP,
        "host": "example.test",
        "username": "user",
        "password": "pw",
    }
    kwargs[field] = value

    with pytest.raises(ConfigurationError):
        TransferConfig(**kwargs)  # type: ignore[arg-type]


def test_config_repr_redacts_secrets() -> None:
    config = TransferConfig(
        protocol=Protocol.SFTP,
        host="example.test",
        username="user",
        private_key_path=Path("key"),
        private_key_passphrase="highly-secret-phrase",
    )

    rendered = repr(config)
    assert "highly-secret-phrase" not in rendered
    assert "private_key_passphrase" not in rendered


def test_password_is_redacted_from_repr() -> None:
    config = TransferConfig(
        protocol=Protocol.SFTP,
        host="example.test",
        username="user",
        password="highly-secret-password",
    )

    rendered = repr(config)
    assert "highly-secret-password" not in rendered
    assert "password=" not in rendered
