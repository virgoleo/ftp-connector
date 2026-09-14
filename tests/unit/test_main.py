import sys
from pathlib import Path

import pytest

from main import load_config_from_environment, load_configs_from_environment
from remote_transfer import AuthenticationMode, ConfigurationError


def test_main_adds_source_directory_to_module_path() -> None:
    source_directory = Path(__file__).parents[2] / "src"

    assert str(source_directory) in sys.path


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


def test_main_loads_multiple_named_sftp_configurations() -> None:
    configs = load_configs_from_environment(
        {
            "SFTP_SERVERS": "test, staging",
            "SFTP_TEST_HOST": "test.sftp.test",
            "SFTP_TEST_USERNAME": "test-user",
            "SFTP_TEST_PRIVATE_KEY_PATH": "test-key",
            "SFTP_TEST_KNOWN_HOSTS_PATH": "test-known-hosts",
            "SFTP_STAGING_HOST": "staging.sftp.test",
            "SFTP_STAGING_USERNAME": "staging-user",
            "SFTP_STAGING_PASSWORD": "staging-password",
            "SFTP_STAGING_KNOWN_HOSTS_PATH": "staging-known-hosts",
        }
    )

    assert configs["TEST"].host == "test.sftp.test"
    assert configs["TEST"].private_key_path == Path("test-key")
    assert configs["TEST"].known_hosts_path == Path("test-known-hosts")
    assert configs["STAGING"].host == "staging.sftp.test"
    assert configs["STAGING"].authentication_mode is AuthenticationMode.PASSWORD
    assert configs["STAGING"].known_hosts_path == Path("staging-known-hosts")


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
        {
            "SFTP_SERVERS": "test, TEST",
            "SFTP_TEST_HOST": "test.sftp.test",
            "SFTP_TEST_USERNAME": "test-user",
            "SFTP_TEST_PASSWORD": "test-password",
        },
    ],
)
def test_main_rejects_invalid_environment(environment: dict[str, str]) -> None:
    with pytest.raises(ConfigurationError):
        if "SFTP_SERVERS" in environment:
            load_configs_from_environment(environment)
        else:
            load_config_from_environment(environment)
