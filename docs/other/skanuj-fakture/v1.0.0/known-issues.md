# Known Issues — SkanujFakture v1.0.0

## 1. Non-standard API port

**Description**: The SkanujFakture API runs on port 8443 instead of the standard 443.

**Impact**: Some clients behind firewalls may have port 8443 blocked.

**Workaround**: Ensure firewall/proxy rules allow HTTPS traffic to `skanujfakture.pl:8443`.

## 2. No dedicated sandbox environment

**Description**: SkanujFakture does not offer a separate test environment. Testing is done on a production account with the starter plan.

**Impact**: Test documents end up on the production account.

**Workaround**: Use a separate account for testing, delete test documents after completion.

## 3. File size limits

**Description**: No documented file size limit in the official API documentation.

**Workaround**: The integrator sets a default limit of 25MB (`max_upload_size_mb`). Large PDF files are split into pages.

## 4. Rate limiting

**Description**: The official documentation does not specify request limits.

**Workaround**: Polling is set to every 300s (5 min) by default, which should be safe. Adjustable in configuration.

## 5. Error response format

**Description**: The API does not always return structured error messages — sometimes HTML instead of JSON on server errors.

**Workaround**: The HTTP client handles both formats; errors are logged with full context.
