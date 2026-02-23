# Known Issues — Shoper Integrator v1.0.0

## Known Limitations

### 1. No webhook support
Shoper does not provide webhooks in its standard API, so the integrator relies on polling (scraping).
The default interval is 300 seconds (5 minutes).

### 2. Inconsistent brand naming "Shoper" vs "Shopper"
In the original Java implementation (integration-rest-api), the naming was inconsistent —
some classes used "Shoper" and others "Shopper". The new implementation standardizes to "Shoper".

### 3. Bulk API limits
The Shoper Bulk API may have limitations on the number of requests per single operation.
Recommended maximum of 50 requests per bulk call.

### 4. Timezone handling
Shoper stores dates in the shop server's timezone.
Date filters are converted to the "Poland" timezone for compatibility.

### 5. Product images
Fetching product images requires additional requests to `/product-images`.
Disabled by default in the scraper — to be enabled in a future version.

## Bugs Found in the Original Implementation (integration-rest-api)

### CRITICAL

1. **AuthorizationService — inverted token cache logic**: `isBefore(now)` instead of `isAfter(now)`,
   which caused returning an expired token and re-authenticating when the token was still valid.

2. **AddOrUpdateShoperProductUseCase — inverted validation**: `if (categoryId != null)` instead of `== null`,
   which meant the validation threw an error when a category WAS set (opposite of intended).

3. **Hardcoded credentials in application.properties**: Shoper login, password, JWT secret,
   Kafka SASL credentials — exposing sensitive data.

4. **Kafka keystore in repository**: files `kafka/cert.pem` and `kafka/kafka.keystore`
   should not be committed to the repository.

### IMPORTANT

5. **Outdated stack**: Java 11 + Spring Boot 2.5.4 (requires Java 21 + Spring Boot 3.x).
6. **javax.* instead of jakarta.***: migration required for Spring Boot 3.x.
7. **No health/readiness endpoints**.
8. **No Prometheus metrics**.
9. **No circuit breaker**.
10. **No structured JSON logging**.
11. **No tests for Shoper code**.
