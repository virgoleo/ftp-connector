"""Production-safe SFTP connectivity entry point.

Supply credentials and connection settings through ``RFT_*`` environment
variables. This script never reads or writes secrets to disk.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from remote_transfer import (
    ConfigurationError,
    Protocol,
    RemoteTransferError,
    SFTPClient,
    TransferConfig,
)


def load_config_from_environment(environment: Mapping[str, str] | None = None) -> TransferConfig:
    """Build a strictly SFTP configuration from runtime environment variables."""

    values = os.environ if environment is None else environment
    try:
        protocol = Protocol(values.get("RFT_PROTOCOL", "sftp").lower())
        port = _optional_integer(values.get("RFT_PORT"))
        connection_timeout = _optional_float(values.get("RFT_CONNECTION_TIMEOUT"), 10.0)
        authentication_timeout = _optional_float(values.get("RFT_AUTHENTICATION_TIMEOUT"), 10.0)
        operation_timeout = _optional_float(values.get("RFT_OPERATION_TIMEOUT"), 30.0)
    except ValueError as exc:
        raise ConfigurationError("Invalid numeric or protocol environment setting") from exc

    if protocol is not Protocol.SFTP:
        raise ConfigurationError("main.py supports only the SFTP protocol")
    return TransferConfig(
        protocol=protocol,
        host=_required_environment_value(values, "RFT_HOST"),
        username=_required_environment_value(values, "RFT_USERNAME"),
        port=port,
        password=_optional_text(values.get("RFT_PASSWORD")),
        private_key_path=_optional_path(values.get("RFT_PRIVATE_KEY_PATH")),
        private_key_passphrase=_optional_text(values.get("RFT_PRIVATE_KEY_PASSPHRASE")),
        use_ssh_agent=_boolean_environment_value(values.get("RFT_USE_SSH_AGENT", "false")),
        known_hosts_path=_optional_path(values.get("RFT_KNOWN_HOSTS_PATH")),
        connection_timeout=connection_timeout,
        authentication_timeout=authentication_timeout,
        operation_timeout=operation_timeout,
    )


def main() -> int:
    """Connect, list ``RFT_REMOTE_PATH`` (or ``.``), and close safely."""

    try:
        config = load_config_from_environment()
        remote_path = os.environ.get("RFT_REMOTE_PATH", ".")
        with SFTPClient(config) as client:
            for entry in client.list(remote_path):
                print(entry.path)
    except RemoteTransferError as exc:
        print(f"SFTP connection failed: {exc}")
        return 1
    return 0


def _required_environment_value(values: Mapping[str, str], name: str) -> str:
    value = values.get(name)
    if value is None or not value.strip():
        raise ConfigurationError(f"{name} must be set")
    return value


def _optional_text(value: str | None) -> str | None:
    return value if value else None


def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None


def _optional_integer(value: str | None) -> int | None:
    return int(value) if value else None


def _optional_float(value: str | None, default: float) -> float:
    return float(value) if value else default


def _boolean_environment_value(value: str) -> bool:
    if value.lower() in {"1", "true", "yes"}:
        return True
    if value.lower() in {"0", "false", "no"}:
        return False
    raise ConfigurationError("RFT_USE_SSH_AGENT must be a boolean")


if __name__ == "__main__":
    raise SystemExit(main())
