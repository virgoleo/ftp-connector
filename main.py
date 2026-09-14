"""Production-safe entry point for two SFTP connections.

Supply settings for any number of servers through ``SFTP_<NAME>_*`` variables.
This script never reads or writes secrets to disk.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path

# Allow ``python main.py`` and VS Code's default debugger to use the src-layout
# package without requiring a manually configured PYTHONPATH.
_SOURCE_DIRECTORY = Path(__file__).resolve().parent / "src"
if _SOURCE_DIRECTORY.is_dir():
    sys.path.insert(0, str(_SOURCE_DIRECTORY))

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
) -> dict[str, TransferConfig]:
    """Build configurations for every server named by ``SFTP_SERVERS``."""

    values = os.environ if environment is None else environment
    server_names = _server_names(values)
    return {
        server_name: _load_sftp_config(values, f"SFTP_{server_name}_")
        for server_name in server_names
    }


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
    """Connect, list each configured server's remote path, and close safely."""

    try:
        configs = load_configs_from_environment()
        for server_name, config in configs.items():
            remote_path = os.environ.get(f"SFTP_{server_name}_REMOTE_PATH", ".")
            with SFTPClient(config) as client:
                print(f"{server_name} entries:")
                for entry in client.list(remote_path):
                    print(entry.path)
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


def _server_names(values: Mapping[str, str]) -> list[str]:
    """Return valid, unique server names from the comma-separated server list."""

    names = [name.strip().upper() for name in _required_environment_value(values, "SFTP_SERVERS").split(",")]
    if not names or any(not name or re.fullmatch(r"[A-Z][A-Z0-9_]*", name) is None for name in names):
        raise ConfigurationError("SFTP_SERVERS must contain comma-separated server names")
    if len(set(names)) != len(names):
        raise ConfigurationError("SFTP_SERVERS must not contain duplicate server names")
    return names


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
