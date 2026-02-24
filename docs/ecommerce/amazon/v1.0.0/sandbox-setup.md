# Amazon SP-API Sandbox Setup

## Overview

Amazon provides a sandbox environment for testing SP-API calls without affecting real seller data.

## Setup Steps

### 1. Register as SP-API Developer

1. Log in to **Seller Central** → Apps & Services → Develop Apps
2. Complete identity verification (government ID + proof of address)
3. Select required roles:
   - **Product Listing** — for Catalog API access
   - **Inventory and Order Tracking** — for Orders and Feeds API access
4. Wait for approval (typically 1-3 business days)

### 2. Register Your Application

1. In Seller Central → Apps & Services → Develop Apps → Add new app client
2. Configure:
   - **API Type**: SP-API
   - **IAM ARN**: Your AWS IAM ARN (for signing requests, if applicable)
3. Note the generated `client_id` and `client_secret`

### 3. Obtain Seller Authorization

For self-authorization (your own seller account):

1. In Seller Central → Apps & Services → Develop Apps
2. Click "Authorize" on your registered app
3. This generates a `refresh_token` for your seller account

For third-party authorization:

1. Generate an OAuth authorization URL
2. Seller visits the URL and grants permission
3. Amazon redirects with an `authorization_code`
4. Exchange for `refresh_token`

### 4. Configure Sandbox Mode

Set `sandbox_mode: true` in the account configuration:

```yaml
accounts:
  - name: sandbox
    client_id: "amzn1.application-oa2-client.xxxx"
    client_secret: "your-client-secret"
    refresh_token: "Atzr|XXXX"
    marketplace_id: "ATVPDKIKX0DER"
    region: "na"
    sandbox_mode: true
```

Or via environment:

```bash
AMAZON_ACCOUNT_0_SANDBOX_MODE=true
```

### 5. Sandbox Limitations

- Sandbox uses the same base URL but with sandbox-specific paths
- Limited data — only predefined test scenarios are available
- Not all API operations have sandbox support
- Token refresh works identically to production

## Credential Storage

- **CI/CD**: Store `client_id`, `client_secret`, and `refresh_token` in CI/CD secrets
- **Local dev**: Use `.env` file (excluded from git)
- **Production**: Use platform Credential Vault (AES-256-GCM encrypted)

## Required IAM Roles (if using AWS Signature)

For direct SP-API calls using AWS Signature v4 (legacy):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "execute-api:Invoke",
      "Resource": "arn:aws:execute-api:*:*:*"
    }
  ]
}
```

> **Note**: Since September 2023, AWS Signature is no longer required for SP-API.
> LWA (Login with Amazon) tokens are sufficient for authentication.
