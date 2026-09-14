"""Production-safe entry point for two SFTP connections.

Supply source settings through ``SOURCE_*`` variables and destination settings
through ``DEST_*`` variables. This script never reads or writes secrets to disk.
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
    """Build one SFTP configuration from the legacy ``RFT_*`` variables."""

    values = os.environ if environment is None else environment
    return _load_sftp_config(values, "RFT_")


def load_configs_from_environment(
    environment: Mapping[str, str] | None = None,
) -> tuple[TransferConfig, TransferConfig]:
    """Build source and destination SFTP configurations from environment variables."""

    values = os.environ if environment is None else environment
    return _load_sftp_config(values, "SOURCE_"), _load_sftp_config(values, "DEST_")


def _load_sftp_config(values: Mapping[str, str], prefix: str) -> TransferConfig:
    """Build one strictly SFTP configuration using the supplied variable prefix."""

    try:
        protocol = Protocol(values.get(f"{prefix}PROTOCOL", "sftp").lower())
        port = _optional_integer(values.get(f"{prefix}PORT"))
        connection_timeout = _optional_float(values.get(f"{prefix}CONNECTION_TIMEOUT"), 10.0)
        authentication_timeout = _optional_float(
            values.get(f"{prefix}AUTHENTICATION_TIMEOUT"), 10.0
        )
        operation_timeout = _optional_float(values.get(f"{prefix}OPERATION_TIMEOUT"), 30.0)
    except ValueError as exc:
        raise ConfigurationError(f"Invalid numeric or protocol setting for {prefix}") from exc

    if protocol is not Protocol.SFTP:
        raise ConfigurationError(f"{prefix}PROTOCOL must be sftp")
    return TransferConfig(
        protocol=protocol,
        host=_required_environment_value(values, f"{prefix}HOST"),
        username=_required_environment_value(values, f"{prefix}USERNAME"),
        port=port,
        password=_optional_text(values.get(f"{prefix}PASSWORD")),
        private_key_path=_optional_path(values.get(f"{prefix}PRIVATE_KEY_PATH")),
        private_key_passphrase=_optional_text(values.get(f"{prefix}PRIVATE_KEY_PASSPHRASE")),
        use_ssh_agent=_boolean_environment_value(values.get(f"{prefix}USE_SSH_AGENT", "false")),
        known_hosts_path=_optional_path(values.get(f"{prefix}KNOWN_HOSTS_PATH")),
        connection_timeout=connection_timeout,
        authentication_timeout=authentication_timeout,
        operation_timeout=operation_timeout,
    )


def main() -> int:
    """Connect, list each configured remote path, and close safely."""

    try:
        source_config, destination_config = load_configs_from_environment()
        source_path = os.environ.get("SOURCE_REMOTE_PATH", ".")
        destination_path = os.environ.get("DEST_REMOTE_PATH", ".")
        with SFTPClient(source_config) as source, SFTPClient(destination_config) as destination:
            print("Source entries:")
            for entry in source.list(source_path):
                print(entry.path)
            print("Destination entries:")
            for entry in destination.list(destination_path):
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
