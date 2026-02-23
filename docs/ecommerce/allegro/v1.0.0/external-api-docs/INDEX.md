# Allegro External API Documentation — Index

Downloaded Allegro REST API documentation for integrator implementation purposes.

Source: [developer.allegro.pl](https://developer.allegro.pl)

Download date: 2026-02-20

## Contents

| File | Description | Size | Source |
|------|------|---------|--------|
| `openapi-3.0-swagger.yaml` | Full OpenAPI 3.0 (Swagger) specification of the Allegro REST API — all endpoints, schemas, parameters | 324 KB | [GitHub/allegro-api](https://github.com/coffeedesk/allegro-api-client-php/blob/master/swagger.yaml) |
| `allegro-rest-api-reference.md` | Complete API reference — list of all endpoints with descriptions, parameters, and responses | 516 KB | [developer.allegro.pl/documentation](https://developer.allegro.pl/documentation) |
| `authentication-and-authorization.md` | Tutorial: OAuth2 authentication (Device Flow, Authorization Code, Client Credentials), token refresh | 65 KB | [developer.allegro.pl/tutorials/uwierzytelnianie](https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR) |
| `order-management.md` | Tutorial: order handling — order events, checkout forms, statuses, fulfillment | 43 KB | [developer.allegro.pl/tutorials/zamowienia](https://developer.allegro.pl/tutorials/jak-obslugiwac-zamowienia-GRaj0q6Gwuy) |
| `offer-management-tutorial.md` | Tutorial: listing and managing offers — products, parameters, images, variants | 256 KB | [developer.allegro.pl/tutorials/oferty](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9M71Bu6) |
| `stock-and-offer-management-tutorial.md` | Tutorial: stock level management, pricing, batch modifications | 224 KB | [developer.allegro.pl/tutorials/oferty](https://developer.allegro.pl/tutorials/jak-zarzadzac-ofertami-7GzB2L37ase) |

## Key Endpoints Used by the Integrator

### Orders
- `GET /order/events` — fetch order events (polling)
- `GET /order/checkout-forms` — list orders
- `GET /order/checkout-forms/{id}` — order details
- `PUT /order/checkout-forms/{id}/fulfillment` — update fulfillment status

### Offers
- `GET /sale/offers/{id}` — offer details (name, EAN, product)
- `PUT /sale/offer-quantity-change-commands/{id}` — quantity change (stock)

### Products
- `GET /sale/products/{id}` — product details (EAN from parameters)

### Authentication
- `POST /auth/oauth/device` — start Device Flow
- `POST /auth/oauth/token` — exchange code for token / refresh token

## Documentation Updates

Documentation should be updated when:
- A new version of the Allegro REST API is released
- New endpoints are added to the integrator
- Changes occur in the authentication process

Check for updates at: https://developer.allegro.pl/news/
