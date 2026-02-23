# FedEx Ship API — API Reference

## Connection Details

| Environment | Base URL |
|-------------|----------|
| Production  | `https://apis.fedex.com/` |
| Sandbox     | `https://apis-sandbox.fedex.com/` |

**Protocol**: REST (JSON over HTTPS)

**Developer Portal**: https://developer.fedex.com/

---

## Authentication

FedEx uses OAuth2 with the `client_credentials` grant type.

### POST /oauth/token

Obtains an access token.

**Request:**

```
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={API_KEY}
&client_secret={SECRET_KEY}
```

**Response:**

| Field          | Type   | Description |
|---------------|--------|-------------|
| `access_token` | string | Bearer token for API calls |
| `token_type`   | string | Always `bearer` |
| `expires_in`   | int    | Token lifetime in seconds |
| `scope`        | string | Granted scopes |

All subsequent requests must include:
```
Authorization: Bearer {access_token}
```

---

## Shipment Operations

### POST /ship/v1/shipments

Creates a shipment and generates labels.

**Request body:**

| Field                    | Type          | Required | Description |
|-------------------------|---------------|----------|-------------|
| `accountNumber.value`   | string        | Yes      | FedEx account number |
| `requestedShipment`     | RequestedShipment | Yes  | Shipment details |

**RequestedShipment structure:**

| Field                  | Type           | Required | Description |
|-----------------------|----------------|----------|-------------|
| `shipper`             | Party          | Yes      | Sender details |
| `recipients`          | Party[]        | Yes      | Receiver details |
| `pickupType`          | string         | Yes      | e.g. `DROPOFF_AT_FEDEX_LOCATION`, `CONTACT_FEDEX_TO_SCHEDULE` |
| `serviceType`         | string         | Yes      | Service type code (see table below) |
| `packagingType`       | string         | Yes      | Packaging type code (see table below) |
| `shippingChargesPayment` | Payment     | Yes      | Who pays for shipping |
| `labelSpecification`  | LabelSpec      | Yes      | Label format options |
| `requestedPackageLineItems` | Package[] | Yes      | Package details |

**Party structure:**

| Field              | Type    | Description |
|-------------------|---------|-------------|
| `contact.personName` | string | Contact name |
| `contact.phoneNumber` | string | Phone number |
| `contact.emailAddress` | string | Email |
| `address.streetLines` | string[] | Street address lines |
| `address.city`    | string  | City |
| `address.stateOrProvinceCode` | string | State/province |
| `address.postalCode` | string | Postal code |
| `address.countryCode` | string | ISO 3166-1 alpha-2 country code |

**Payment structure:**

| Field           | Type   | Description |
|----------------|--------|-------------|
| `paymentType`  | string | `SENDER`, `RECIPIENT`, or `THIRD_PARTY` |
| `payor.responsibleParty.accountNumber.value` | string | Account number of payer |

**LabelSpec structure:**

| Field               | Type   | Description |
|--------------------|--------|-------------|
| `labelFormatType`  | string | `COMMON2D` |
| `imageType`        | string | `PDF`, `PNG`, `ZPLII` |
| `labelStockType`   | string | e.g. `PAPER_85X11_TOP_HALF_LABEL` |

**Package structure:**

| Field            | Type    | Description |
|-----------------|---------|-------------|
| `weight.units`  | string  | `KG` or `LB` |
| `weight.value`  | float   | Package weight |
| `dimensions.length` | int | Length |
| `dimensions.width` | int  | Width |
| `dimensions.height` | int | Height |
| `dimensions.units` | string | `CM` or `IN` |

**Response:**

| Field                        | Type    | Description |
|-----------------------------|---------|-------------|
| `transactionId`             | string  | Transaction identifier |
| `output.transactionShipments[].masterTrackingNumber` | string | Main tracking number |
| `output.transactionShipments[].pieceResponses[].trackingNumber` | string | Per-piece tracking |
| `output.transactionShipments[].pieceResponses[].packageDocuments[].encodedLabel` | string | Base64-encoded label |

---

### PUT /ship/v1/shipments/cancel

Cancels a previously created shipment.

**Request body:**

| Field                    | Type   | Required | Description |
|-------------------------|--------|----------|-------------|
| `accountNumber.value`   | string | Yes      | FedEx account number |
| `trackingNumber`        | string | Yes      | Tracking number to cancel |

**Response:**

| Field                      | Type    | Description |
|---------------------------|---------|-------------|
| `output.cancelledShipment` | boolean | Whether cancellation succeeded |
| `output.alerts`           | Alert[] | Warnings or information |

---

## Location Services

### POST /location/v1/locations

Searches for FedEx service points and drop-off locations.

**Request body:**

| Field                          | Type   | Required | Description |
|-------------------------------|--------|----------|-------------|
| `location.address.postalCode` | string | Yes      | Search area postal code |
| `location.address.countryCode`| string | Yes      | ISO country code |
| `resultsRequested`            | int    | No       | Max results (default 10) |

**Response:**

| Field                                  | Type       | Description |
|---------------------------------------|------------|-------------|
| `output.locationDetailList[].locationId` | string   | Location identifier |
| `output.locationDetailList[].contactAndAddress` | object | Address details |
| `output.locationDetailList[].storeHours` | object[] | Operating hours |

---

## Service Types

| Code | Description |
|------|-------------|
| `FEDEX_INTERNATIONAL_PRIORITY` | International Priority |
| `FEDEX_INTERNATIONAL_ECONOMY` | International Economy |
| `INTERNATIONAL_FIRST` | International First |
| `FEDEX_GROUND` | Ground service |
| `FEDEX_EXPRESS_SAVER` | Express Saver |
| `FIRST_OVERNIGHT` | First Overnight |
| `PRIORITY_OVERNIGHT` | Priority Overnight |
| `STANDARD_OVERNIGHT` | Standard Overnight |
| `FEDEX_2_DAY` | 2-Day delivery |
| `FEDEX_2_DAY_AM` | 2-Day AM delivery |

## Packaging Types

| Code | Description |
|------|-------------|
| `YOUR_PACKAGING` | Custom packaging |
| `FEDEX_ENVELOPE` | FedEx envelope |
| `FEDEX_BOX` | FedEx box |
| `FEDEX_SMALL_BOX` | FedEx small box |
| `FEDEX_MEDIUM_BOX` | FedEx medium box |
| `FEDEX_LARGE_BOX` | FedEx large box |
| `FEDEX_PAK` | FedEx Pak |
| `FEDEX_TUBE` | FedEx tube |

---

## Error Handling

FedEx returns structured error responses:

```json
{
  "transactionId": "abc-123",
  "errors": [
    {
      "code": "INVALID.INPUT.EXCEPTION",
      "message": "Invalid field value",
      "parameterList": [
        {
          "key": "fieldName",
          "value": "serviceType"
        }
      ]
    }
  ]
}
```

**Common error codes:**

| Code | HTTP Status | Description |
|------|------------|-------------|
| `NOT.AUTHORIZED.ERROR` | 401 | Invalid or expired access token |
| `INVALID.INPUT.EXCEPTION` | 400 | Request validation failure |
| `SERVICE.UNAVAILABLE.ERROR` | 503 | FedEx API temporarily unavailable |
| `RATE.LIMIT.EXCEEDED` | 429 | Too many requests — back off and retry |
| `SHIPMENT.NOT.FOUND` | 404 | Tracking number not found |

---

## Shipment Flow Summary

```
POST /oauth/token
  │
  ▼
POST /ship/v1/shipments  ──▶  Label (PDF) + Tracking Number
  │
  ├──▶ PUT /ship/v1/shipments/cancel  (if needed)
  │
  ▼
POST /location/v1/locations  (service points lookup)
```
