from pathlib import Path

import pytest

from main import load_config_from_environment, load_configs_from_environment
from remote_transfer import AuthenticationMode, ConfigurationError


def _environment(**overrides: str) -> dict[str, str]:
    values = {
        "RFT_HOST": "sftp.test",
        "RFT_USERNAME": "test-user",
        "RFT_PASSWORD": "test-password",
    }
    values.update(overrides)
    return values


def test_main_loads_password_configuration_from_environment() -> None:
    config = load_config_from_environment(_environment(RFT_PORT="2222"))

    assert config.port == 2222
    assert config.authentication_mode is AuthenticationMode.PASSWORD


def test_main_loads_private_key_configuration_from_environment() -> None:
    config = load_config_from_environment(
        _environment(
            RFT_PASSWORD="",
            RFT_PRIVATE_KEY_PATH="test-key",
            RFT_PRIVATE_KEY_PASSPHRASE="test-passphrase",
            RFT_KNOWN_HOSTS_PATH="known_hosts",
        )
    )

    assert config.private_key_path == Path("test-key")
    assert config.private_key_passphrase == "test-passphrase"
    assert config.known_hosts_path == Path("known_hosts")


def test_main_loads_ssh_agent_configuration_from_environment() -> None:
    config = load_config_from_environment(_environment(RFT_PASSWORD="", RFT_USE_SSH_AGENT="true"))

    assert config.authentication_mode is AuthenticationMode.SSH_AGENT


def test_main_loads_source_and_destination_configurations() -> None:
    source, destination = load_configs_from_environment(
        {
            "SOURCE_HOST": "source.sftp.test",
            "SOURCE_USERNAME": "source-user",
            "SOURCE_PRIVATE_KEY_PATH": "source-key",
            "SOURCE_KNOWN_HOSTS_PATH": "source-known-hosts",
            "DEST_HOST": "destination.sftp.test",
            "DEST_USERNAME": "destination-user",
            "DEST_PASSWORD": "destination-password",
            "DEST_KNOWN_HOSTS_PATH": "destination-known-hosts",
        }
    )

    assert source.host == "source.sftp.test"
    assert source.private_key_path == Path("source-key")
    assert source.known_hosts_path == Path("source-known-hosts")
    assert destination.host == "destination.sftp.test"
    assert destination.authentication_mode is AuthenticationMode.PASSWORD
    assert destination.known_hosts_path == Path("destination-known-hosts")


@pytest.mark.parametrize(
    "environment",
    [
        {"RFT_USERNAME": "test-user", "RFT_PASSWORD": "test-password"},
        {"RFT_HOST": "sftp.test", "RFT_PASSWORD": "test-password"},
        {"RFT_HOST": "sftp.test", "RFT_USERNAME": "test-user", "RFT_PROTOCOL": "ftp"},
        {
            "RFT_HOST": "sftp.test",
            "RFT_USERNAME": "test-user",
            "RFT_PASSWORD": "test-password",
            "RFT_USE_SSH_AGENT": "maybe",
        },
    ],
)
def test_main_rejects_invalid_environment(environment: dict[str, str]) -> None:
    with pytest.raises(ConfigurationError):
        load_config_from_environment(environment)
