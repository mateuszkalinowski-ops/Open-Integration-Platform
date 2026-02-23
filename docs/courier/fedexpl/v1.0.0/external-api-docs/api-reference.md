# FedEx PL (IKL Service) — API Reference

## Connection Details

| Property   | Value |
|-----------|-------|
| WSDL URL  | `https://poland.fedex.com/fdsWs/IklServicePort?wsdl` |
| Endpoint  | `https://poland.fedex.com/fdsWs/IklServicePort` |
| Protocol  | SOAP 1.1 / WSDL |

---

## Authentication

Authentication credentials are embedded in each SOAP request — no session or token management required.

| Parameter            | Type   | Required | Description |
|---------------------|--------|----------|-------------|
| `accessCode`        | string | Yes      | API key issued by FedEx Poland |
| `senderId`          | string | Yes      | Client identifier |
| `courierId`         | string | Yes      | Courier number assigned to the client |
| `bankAccountNumber` | string | Conditional | Required when using COD; bank account for settlements |

---

## Shipment Operations

### zapiszListV2

Creates a new shipment and registers it in the FedEx Poland system.

**Request parameters:**

| Parameter    | Type       | Required | Description |
|-------------|------------|----------|-------------|
| `accessCode` | string    | Yes      | API key |
| `senderId`   | string    | Yes      | Client ID |
| `courierId`  | string    | Yes      | Courier number |
| `shipmentV2` | ShipmentV2 | Yes     | Full shipment data structure |

**ShipmentV2 structure:**

| Field             | Type              | Required | Description |
|------------------|-------------------|----------|-------------|
| `sender`         | AddressData       | Yes      | Sender address and contact |
| `receiver`       | AddressData       | Yes      | Receiver address and contact |
| `payer`          | PayerData         | Yes      | Payment responsibility |
| `parcels`        | ParcelData[]      | Yes      | List of parcels |
| `proofOfDispatch` | ProofOfDispatch  | No       | Proof of dispatch details |
| `cod`            | CodData           | No       | Cash on Delivery configuration |
| `insurance`      | InsuranceData     | No       | Insurance details |

**AddressData structure:**

| Field         | Type   | Description |
|--------------|--------|-------------|
| `name`       | string | Company or person name |
| `street`     | string | Street address |
| `city`       | string | City |
| `postCode`   | string | Postal code |
| `countryCode` | string | ISO country code (e.g. `PL`) |
| `phone`      | string | Phone number |
| `email`      | string | Email address |
| `contactPerson` | string | Contact person name |

**PayerData structure:**

| Field         | Type   | Description |
|--------------|--------|-------------|
| `payerType`  | string | `SENDER`, `RECEIVER`, or `THIRD_PARTY` |
| `accountNumber` | string | Payer account number (when third party) |

**ParcelData structure:**

| Field      | Type   | Description |
|-----------|--------|-------------|
| `weight`  | float  | Weight in kg |
| `length`  | int    | Length in cm |
| `width`   | int    | Width in cm |
| `height`  | int    | Height in cm |
| `reference` | string | Parcel reference |
| `content` | string | Content description |

**CodData structure:**

| Field               | Type   | Required | Description |
|--------------------|--------|----------|-------------|
| `codType`          | string | Yes      | COD type — use `B` for bank transfer |
| `codValue`         | float  | Yes      | Amount to collect on delivery |
| `bankAccountNumber` | string | Yes     | Bank account number for COD transfer |
| `currency`         | string | No       | Currency code (default `PLN`) |

**InsuranceData structure:**

| Field            | Type   | Description |
|-----------------|--------|-------------|
| `insuranceValue` | float  | Declared value for insurance |
| `currency`      | string | Currency code |

**ProofOfDispatch structure:**

| Field        | Type   | Description |
|-------------|--------|-------------|
| `type`      | string | Proof type |
| `reference` | string | Dispatch reference |

**Response:**

| Field            | Type   | Description |
|-----------------|--------|-------------|
| `shipmentId`    | string | FedEx Poland shipment identifier |
| `waybillNumber` | string | Waybill / tracking number |
| `status`        | string | Creation status |

---

## Label Operations

### wydrukujEtykiete

Retrieves a shipping label for a created shipment.

**Request parameters:**

| Parameter      | Type   | Required | Description |
|---------------|--------|----------|-------------|
| `accessCode`  | string | Yes      | API key |
| `senderId`    | string | Yes      | Client ID |
| `shipmentId`  | string | Yes      | Shipment ID returned by `zapiszListV2` |
| `labelFormat` | string | No       | Label format — `PDF` (default) |

**Response:**

| Field     | Type   | Description |
|----------|--------|-------------|
| `label`  | base64 | Shipping label in PDF format (base64-encoded) |
| `format` | string | Label format (e.g. `PDF`) |

---

## Error Handling

SOAP faults are returned for invalid requests. Common error scenarios:

| Scenario | Description |
|----------|-------------|
| Invalid `accessCode` | Authentication failure — verify API key |
| Missing receiver address fields | Validation error — all required address fields must be provided |
| Invalid `codType` | Only supported COD types are accepted (use `B` for bank transfer) |
| Invalid parcel dimensions | Weight/dimensions out of allowed range |
| Shipment not found | `shipmentId` does not exist for label retrieval |

---

## Shipment Flow Summary

```
zapiszListV2
  │
  ├──▶ Shipment created (shipmentId + waybillNumber)
  │
  ▼
wydrukujEtykiete
  │
  ├──▶ Label PDF returned
  │
  ▼
(Courier picks up parcel)
```
