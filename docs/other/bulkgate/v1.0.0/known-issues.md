# BulkGate SMS Gateway — Known Issues & Limitations

## v1.0.0

### No Sandbox Environment
BulkGate does not provide a dedicated sandbox/staging API. All API calls go to the production endpoint (`portal.bulkgate.com`). Test messages consume real credits.

### SMPP Not Supported
This connector implements HTTP APIs only (Simple v1.0 and Advanced v2.0). SMPP protocol is not supported — contact BulkGate for SMPP access if high-throughput is needed.

### Email-to-SMS (SMTP API) Not Implemented
The SMTP-based Email-to-SMS API is not implemented in this version. Use the HTTP APIs for programmatic SMS sending.

### WhatsApp and RCS Channels
While the Advanced API v2.0 supports WhatsApp and RCS channel objects, this connector currently implements only SMS and Viber channel cascades. WhatsApp and RCS support is planned for v1.1.0.

### Delivery Report Payload Format
BulkGate's delivery report webhook payload format is not strictly documented. The `DeliveryReportPayload` schema is based on available documentation and may need adjustment based on actual webhook payloads received.

### Sender ID Country Restrictions
Some sender ID types (e.g., `gText` — alphanumeric sender) are not available in all countries. The connector does not validate sender ID availability per country — BulkGate will deliver with a fallback sender type if the requested type is unavailable.

### Message Length
- Standard (7-bit): 160 characters per SMS part, max 612 characters total (concatenated)
- Unicode: 70 characters per SMS part, max 268 characters total
- Longer messages are split and each part is billed separately
