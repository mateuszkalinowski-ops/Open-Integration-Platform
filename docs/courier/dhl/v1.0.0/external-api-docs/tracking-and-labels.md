# DHL24 WebAPI v2 — Tracking & Labels

> Source: https://dhl24.com.pl/en/webapi2/doc.html
> Fetched: 2026-02-24

---

## getTrackAndTraceInfo

Downloads delivery process history and current shipment status.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `shipmentId` | string | Yes | Shipment ID (waybill number) |

### Output Parameters

| Field | Type | Description |
|-------|------|-------------|
| `shipmentId` | string | Shipment ID |
| `receivedBy` | string | Person who collected the parcel (if delivered) |
| `events` | array | Array of ShipmentEvent structures |

### ShipmentEvent Structure

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Event status description |
| `terminal` | string | Terminal/location name |
| `timestamp` | datetime | Event date and time |

### SOAP Request Example

```xml
<getTrackAndTraceInfo>
  <authData>
    <username>testuser</username>
    <password>testpass</password>
  </authData>
  <shipmentId>11122223333</shipmentId>
</getTrackAndTraceInfo>
```

### Tracking URL (no API call needed)

```
https://www.dhl.com/pl-en/home/tracking/tracking-parcel.html?submit=1&tracking-id={waybill_number}
```

---

## getLabels

Retrieves generated shipping labels for created shipments.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `itemsToPrint` | array | Yes | Array of items to print |

Each item in `itemsToPrint`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `shipmentId` | string | Yes | Shipment waybill number |
| `labelType` | string | Yes | Label format (see below) |

### Label Types

| Code | Description | Printer |
|------|-------------|---------|
| `LP` | Consignment note | — |
| `BLP` | BLP label (PDF) | Laser printer |
| `LBLP` | LBLP label (PDF A4) | Laser printer |
| `ZBLP` | BLP label (ZPL) | Zebra thermal |
| `ZBLP300` | BLP 300dpi (ZPL) | Zebra thermal |

### Output Parameters

Array of label objects:

| Field | Type | Description |
|-------|------|-------------|
| `shipmentId` | string | Shipment ID |
| `labelType` | string | Label type returned |
| `labelMimeType` | string | MIME type (e.g. `application/pdf`) |
| `labelData` | string | Label content encoded in base64 |

### Error Responses

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `100` | 401 | Authentication error |
| Other | 400 | Application error with message |
| null response | 200 | No data available |

### SOAP Request Example

```xml
<getLabels>
  <authData>
    <username>testuser</username>
    <password>testpass</password>
  </authData>
  <itemsToPrint>
    <item>
      <labelType>BLP</labelType>
      <shipmentId>11122223333</shipmentId>
    </item>
  </itemsToPrint>
</getLabels>
```

---

## getMyShipments / getMyShipmentsCount

Retrieves list of user's created shipments within a date range.

### getMyShipmentsCount — Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `createdFrom` | date | Yes | Start date |
| `createdTo` | date | Yes | End date |

**Output:** integer — total shipment count

### getMyShipments — Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `createdFrom` | date | Yes | Start date |
| `createdTo` | date | Yes | End date |
| `offset` | int | No | Pagination offset (100 items per page) |

**Output:** Array of shipment objects including:
- `shipmentId` — waybill number
- `orderStatus` — current status
- `created` — creation date
- Shipper/receiver address details
- Service information

**Note:** Maximum date range is 90 days. There is no direct lookup by waybill —
must paginate through results.

---

## bookCourier

Books courier pickup for already created shipments.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `pickupDate` | date | Yes | Pickup date |
| `pickupTimeFrom` | string | Yes | Start time (HH:MM) |
| `pickupTimeTo` | string | Yes | End time (HH:MM) |
| `additionalInfo` | string | No | Info for courier |
| `shipmentIdList` | array | Yes | List of shipment IDs |
| `courierWithLabel` | bool | No | Courier brings labels |

### Output

Array of dispatch notification numbers (order IDs).

---

## cancelCourierBooking

Cancels a previously booked courier pickup.

---

## deleteShipments

Cancels/deletes shipments.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization |
| `shipment` | object | Yes | Contains `shipmentIdentificationNumber` and `dispatchIdentificationNumber` |

### Output

| Field | Type | Description |
|-------|------|-------------|
| `result` | bool | Success flag |
| `error` | string | Error message (if failed) |
