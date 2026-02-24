# Known Issues — FTP/SFTP Integrator v1.0.0

## Limitations

### FTP protocol
- **No TLS/FTPS support** in v1.0.0 — only plain FTP. FTPS (FTP over TLS) will be added in v1.1.0.
- **Active mode** may not work through NAT/firewalls. Use passive mode (default).
- **FTP encoding**: file names with non-ASCII characters may not be handled correctly on all FTP servers. UTF-8 is assumed.

### SFTP protocol
- **Host key verification** is disabled by default (`known_hosts=None`). For production use, consider configuring known hosts.
- **Private key passphrase**: currently not supported. Keys must be unencrypted PEM format.
- **Ed25519 keys**: supported via asyncssh, but ECDSA and RSA are more widely tested.

### General
- **Large file transfers**: files are loaded fully into memory (base64 encoding in API). For files >100 MB, consider streaming support (planned for v1.1.0).
- **Polling state**: stored in SQLite. If the database file is lost, the poller will re-detect all existing files as new.
- **Concurrent connections**: each operation opens a new connection. Connection pooling is planned for v1.1.0.

## Planned for v1.1.0

- FTPS (FTP over TLS) support
- Streaming upload/download for large files
- Connection pooling
- SSH host key verification configuration
- Private key passphrase support
- Recursive directory listing
- File checksum verification (MD5/SHA-256)
