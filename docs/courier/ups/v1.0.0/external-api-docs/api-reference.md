# UPS REST API — API Reference

Source: https://developer.ups.com/api/reference

## Base URLs
- Production: https://onlinetools.ups.com/
- Sandbox: https://wwwcie.ups.com/

## Authentication

### Obtain Access Token
`POST /security/v1/oauth/token`

Headers:
```
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}
```

Body:
```
grant_type=client_credentials
```

Response:
```json
{
  "token_type": "Bearer",
  "issued_at": "1708430400000",
  "client_id": "...",
  "access_token": "eyJ...",
  "expires_in": "14399",
  "status": "approved"
}
```

All subsequent requests require:
```
Authorization: Bearer {access_token}
```

Token caching is critical — UPS limits to ~250 token requests per day.

## Endpoints

### Create Shipment
`POST /api/shipments/v2205/ship`

Request body (ShipmentRequest):
```json
{
  "ShipmentRequest": {
    "Request": {
      "SubVersion": "2205",
      "RequestOption": "nonvalidate",
      "TransactionReference": {"CustomerContext": "ORDER-123"}
    },
    "Shipment": {
      "Description": "Order shipment",
      "Shipper": {
        "Name": "Sender Company",
        "ShipperNumber": "ABC123",
        "Address": {
          "AddressLine": ["ul. Testowa 1"],
          "City": "Warszawa",
          "PostalCode": "00-001",
          "CountryCode": "PL"
        },
        "Phone": {"Number": "500100200"}
      },
      "ShipTo": {
        "Name": "Receiver Name",
        "Address": {
          "AddressLine": ["ul. Odbiorcza 5"],
          "City": "Kraków",
          "PostalCode": "30-001",
          "CountryCode": "PL"
        },
        "Phone": {"Number": "500200300"},
        "EMailAddress": "receiver@test.pl"
      },
      "ShipFrom": {"...same structure as Shipper..."},
      "PaymentInformation": {
        "ShipmentCharge": [{
          "Type": "01",
          "BillShipper": {"AccountNumber": "ABC123"}
        }]
      },
      "Service": {"Code": "11", "Description": "UPS Standard"},
      "Package": [{
        "PackagingType": {"Code": "02", "Description": "Customer Supplied Package"},
        "Dimensions": {
          "UnitOfMeasurement": {"Code": "CM"},
          "Length": "30",
          "Width": "20",
          "Height": "15"
        },
        "PackageWeight": {
          "UnitOfMeasurement": {"Code": "KGS"},
          "Weight": "5.0"
        }
      }],
      "ShipmentServiceOptions": {}
    },
    "LabelSpecification": {
      "LabelImageFormat": {"Code": "GIF"},
      "LabelStockSize": {"Height": "6", "Width": "4"}
    }
  }
}
```

Response (ShipmentResponse):
```json
{
  "ShipmentResponse": {
    "Response": {"ResponseStatus": {"Code": "1", "Description": "Success"}},
    "ShipmentResults": {
      "ShipmentIdentificationNumber": "1Z999AA10123456784",
      "ShipmentCharges": {
        "TotalCharges": {"CurrencyCode": "PLN", "MonetaryValue": "45.00"}
      },
      "PackageResults": [{
        "TrackingNumber": "1Z999AA10123456784",
        "ShippingLabel": {
          "ImageFormat": {"Code": "GIF"},
          "GraphicImage": "R0lGODlh..."
        }
      }]
    }
  }
}
```

Label handling: The `GraphicImage` field contains a base64-encoded GIF that requires 270-degree rotation before printing. Convert the rotated GIF to PDF for standard label workflows.

### Void Shipment
`DELETE /api/shipments/v2205/void/cancel/{shipmentIdentificationNumber}`

Response confirms cancellation with status code.

### Track Shipment
`GET /api/track/v1/details/{inquiryNumber}`

Query parameters:
- `locale` (string) — Response language (e.g., `en_US`, `pl_PL`)
- `returnSignature` (bool) — Include proof of delivery signature

Response:
```json
{
  "trackResponse": {
    "shipment": [{
      "package": [{
        "trackingNumber": "1Z999AA10123456784",
        "activity": [{
          "date": "20260220",
          "time": "143000",
          "location": {"address": {"city": "Warszawa", "country": "PL"}},
          "status": {
            "type": "D",
            "description": "DELIVERED",
            "code": "KB"
          }
        }],
        "currentStatus": {"description": "DELIVERED", "code": "011"}
      }]
    }]
  }
}
```

### Recover Label
`POST /api/labels/v2205/recovery`

Retrieves a previously generated label by tracking number.

Request body:
```json
{
  "LabelRecoveryRequest": {
    "LabelSpecification": {
      "LabelImageFormat": {"Code": "GIF"},
      "LabelStockSize": {"Height": "6", "Width": "4"}
    },
    "TrackingNumber": "1Z999AA10123456784"
  }
}
```

### Rate / Price Estimate
`POST /api/rating/v2205/rate`

Returns estimated cost for a shipment before creation.

### Address Validation
`GET /api/addressvalidation/v1/1?RegionalRequestIndicator=string&MaximumListSize=10`

Query parameters include address fields for validation.

## Structures

### ShipmentCharge
- `Type` (string) — `01` (Transportation), `02` (Duties and Taxes)
- `BillShipper` — Bill to shipper account
- `BillReceiver` — Bill to receiver account
- `BillThirdParty` — Bill to third-party account

### ShipmentServiceOptions
Optional services added to shipment:
- `COD` — Cash on delivery
  - `CODFundsCode` (string) — `0` (check/money order), `8` (cashier's check)
  - `CODAmount` — `CurrencyCode` + `MonetaryValue`
- `InsuredValue` — Declared value coverage
  - `CurrencyCode` (string) — ISO currency code
  - `MonetaryValue` (string) — Insured amount
- `Notification` — Email/SMS notifications
  - `NotificationCode` (string) — `6` (ship), `7` (exception), `8` (delivery)
  - `EMail` — `EMailAddress` array, `UndeliverableEMailAddress`
- `InternationalForms` — Commercial invoice, certificate of origin
  - `FormType` (string) — `01` (invoice), `03` (CO), `04` (NAFTA CO)
  - `Product` array — Line items with description, value, origin country
  - `Contacts`, `SoldTo` — Party information

### Package Types
- `01` — UPS Letter
- `02` — Customer Supplied Package
- `03` — Tube
- `04` — PAK
- `21` — UPS Express Box (Small)
- `24` — UPS 25KG Box
- `25` — UPS 10KG Box
- `30` — Pallet

## Error Handling
UPS returns structured error responses:
```json
{
  "response": {
    "errors": [{
      "code": "120100",
      "message": "Missing or invalid shipper number"
    }]
  }
}
```

Common error codes:
- `120100` — Missing or invalid shipper number
- `120124` — Invalid postal code
- `120500` — Ship-to country invalid
- `120802` — Package weight exceeds maximum
- `250001` — Invalid tracking number
- `250002` — No tracking information available
- `401` — Unauthorized (expired or invalid token)
- `429` — Rate limit exceeded
