# Sandbox Setup — Email Client v1.0.0

## Option 1: Gmail (recommended for testing)

### Step 1: Create a test Gmail account

1. Create a new Google account: https://accounts.google.com/signup
2. Enable 2FA (required for App Password): https://myaccount.google.com/security

### Step 2: Generate an App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Choose an app name (e.g. "Pinquark Email Client")
3. Copy the generated password (16 characters)

### Step 3: Account configuration

```yaml
accounts:
  - name: test-gmail
    email_address: "test.pinquark@gmail.com"
    password: "xxxx xxxx xxxx xxxx"  # App Password
    imap_host: "imap.gmail.com"
    imap_port: 993
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    use_ssl: true
    polling_folder: "INBOX"
    environment: sandbox
```

### Step 4: Enable IMAP in Gmail

1. Gmail → Settings → See all settings → Forwarding and POP/IMAP
2. Enable IMAP
3. Save changes

---

## Option 2: Mailtrap (email sandbox)

[Mailtrap](https://mailtrap.io) is an email testing service — emails are not actually delivered.

1. Create an account at https://mailtrap.io
2. Create an Inbox
3. Use the SMTP credentials from the "SMTP Settings" tab

```yaml
accounts:
  - name: test-mailtrap
    email_address: "user@mailtrap.io"
    password: "mailtrap-password"
    imap_host: "imap.mailtrap.io"
    imap_port: 993
    smtp_host: "smtp.mailtrap.io"
    smtp_port: 587
    use_ssl: true
    environment: sandbox
```

---

## Option 3: Local server (Docker)

Use [Greenmail](https://greenmail-mail-test.github.io/greenmail/) or [MailHog](https://github.com/mailhog/MailHog):

```yaml
# docker-compose.test.yml
services:
  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"   # SMTP
      - "8025:8025"   # Web UI
```

Configuration:
```yaml
accounts:
  - name: test-local
    email_address: "test@localhost"
    password: ""
    imap_host: "localhost"
    imap_port: 143
    smtp_host: "localhost"
    smtp_port: 1025
    use_ssl: false
    environment: sandbox
```

---

## Credential Storage

Sandbox credentials should NOT be committed to the repository.
Use environment variables or CI/CD secrets:

```bash
# CI/CD secrets
EMAIL_SANDBOX_ADDRESS=test.pinquark@gmail.com
EMAIL_SANDBOX_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_SANDBOX_IMAP_HOST=imap.gmail.com
EMAIL_SANDBOX_SMTP_HOST=smtp.gmail.com
```
