# Poczta Polska — API Reference

## Service Overview

Poczta Polska exposes **two independent SOAP services** with different authentication mechanisms:

| Service | Purpose | Authentication |
|---------|---------|---------------|
| Tracking (Sledzenie) | Shipment status lookup | WSSE UsernameToken |
| Posting (eNadawca) | Shipment creation, labels, courier orders | HTTP Basic Auth |

---

## Service 1: Tracking (Sledzenie)

### Connection Details

| Property | Value |
|----------|-------|
| WSDL URL | `https://tt.poczta-polska.pl/Sledzenie/services/Sledzenie?wsdl` |
| Protocol | SOAP 1.1 with WS-Security |

### Authentication

WSSE UsernameToken passed in the SOAP header:

```xml
<wsse:Security>
  <wsse:UsernameToken>
    <wsse:Username>YOUR_USERNAME</wsse:Username>
    <wsse:Password>YOUR_PASSWORD</wsse:Password>
  </wsse:UsernameToken>
</wsse:Security>
```

### sprawdzPrzesylke

Checks the current status and tracking history of a shipment.

**Request parameters:**

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `numer`   | string | Yes      | Shipment tracking number |

**Response:**

| Field               | Type          | Description |
|--------------------|---------------|-------------|
| `status`           | string        | Current shipment status |
| `numer`            | string        | Tracking number |
| `danePrzesylki`    | ShipmentInfo  | Shipment metadata |
| `zdarzenia`        | Event[]       | List of tracking events |

**Event structure:**

| Field     | Type     | Description |
|----------|----------|-------------|
| `czas`   | datetime | Event timestamp |
| `nazwa`  | string   | Event description |
| `kod`    | string   | Status code |
| `jednostka` | string | Handling unit / office |

---

## Service 2: Posting (eNadawca)

### Connection Details

| Property | Value |
|----------|-------|
| Endpoint (Legacy) | `https://e-nadawca.poczta-polska.pl` |
| Endpoint (New, 2025+) | `https://e-nadawca.api.poczta-polska.pl/websrv/` |
| Protocol | SOAP 1.1 with HTTP Basic Auth |

### Authentication

Standard HTTP Basic Authentication header:

```
Authorization: Basic base64(username:password)
```

---

### Shipment Creation Flow

The eNadawca API requires a multi-step process to create and dispatch shipments:

```
clearEnvelope
  │
  ▼
addShipment  ──(repeat for each parcel)──┐
  │                                       │
  ▼                                       │
zamowKuriera  ◀───────────────────────────┘
  │
  ▼
sendEnvelope
  │
  ▼
getPrintForParcel  (label retrieval)
```

### clearEnvelope

Prepares a clean posting envelope for a new batch of shipments.

**Request parameters:**

| Parameter     | Type   | Required | Description |
|--------------|--------|----------|-------------|
| `idEnvelope` | int    | No       | Existing envelope ID to clear (creates new if omitted) |

**Response:**

| Field          | Type | Description |
|---------------|------|-------------|
| `idEnvelope`  | int  | Envelope ID for subsequent operations |

### addShipment

Adds a shipment to the current envelope. Each shipment receives a GUID for identification.

**Request parameters:**

| Parameter      | Type         | Required | Description |
|---------------|--------------|----------|-------------|
| `idEnvelope`  | int          | Yes      | Envelope ID from `clearEnvelope` |
| `przesylka`   | Shipment     | Yes      | Shipment data structure |

**Shipment structure (Pocztex 2021 format):**

| Field         | Type         | Required | Description |
|--------------|--------------|----------|-------------|
| `adresNadawcy` | Address    | Yes      | Sender address |
| `adresOdbiorcy` | Address   | Yes      | Receiver address |
| `masa`       | int          | Yes      | Weight in grams |
| `wartosc`    | int          | No       | Declared value in grosze (1/100 PLN) |
| `pobranie`   | Pobranie     | No       | COD details |
| `ubezpieczenie` | int       | No       | Insurance value in grosze |
| `format`     | string       | Yes      | Parcel format: `S`, `M`, `L`, `XL`, `2XL` |
| `opis`       | string       | No       | Content description |
| `numerNadania` | string     | No       | Custom dispatch number |

**Address structure:**

| Field          | Type   | Description |
|---------------|--------|-------------|
| `nazwa`       | string | Name (person or company) |
| `nazwa2`      | string | Additional name line |
| `ulica`       | string | Street name |
| `numerDomu`   | string | Building number |
| `numerLokalu` | string | Apartment/unit number |
| `miejscowosc` | string | City |
| `kodPocztowy` | string | Postal code (XX-XXX format) |
| `telefon`     | string | Phone number |
| `email`       | string | Email address |

**Pobranie (COD) structure:**

| Field               | Type   | Description |
|--------------------|--------|-------------|
| `kwotaPobrania`    | int    | COD amount in grosze |
| `rachunekBankowy`  | string | Bank account number for COD transfer |
| `tytulemPobrania`  | string | COD transfer title |

**Format detection (based on dimensions):**

| Format | Max dimensions (L x W x H) |
|--------|----------------------------|
| S      | Smallest tier |
| M      | Medium tier |
| L      | Large tier |
| XL     | Extra large tier |
| 2XL    | Largest tier |

Exact thresholds are defined by Poczta Polska's current Pocztex 2021 pricing tables.

**Response:**

| Field    | Type   | Description |
|---------|--------|-------------|
| `guid`  | string | Unique shipment identifier (GUID) |
| `status` | string | Creation status |
| `numerNadania` | string | Assigned dispatch number |

### zamowKuriera

Schedules a courier pickup for shipments in the envelope.

**Request parameters:**

| Parameter         | Type     | Required | Description |
|------------------|----------|----------|-------------|
| `adresMiejscaOdbioru` | Address | Yes  | Pickup location address |
| `dataOdbioru`    | date     | Yes      | Requested pickup date |
| `godzinaOd`      | time     | No       | Earliest pickup time |
| `godzinaDo`      | time     | No       | Latest pickup time |

**Response:**

| Field              | Type   | Description |
|-------------------|--------|-------------|
| `numerZamowienia` | string | Courier order number |
| `status`          | string | Order status |

### sendEnvelope

Finalizes and submits the posting envelope, locking all contained shipments for dispatch.

**Request parameters:**

| Parameter     | Type   | Required | Description |
|--------------|--------|----------|-------------|
| `idEnvelope` | int    | Yes      | Envelope ID to submit |

**Response:**

| Field    | Type   | Description |
|---------|--------|-------------|
| `status` | string | Submission status |

---

### Label Operations

### getPrintForParcel

Retrieves the shipping label for a specific parcel.

**Request parameters:**

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `guid`    | string | Yes      | Shipment GUID from `addShipment` |
| `format`  | string | No       | Output format (default `PDF`) |

**Response:**

| Field     | Type   | Description |
|----------|--------|-------------|
| `plik`   | base64 | Label file content (base64-encoded PDF) |
| `format` | string | File format |

---

### Postal Office Lookup

### getPlacowkiPocztowe

Retrieves a list of postal offices, optionally filtered by location.

**Request parameters:**

| Parameter       | Type   | Required | Description |
|----------------|--------|----------|-------------|
| `kodPocztowy`  | string | No       | Filter by postal code |
| `miejscowosc`  | string | No       | Filter by city name |

**Response:**

| Field         | Type           | Description |
|--------------|----------------|-------------|
| `placowki`   | PostOffice[]   | List of matching postal offices |

**PostOffice structure:**

| Field            | Type   | Description |
|-----------------|--------|-------------|
| `pni`           | string | Postal office identifier (PNI) |
| `nazwa`         | string | Office name |
| `adres`         | Address | Office address |
| `godzinyOtwarcia` | string | Opening hours |
| `typ`           | string | Office type |

---

## Error Handling

Both services return SOAP faults for invalid requests.

**Tracking service errors:**

| Scenario | Description |
|----------|-------------|
| Invalid tracking number | Number format not recognized or shipment not found |
| Authentication failure | WSSE token rejected — verify username/password |

**eNadawca service errors:**

| Scenario | Description |
|----------|-------------|
| Invalid credentials | HTTP 401 — verify Basic Auth username/password |
| Missing required field | Validation error with field name in fault detail |
| Invalid format | Parcel format not matching allowed values |
| Envelope not found | Specified envelope ID does not exist |
| GUID not found | Shipment GUID not found for label retrieval |
| Envelope already sent | Cannot modify an already submitted envelope |

---

## Complete Shipment Flow

```
[Tracking Service - WSSE Auth]
sprawdzPrzesylke ──▶ Tracking status + event history

[eNadawca Service - HTTP Basic Auth]
clearEnvelope
  │
  ▼
addShipment (parcel 1) ──▶ GUID
addShipment (parcel 2) ──▶ GUID
  │
  ▼
zamowKuriera ──▶ Courier order number
  │
  ▼
sendEnvelope ──▶ Finalized
  │
  ▼
getPrintForParcel(guid) ──▶ Label PDF
  │
  ▼
getPlacowkiPocztowe ──▶ Postal office list (optional)
```
