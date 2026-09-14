# Codex implementation tasks

## Phase 1 — Domain and public API

Create protocol/configuration models, remote entry metadata, stable exceptions,
the abstract client interface, and public exports. Add validation and unit tests.
Do not implement network connections yet.

## Phase 2 — SFTP adapter

Implement password, private-key, encrypted-key/passphrase, and SSH-agent modes.
Enforce host-key verification. Mock the transport in unit tests.

## Phase 3 — FTP and FTPS adapters

Implement FTP plus explicit and implicit FTPS. Verify certificates by default.
Test login, cleanup, listing, upload, and download through mocks.

## Phase 4 — Factory and examples

Implement `connect(config)`, context management, safe examples, and CLI. Ensure
examples read secrets at runtime and never contain real endpoints.

## Phase 5 — Production hardening

Add error translation, retry policy, atomic downloads, progress callbacks,
structured logging with redaction, and optional integration-test scaffolding.

## Phase 6 — Release

Finalize packaging metadata, changelog, CI matrix, coverage threshold, wheel and
sdist build, and private-package-index publishing documentation.
