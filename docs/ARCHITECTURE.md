# Architecture

```text
remote-file-transfer-kit/
├── AGENTS.md
├── CODEX_TASKS.md
├── README.md
├── ROADMAP.md
├── pyproject.toml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PRODUCT_REQUIREMENTS.md
│   └── SECURITY.md
├── examples/
│   └── README.md
├── src/remote_transfer/
│   ├── __init__.py
│   ├── base.py
│   ├── config.py
│   ├── exceptions.py
│   ├── factory.py
│   ├── models.py
│   └── transports/
│       ├── __init__.py
│       ├── ftp.py
│       ├── ftps.py
│       └── sftp.py
└── tests/
    ├── unit/
    └── integration/
```

The files not yet present should be created by Codex in the relevant phase.
Protocol adapters may depend on third-party packages, but domain configuration,
models, and exceptions should not depend on a transport implementation.

Dependencies point inward: public API → factory/interface → transport adapters.
Consuming applications must not import adapter internals.
