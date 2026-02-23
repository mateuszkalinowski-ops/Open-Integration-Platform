# GLS ADE Plus — API Reference

## Connection Details

| Environment | WSDL URL |
|-------------|----------|
| Production  | `https://adeplus.gls-poland.com/adeplus/pm1/ade_webapi2.php?wsdl` |
| Sandbox     | `https://ade-test.gls-poland.com/adeplus/pm1/ade_webapi2.php?wsdl` |

**Protocol**: SOAP 1.1 / WSDL

---

## Authentication

GLS ADE Plus uses session-based authentication. A session must be opened before any operation and closed after.

### adeLogin

Opens a new session.

**Request parameters:**

| Parameter    | Type   | Required | Description                |
|-------------|--------|----------|----------------------------|
| `user_name` | string | Yes      | ADE Plus account username  |
| `user_password` | string | Yes  | ADE Plus account password  |

**Response:**

| Field       | Type   | Description              |
|-------------|--------|--------------------------|
| `session`   | string | Session ID for subsequent calls |

### adeLogout

Closes an active session.

**Request parameters:**

| Parameter | Type   | Required | Description     |
|-----------|--------|----------|-----------------|
| `session` | string | Yes      | Active session ID |

**Response:** Confirmation of session closure.

---

## Shipment Operations

### adePreparingBox_Insert

Creates a new parcel (box) record in the GLS system prior to pickup scheduling.

**Request parameters:**

| Parameter        | Type           | Required | Description |
|-----------------|----------------|----------|-------------|
| `session`       | string         | Yes      | Active session ID |
| `consign_prep_data` | ConsignPrepData | Yes  | Parcel details structure |

**ConsignPrepData structure:**

| Field            | Type    | Description |
|-----------------|---------|-------------|
| `rname1`        | string  | Receiver name (line 1) |
| `rname2`        | string  | Receiver name (line 2) |
| `rname3`        | string  | Receiver contact person |
| `rcountry`      | string  | Receiver country code (ISO 3166-1 alpha-2) |
| `rzipcode`      | string  | Receiver postal code |
| `rcity`         | string  | Receiver city |
| `rstreet`       | string  | Receiver street |
| `rphone`        | string  | Receiver phone number |
| `remail`        | string  | Receiver email |
| `references`    | string  | Shipment reference |
| `notes`         | string  | Notes for driver |
| `weight`        | float   | Weight in kg |
| `srv_bool`      | SrvBool | Service flags structure |

**SrvBool (service flags):**

| Field   | Type    | Description |
|---------|---------|-------------|
| `cod`   | boolean | Cash on Delivery |
| `cod_amount` | float | COD amount (when `cod` = true) |
| `rod`   | boolean | Return on Delivery |
| `daw`   | boolean | Delivery at Work |
| `pr`    | boolean | Parcel Return |
| `s10`   | boolean | Delivery before 10:00 |
| `s12`   | boolean | Delivery before 12:00 |
| `sat`   | boolean | Saturday delivery |
| `srs`   | boolean | Saturday Return Service |
| `sds`   | boolean | Same Day Service |
| `exc`   | boolean | Exchange Service |
| `ppe`   | boolean | Pick & Pack & Export |

**Response:**

| Field        | Type   | Description |
|-------------|--------|-------------|
| `id`        | int    | Internal parcel ID |
| `number`    | string | GLS parcel number |

---

## Pickup Operations

### adePickup_Create

Creates a pickup order for one or more previously inserted parcels.

**Request parameters:**

| Parameter    | Type      | Required | Description |
|-------------|-----------|----------|-------------|
| `session`   | string    | Yes      | Active session ID |
| `id_start`  | int       | Yes      | First parcel ID in range |
| `id_end`    | int       | Yes      | Last parcel ID in range |
| `desc`      | string    | No       | Pickup description |

**Response:**

| Field        | Type   | Description |
|-------------|--------|-------------|
| `pickup_id` | int    | Created pickup ID |

### adePickup_GetConsign

Retrieves the consignment document (PDF) for a pickup.

**Request parameters:**

| Parameter    | Type   | Required | Description |
|-------------|--------|----------|-------------|
| `session`   | string | Yes      | Active session ID |
| `pickup_id` | int    | Yes      | Pickup ID |

**Response:**

| Field   | Type   | Description |
|---------|--------|-------------|
| `pdf`   | base64 | Consignment document in PDF format (base64-encoded) |

---

## Label Operations

### adePickup_GetParcelLabel

Retrieves a shipping label for a single parcel.

**Request parameters:**

| Parameter    | Type   | Required | Description |
|-------------|--------|----------|-------------|
| `session`   | string | Yes      | Active session ID |
| `parcel_id` | int    | Yes      | Parcel ID |

**Response:**

| Field   | Type   | Description |
|---------|--------|-------------|
| `pdf`   | base64 | Shipping label in PDF format (base64-encoded) |

### adePickup_GetParcelsLabels

Retrieves shipping labels for multiple parcels in a single PDF document.

**Request parameters:**

| Parameter    | Type   | Required | Description |
|-------------|--------|----------|-------------|
| `session`   | string | Yes      | Active session ID |
| `parcel_ids` | int[] | Yes      | Array of parcel IDs |

**Response:**

| Field   | Type   | Description |
|---------|--------|-------------|
| `pdf`   | base64 | Combined shipping labels in PDF format (base64-encoded) |

---

## Tracking

### adeTrackID_Get

Retrieves tracking history for a parcel.

**Request parameters:**

| Parameter    | Type   | Required | Description |
|-------------|--------|----------|-------------|
| `session`   | string | Yes      | Active session ID |
| `parcel_id` | int    | Yes      | Parcel ID or GLS tracking number |

**Response:**

| Field     | Type          | Description |
|-----------|---------------|-------------|
| `history` | TrackEvent[]  | Array of tracking events |

**TrackEvent structure:**

| Field       | Type     | Description |
|------------|----------|-------------|
| `date`     | datetime | Event timestamp |
| `code`     | string   | Status code |
| `desc`     | string   | Status description |
| `depot`    | string   | Depot/location information |

---

## Error Handling

SOAP faults are returned for invalid requests. Common error scenarios:

| Scenario | Fault Code | Description |
|----------|-----------|-------------|
| Invalid session | `SessionExpired` | Session has expired or is invalid — re-authenticate |
| Missing required field | `ValidationError` | Required parcel data field is missing |
| Invalid credentials | `AuthenticationError` | Username or password is incorrect |
| Parcel not found | `NotFound` | Specified parcel ID does not exist |

---

## Shipment Flow Summary

```
adeLogin
  │
  ▼
adePreparingBox_Insert  ──(repeat for each parcel)──┐
  │                                                   │
  ▼                                                   │
adePickup_Create  ◀───────────────────────────────────┘
  │
  ├──▶ adePickup_GetConsign       (consignment PDF)
  ├──▶ adePickup_GetParcelLabel   (single label)
  ├──▶ adePickup_GetParcelsLabels (batch labels)
  │
  ▼
adeTrackID_Get  (tracking)
  │
  ▼
adeLogout
```
