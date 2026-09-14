# Security checklist

- Reject unknown SSH host keys by default.
- Use the operating system's trusted CA store for FTPS by default.
- Never disable verification as a hidden fallback.
- Redact passwords, passphrases, keys, and tokens from logs and exceptions.
- Ensure dataclass/model representations do not reveal secrets.
- Set connection, authentication, and operation timeouts.
- Validate local and remote paths without assuming Windows separators remotely.
- Document the risk of plain FTP.
- Use fake credentials and mocked clients in unit tests.
