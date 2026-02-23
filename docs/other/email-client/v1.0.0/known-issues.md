# Known Issues — Email Client v1.0.0

## 1. Gmail requires App Password

**Problem**: Gmail does not allow IMAP/SMTP login with a standard password — it requires an App Password.

**Solution**: Enable 2FA on the Google account, then generate an App Password in the account security settings. Use the App Password instead of the regular password.

**Status**: Google limitation — OAuth2 support for Gmail/Google Workspace is planned for a future version (v2.0.0).

---

## 2. IMAP IDLE is not supported

**Problem**: The connector uses polling (SEARCH UNSEEN) instead of IMAP IDLE, which means there is a delay in receiving new messages equal to the polling interval.

**Solution**: Set a shorter polling interval (`EMAIL_POLLING_INTERVAL_SECONDS=30`). IMAP IDLE will be added in a future version.

**Status**: Planned for v1.1.0.

---

## 3. Large attachments

**Problem**: Attachments are base64-encoded and transmitted via REST API, which limits their size to ~25MB (configurable).

**Solution**: For large attachments, consider direct access to the mail server. The limit is configurable via `EMAIL_MAX_ATTACHMENT_SIZE_MB`.

**Status**: Current REST architecture limitation.

---

## 4. No OAuth2

**Problem**: Authentication is done via password/App Password. Some providers (Google, Microsoft) prefer or require OAuth2.

**Solution**: Use an App Password or an email server that supports password authentication.

**Status**: OAuth2 planned for v2.0.0.

---

## 5. Blocking IMAP/SMTP operations

**Problem**: The `imaplib` and `smtplib` libraries are synchronous — operations are executed in a thread pool executor, which may limit throughput with a large number of concurrent operations.

**Solution**: The current implementation uses `asyncio.run_in_executor()`. In the future, migration to a natively asynchronous IMAP library (e.g. `aioimaplib`) is possible.

**Status**: Acceptable for typical workloads. Monitored via Prometheus metrics.
