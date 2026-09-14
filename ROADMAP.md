# Roadmap

## 0.1 — Foundation

- Common API for FTP, FTPS, and SFTP
- Password, SSH key/passphrase, and SSH agent authentication
- Secure host-key and TLS defaults
- Unit tests and CLI

## 0.2 — Production hardening

- Retry policy with exponential backoff and transient-error classification
- Atomic download via temporary file and rename
- Checksums, transfer progress callback, timeouts, structured logging
- Proxy and SSH jump-host support
- Integration tests using disposable test servers

## 0.3 — Distribution

- CI for Windows/Linux and Python 3.10–3.13
- Semantic versioning and changelog automation
- Build signed wheel/sdist
- Publish to a private package index or PyPI

