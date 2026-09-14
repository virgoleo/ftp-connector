from os import PathLike

from remote_transfer import RemoteEntry, TransferClient


class FakeClient(TransferClient):
    def __init__(self) -> None:
        self.connected = False
        self.closed = False

    def connect(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.closed = True

    def list(self, remote_path: str = ".") -> list[RemoteEntry]:
        return []

    def download(self, remote_path: str, local_path: str | PathLike[str]) -> None:
        return None

    def upload(self, local_path: str | PathLike[str], remote_path: str) -> None:
        return None

    def exists(self, remote_path: str) -> bool:
        return False

    def mkdir(self, remote_path: str) -> None:
        return None

    def remove(self, remote_path: str) -> None:
        return None


def test_context_manager_connects_and_closes() -> None:
    client = FakeClient()

    with client as entered:
        assert entered is client
        assert client.connected
        assert not client.closed

    assert client.closed


def test_context_manager_closes_after_body_error() -> None:
    client = FakeClient()

    try:
        with client:
            raise RuntimeError("body failed")
    except RuntimeError:
        pass

    assert client.closed
