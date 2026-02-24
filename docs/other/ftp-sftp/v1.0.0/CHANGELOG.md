# Changelog

## [1.0.0] - 2026-02-24

### Added
- Initial release of FTP/SFTP connector
- Dual protocol support: FTP (aioftp) and SFTP (asyncssh)
- File operations: upload, download, list, delete, move/rename
- Directory operations: create, list
- Background polling for new files with state persistence (SQLite)
- Multi-account support (YAML config or environment variables)
- Kafka event publishing (file.new, file.uploaded, file.deleted)
- Platform event notification for Flow Engine integration
- Glob pattern filtering for file listing
- Connection testing endpoint
- Prometheus metrics at /metrics
- Health and readiness endpoints
- Swagger UI documentation
