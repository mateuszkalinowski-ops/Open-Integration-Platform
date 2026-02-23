# FedEx Courier Integration — v1.0.0

## Overview
FedEx Ship API integration for creating shipments, retrieving labels, cancelling shipments, and locating service points via REST API with OAuth2 authentication.

## External API
- **Protocol**: REST (JSON)
- **API URL (Production)**: https://apis.fedex.com/
- **API URL (Sandbox)**: https://apis-sandbox.fedex.com/
- **Developer Portal**: https://developer.fedex.com/
- **Documentation**: https://developer.fedex.com/api/en-ai/catalog/ship/v1/docs.html

## Authentication
- OAuth2 `client_credentials` grant type
- Obtain an access token via `POST /oauth/token` with `client_id` and `client_secret`
- Access tokens are short-lived; the integrator must handle token refresh before expiry
- Credentials are obtained by registering an application on the FedEx Developer Portal

## Key Capabilities
- Create single and multi-piece shipments
- Generate shipping labels (PDF format)
- Cancel shipments
- Look up FedEx service points / drop-off locations
- Multiple service types (FedEx International Priority, Economy, Ground, etc.)
- Flexible payment options: SENDER, RECIPIENT, THIRD_PARTY

## Configuration
See `.env.example` in the integrator directory for required environment variables.

## Sandbox
FedEx provides a full sandbox environment at `apis-sandbox.fedex.com`.
Register at https://developer.fedex.com/ to obtain sandbox credentials.

## Rate Limits
FedEx applies rate limits per application. Consult the Developer Portal for current thresholds. The integrator implements exponential backoff with jitter on 429 responses.
