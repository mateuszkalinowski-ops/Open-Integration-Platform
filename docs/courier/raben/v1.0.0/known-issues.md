# Raben Group — Known Issues and Limitations

## v1.0.0

### API Documentation
- Raben Group does not provide publicly available REST API documentation. The integration is based on the myRaben platform capabilities and common logistics API patterns.
- API endpoints and schemas may need adjustment once official API documentation is obtained from Raben.

### ETA
- ETA is only available once the shipment is on a delivery vehicle with active GPS tracking.
- ETA accuracy is +/- 2 hours as stated by Raben.
- ETA may not be available for all shipment types or routes.

### PCD (Photo Confirming Delivery)
- PCD photos are only available after delivery is completed.
- PCD must be enabled at order creation time (`pcd_enabled: true`).
- Photo URLs may expire after a certain period.

### Service Availability
- Not all service types (Premium 08/10/12/16) are available for all routes and destinations.
- Cargo Premium services may have additional surcharges.
- Some routes may only support Cargo Classic.

### Rate Limiting
- Raben API rate limits are not publicly documented.
- The integrator implements exponential backoff on 429 responses.

### Multi-Country Support
- The integrator supports Raben Group operations across 17 European countries.
- Country-specific service availability may vary.
- Address format requirements differ by country.
