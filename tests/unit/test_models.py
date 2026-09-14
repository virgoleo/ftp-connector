from datetime import datetime, timezone

import pytest

from remote_transfer import ConfigurationError, RemoteEntry


def test_remote_entry_preserves_metadata() -> None:
    modified_at = datetime(2026, 1, 2, tzinfo=timezone.utc)

    entry = RemoteEntry(
        path="/incoming/report.csv",
        name="report.csv",
        is_directory=False,
        size=42,
        modified_at=modified_at,
    )

    assert entry.path == "/incoming/report.csv"
    assert entry.name == "report.csv"
    assert entry.size == 42
    assert entry.modified_at is modified_at


@pytest.mark.parametrize(
    "kwargs",
    [
        {"path": "", "name": "file", "size": 0},
        {"path": "/file", "name": "", "size": 0},
        {"path": "/file", "name": "file", "size": -1},
        {"path": "/bad\x00path", "name": "file", "size": 0},
    ],
)
def test_remote_entry_rejects_invalid_metadata(kwargs: dict[str, object]) -> None:
    with pytest.raises(ConfigurationError):
        RemoteEntry(is_directory=False, **kwargs)  # type: ignore[arg-type]
