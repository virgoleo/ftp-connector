# Coding agent guide

## Goal

Build a secure, reusable Python library offering one API for FTP, FTPS, and
SFTP. Keep protocol-specific behavior behind a common client interface.

## Rules

- Never commit credentials, private keys, access tokens, server fingerprints,
  or real company hostnames.
- Reject unknown SSH host keys by default.
- Verify TLS certificates by default.
- Add or update tests with every behavior change.
- Preserve backward compatibility in the public imports from
  `remote_transfer/__init__.py`.
- Keep network integration tests separate from unit tests.
- Use typed exceptions from `exceptions.py`; do not expose raw library errors
  when a stable package error is practical.
- Implement only the phase explicitly requested by the user.
- Before coding, inspect existing files and state a short plan.
- Do not silently expand scope or add a UI, database, scheduler, or web API.

## Definition of done

Run:

```powershell
ruff check .
pytest
mypy src
python -m build
```
