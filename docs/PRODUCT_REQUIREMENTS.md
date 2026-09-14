# Product requirements

## Objective

Create a Python package that consuming projects can call without knowing the
details of FTP, FTPS, or SFTP authentication.

## Supported connections

- FTP with username and password.
- Explicit FTPS with username and password.
- Implicit FTPS with username and password.
- SFTP with username and password.
- SFTP with an SSH private key without a passphrase.
- SFTP with an encrypted SSH private key and passphrase.
- SFTP using keys exposed by an SSH agent.

Clarification: a passphrase unlocks a private key; it is not a separate server
authentication protocol.

## Public API target

The final package should expose a configuration model, protocol enum, client
factory, typed remote-file metadata, and stable exceptions. A consumer should
be able to use one `connect(config)` entry point and a context manager.

Required operations: connect, close, list, download, upload, exists, mkdir, and
remove. Later phases may add retries, atomic downloads, checksums, progress,
and batch transfers.

## Security requirements

- No secrets in source, logs, exceptions, fixtures, or examples.
- Verify SFTP host keys by default.
- Verify FTPS certificates by default.
- Clearly warn that FTP is unencrypted.
- Unknown host keys require an explicit opt-in.
- Support secrets supplied at runtime; do not force `.env` usage.

## Quality requirements

- Python 3.10 or newer; Windows and Linux compatible.
- Type hints for the public API.
- Unit tests must not contact real servers.
- Integration tests must be opt-in and isolated.
- Build both wheel and source distribution.

## Out of scope for initial release

- SharePoint, HTTP downloads, cloud object storage, web UI, database ingestion,
  scheduling, credential storage, and business-specific file parsing.
