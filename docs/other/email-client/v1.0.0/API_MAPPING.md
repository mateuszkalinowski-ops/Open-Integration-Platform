# API Mapping — Email Client v1.0.0

Mapping of fields between standard email protocols (IMAP/SMTP/MIME) and the Pinquark Email Client schema.

## IMAP → Pinquark EmailMessage

| IMAP/MIME Field | Pinquark Field | Transformation |
|----------------|---------------|---------------|
| `Message-ID` header | `message_id` | Direct copy |
| `From` header | `sender` | Parsed to `EmailAddress(name, address)` |
| `To` header | `recipients` | Address list parsing |
| `Cc` header | `cc` | Address list parsing |
| `Subject` header | `subject` | RFC 2047 (encoded-words) decoding |
| `Date` header | `date` | Parsed to datetime UTC |
| `X-Priority` header | `priority` | 1-2 = HIGH, 3 = NORMAL, 4-5 = LOW |
| `\Seen` flag | `is_read` | true if flag is set |
| MIME `text/plain` part | `body_text` | Charset decoding |
| MIME `text/html` part | `body_html` | Charset decoding |
| MIME attachment parts | `attachments` | Extraction of name, type, base64 content |
| IMAP folder name | `folder` | Direct copy |
| First 20 headers | `headers` | Key-value dict |

## Pinquark SendEmailRequest → SMTP/MIME

| Pinquark Field | SMTP/MIME Field | Transformation |
|---------------|----------------|---------------|
| `to` | `To` header + RCPT TO | Email address list |
| `subject` | `Subject` header | Direct copy |
| `body_text` | MIME `text/plain` | UTF-8, `multipart/alternative` |
| `body_html` | MIME `text/html` | UTF-8, `multipart/alternative` |
| `cc` | `Cc` header + RCPT TO | Address list |
| `bcc` | (no header) + RCPT TO | SMTP envelope only |
| `priority` | `X-Priority` + `Importance` | HIGH→1/High, NORMAL→3/Normal, LOW→5/Low |
| `reply_to` | `Reply-To` header | Email address |
| `attachments[].filename` | `Content-Disposition: attachment; filename=` | Filename |
| `attachments[].content_base64` | MIME part body | Base64 decode → binary attachment |
| `attachments[].content_type` | MIME part `Content-Type` header | MIME type |

## IMAP Folder Mapping

| IMAP Flag | Typical Name | Description |
|------------|-------------|------|
| `\Inbox` | INBOX | Inbox |
| `\Sent` | Sent / [Gmail]/Sent Mail | Sent messages |
| `\Drafts` | Drafts / [Gmail]/Drafts | Drafts |
| `\Trash` | Trash / [Gmail]/Trash | Trash |
| `\Junk` | Junk / Spam / [Gmail]/Spam | Spam |
| `\All` | [Gmail]/All Mail | All messages |
| (none) | Custom folders | User-created folders |

## Response Statuses

| Operation | Success Status | Possible Errors |
|----------|---------------|---------------|
| `send_email` | `sent` | SMTP connection error, auth error |
| `mark_as_read` | `marked_read` | IMAP error, message not found |
| `delete_email` | `deleted` | IMAP error, message not found |
| `fetch_emails` | EmailsPage with list | IMAP connection error |
| `list_folders` | FolderInfo list | IMAP connection error |
