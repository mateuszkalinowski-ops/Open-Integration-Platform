# Sandbox Setup — FTP/SFTP Integrator

## Local test SFTP server

The `docker-compose.yml` includes a test SFTP server (`atmoz/sftp:alpine`) for development and testing.

### Start test server

```bash
cd integrators/other/ftp-sftp/v1.0.0
docker compose --profile dev up -d sftp-server
```

### Test server credentials

| Parameter | Value |
|---|---|
| Host | `localhost` (or `sftp-server` from Docker network) |
| Port | `2222` (mapped to container port 22) |
| Protocol | `sftp` |
| Username | `testuser` |
| Password | `testpass` |
| Upload directory | `/home/testuser/upload` |

### Configure account for test server

Add to `config/accounts.yaml`:

```yaml
accounts:
  - name: local-test
    host: sftp-server
    protocol: sftp
    port: 22
    username: testuser
    password: testpass
    base_path: /home/testuser/upload
    environment: development
```

Or from host machine:

```yaml
accounts:
  - name: local-test
    host: localhost
    protocol: sftp
    port: 2222
    username: testuser
    password: testpass
    base_path: /home/testuser/upload
    environment: development
```

### Local FTP server (vsftpd)

For FTP testing, you can use the `fauria/vsftpd` Docker image:

```bash
docker run -d \
  --name test-ftp \
  -p 20-21:20-21 \
  -p 21100-21110:21100-21110 \
  -e FTP_USER=ftpuser \
  -e FTP_PASS=ftppass \
  -e PASV_ADDRESS=127.0.0.1 \
  -e PASV_MIN_PORT=21100 \
  -e PASV_MAX_PORT=21110 \
  fauria/vsftpd
```

Credentials: `ftpuser` / `ftppass`, port `21`, passive mode ports `21100-21110`.

## External test servers

For CI/CD integration testing, public FTP test servers can be used:

| Server | Protocol | Host | Credentials |
|---|---|---|---|
| Rebex | SFTP | `test.rebex.net:22` | `demo` / `password` |
| Rebex | FTP | `test.rebex.net:21` | `demo` / `password` |

Note: these are read-only servers suitable for listing and downloading only.
