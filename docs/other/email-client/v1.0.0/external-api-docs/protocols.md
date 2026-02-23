# External API Documentation — Email Protocols

## IMAP4rev1 (RFC 3501)

Protocol documentation: https://datatracker.ietf.org/doc/html/rfc3501

### Commands Used

| Command | Usage in Connector | Description |
|---------|---------------------|------|
| `LOGIN` | Authentication | Login with username and password |
| `LIST` | `list_folders()` | List IMAP folders |
| `SELECT` | Before each fetch | Select folder |
| `SEARCH` | `fetch_emails()` | Search messages (ALL, UNSEEN, SINCE) |
| `FETCH` | `get_email()` | Retrieve full message (RFC822) |
| `STORE` | `mark_as_read()`, `delete_email()` | Set flags (\Seen, \Deleted) |
| `EXPUNGE` | `delete_email()` | Permanently delete flagged messages |
| `NOOP` | `ping()` | Connection health check |
| `LOGOUT` | `disconnect()` | Close session |

### Ports

| Port | Encryption | Usage |
|------|-------------|--------|
| 993 | SSL/TLS (immediate) | Default — `IMAP4_SSL` |
| 143 | STARTTLS (upgrade) | Alternative — `IMAP4` + `STARTTLS` |

---

## SMTP (RFC 5321)

Protocol documentation: https://datatracker.ietf.org/doc/html/rfc5321

### Commands Used

| Command | Usage in Connector | Description |
|---------|---------------------|------|
| `EHLO` | After connection | Client identification + extension discovery |
| `STARTTLS` | Encryption | Upgrade to TLS (port 587) |
| `AUTH LOGIN/PLAIN` | Authentication | Login with username and password |
| `MAIL FROM` | `send_email()` | Sender address |
| `RCPT TO` | `send_email()` | Recipient address(es) |
| `DATA` | `send_email()` | Transmit message content (MIME) |
| `QUIT` | After sending | Close session |

### Ports

| Port | Encryption | Usage |
|------|-------------|--------|
| 587 | STARTTLS | Default — `SMTP` + `starttls()` |
| 465 | SSL/TLS (immediate) | Alternative — `SMTP_SSL` |
| 25 | None (not recommended) | Internal networks only |

---

## MIME (RFC 2045-2049)

Email message structure in MIME format.

### Message Structure Used

```
multipart/mixed
├── multipart/alternative
│   ├── text/plain (body_text)
│   └── text/html (body_html)
├── application/pdf (attachment 1)
└── image/png (attachment 2)
```

### Headers

| Header | RFC | Usage |
|--------|-----|--------|
| `From` | 5322 | Sender address |
| `To` | 5322 | Recipient addresses |
| `Cc` | 5322 | Carbon copy |
| `Subject` | 5322 | Subject (with RFC 2047 encoded-words support) |
| `Date` | 5322 | Send date |
| `Message-ID` | 5322 | Unique message identifier |
| `X-Priority` | non-standard | Priority: 1 (high) — 5 (low) |
| `Importance` | non-standard | Priority in words: High / Normal / Low |
| `Reply-To` | 5322 | Reply-to address |
| `Content-Type` | 2045 | MIME content type |
| `Content-Disposition` | 2183 | attachment / inline |
| `Content-Transfer-Encoding` | 2045 | base64 / quoted-printable |
