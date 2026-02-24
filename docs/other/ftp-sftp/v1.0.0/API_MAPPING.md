# API Mapping — FTP/SFTP Integrator v1.0.0

## Platform Action → Connector Endpoint Mapping

| Platform Action | HTTP Method | Connector Endpoint | Payload Fields |
|---|---|---|---|
| `file.upload` | `POST` | `/files/upload` | `remote_path`, `filename`, `content_base64`, `overwrite` |
| `file.download` | `GET` | `/files/download` | `remote_path` (query) |
| `file.list` | `GET` | `/files` | `remote_path`, `pattern` (query) |
| `file.delete` | `DELETE` | `/files` | `remote_path` |
| `file.move` | `POST` | `/files/move` | `source_path`, `destination_path` |
| `directory.create` | `POST` | `/directories` | `remote_path` |
| `directory.list` | `GET` | `/directories` | `remote_path` (query) |

## Event Field Mapping

### file.new (emitted by poller)

| Event Field | Type | Description |
|---|---|---|
| `filename` | `string` | Name of the detected file |
| `path` | `string` | Full remote path |
| `size` | `integer` | File size in bytes |
| `modified_at` | `string` (ISO 8601) | Last modification time |
| `account_name` | `string` | Account that detected the file |
| `detected_at` | `string` (ISO 8601) | When the file was detected |

### file.uploaded (emitted after upload)

| Event Field | Type | Description |
|---|---|---|
| `filename` | `string` | Uploaded file name |
| `path` | `string` | Remote path |
| `size` | `integer` | File size in bytes |
| `account_name` | `string` | Account used for upload |

### file.deleted (emitted after deletion)

| Event Field | Type | Description |
|---|---|---|
| `filename` | `string` | Deleted file name |
| `path` | `string` | Remote path |
| `account_name` | `string` | Account used for deletion |

## Common Flow Mappings

### FTP file → WMS document

| FTP/SFTP Field | WMS Field | Notes |
|---|---|---|
| `filename` | `documentName` | File name as document identifier |
| `path` | `sourcePath` | Full path for reference |
| `size` | `fileSize` | File size metadata |
| `modified_at` | `sourceModifiedAt` | Modification timestamp |

### WMS export → FTP upload

| WMS Field | FTP/SFTP Field | Notes |
|---|---|---|
| `documentContent` | `content_base64` | Base64-encoded file content |
| `exportFileName` | `filename` | Target file name |
| `exportPath` | `remote_path` | Target directory |
