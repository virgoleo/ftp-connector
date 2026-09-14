import remote_transfer


def test_public_api_exports_are_declared() -> None:
    expected = {
        "AuthenticationError",
        "AuthenticationMode",
        "ConfigurationError",
        "ConnectionError",
        "HostKeyVerificationError",
        "OperationError",
        "Protocol",
        "RemoteEntry",
        "RemoteFileExistsError",
        "RemoteFileNotFoundError",
        "RemotePermissionError",
        "RemoteTransferError",
        "SFTPClient",
        "TransferClient",
        "TransferConfig",
    }

    assert set(remote_transfer.__all__) == expected
    for name in expected:
        assert getattr(remote_transfer, name) is not None
