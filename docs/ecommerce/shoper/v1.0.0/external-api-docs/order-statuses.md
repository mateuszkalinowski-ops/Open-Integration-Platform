# Shoper REST API — Order Statuses Reference

Source: https://developers.shoper.pl/, integration-rest-api/map/mappingFile.json
Fetched: 2026-02-22

## Default Order Statuses

Shoper uses numeric `status_id` values for order statuses. The default
statuses (may vary per store configuration):

| status_id | Name (PL)                    | Name (EN)               | Connector Mapping         |
|-----------|------------------------------|-------------------------|---------------------------|
| 1         | Tymczasowe                   | Temporary               | NEW (inactive)            |
| 2         | Nowe                         | New                     | NEW                       |
| 3         | W realizacji                 | In progress             | PROCESSING                |
| 4         | W realizacji (opłacone)      | In progress (paid)      | PROCESSING                |
| 5         | Wysłane                      | Shipped                 | PROCESSING                |
| 6         | Gotowe do odbioru            | Ready for pickup        | READY_FOR_SHIPMENT        |
| 7         | Zrealizowane                 | Completed               | DELIVERED                 |
| 8         | Anulowane                    | Cancelled               | CANCELLED                 |
| 9         | Zwrócone                     | Returned                | CANCELLED                 |
| 10        | Reklamacja                   | Complaint               | CANCELLED                 |
| 12        | Odrzucone                    | Rejected                | CANCELLED                 |

> **Note**: Stores can add custom statuses. The above are the defaults.
> Use `GET /webapi/rest/order-statuses` to fetch the current list for a
> specific store.

## Status Transition Flow

```
┌─────────────┐    ┌────────────────┐    ┌──────────────────┐
│ 1: Temporary │───►│ 2: New         │───►│ 3-5: In progress │
└─────────────┘    └────────────────┘    └──────────────────┘
                          │                       │
                          │                       ▼
                          │              ┌──────────────────┐
                          │              │ 6: Ready pickup  │
                          │              └──────────────────┘
                          │                       │
                          ▼                       ▼
                   ┌─────────────┐       ┌──────────────────┐
                   │ 8: Cancelled│       │ 7: Completed     │
                   └─────────────┘       └──────────────────┘
                          ▲                       │
                          │                       ▼
                   ┌─────────────┐       ┌──────────────────┐
                   │ 10: Claim   │       │ 9: Returned      │
                   └─────────────┘       └──────────────────┘
```

## Connector Status Mapping

### Shoper → Pinquark (inbound)

Used when importing orders from Shoper:

```python
SHOPER_STATUS_TO_ORDER = {
    "1": OrderStatus.NEW,
    "2": OrderStatus.NEW,
    "3": OrderStatus.PROCESSING,
    "4": OrderStatus.PROCESSING,
    "5": OrderStatus.PROCESSING,
    "6": OrderStatus.READY_FOR_SHIPMENT,
    "7": OrderStatus.DELIVERED,
    "8": OrderStatus.CANCELLED,
    "9": OrderStatus.CANCELLED,
    "10": OrderStatus.CANCELLED,
    "12": OrderStatus.CANCELLED,
}
```

### Pinquark → Shoper (outbound)

Used when updating order statuses from the platform back to Shoper:

```python
ORDER_STATUS_TO_SHOPER = {
    OrderStatus.NEW: "2",
    OrderStatus.PROCESSING: "4",
    OrderStatus.READY_FOR_SHIPMENT: "6",
    OrderStatus.SHIPPED: "7",
    OrderStatus.DELIVERED: "7",
    OrderStatus.CANCELLED: "8",
}
```

## ERP Status Mapping (from mappingFile.json)

The original Java integration included mappings between Shoper statuses
and ERP (WMS) statuses:

### Shoper → ERP

| Shoper status_id | ERP Translation          | Active |
|-------------------|--------------------------|--------|
| 1                 | DOKUMENT TYMCZASOWY      | No     |
| 2                 | NOWY                     | Yes    |
| 3                 | W TRAKCIE REALIZACJI     | Yes    |
| 4                 | W TRAKCIE REALIZACJI     | Yes    |
| 5                 | W TRAKCIE REALIZACJI     | Yes    |
| 6                 | W TRAKCIE REALIZACJI     | Yes    |
| 7                 | ZREALIZOWANY             | Yes    |
| 8                 | ANULOWANY                | Yes    |
| 9                 | ANULOWANY                | Yes    |
| 10                | ANULOWANY                | Yes    |
| 12                | ANULOWANY                | Yes    |

### ERP → Shoper

| ERP Status              | Shoper status_id | Active |
|-------------------------|-------------------|--------|
| NOWY                    | 2                 | Yes    |
| W TRAKCIE REALIZACJI    | 4                 | Yes    |
| ZREALIZOWANY            | 7                 | Yes    |
| ZAMKNIETY               | 7                 | Yes    |
| ZAMKNIETY RECZNIE       | 7                 | Yes    |
| ZAMKNIETY Z BRAKAMI     | 7                 | Yes    |
| ZAMKNIETY PRZEZ SYSTEM  | 8                 | Yes    |
| ZREALIZOWANY CZESCIOWO | 7                 | Yes    |
| ANULOWANY               | 8                 | Yes    |
| ROBOCZY                 | 1                 | No     |
| DOKUMENT TYMCZASOWY     | 1                 | No     |

> These mappings are the Layer 1 defaults. Per-tenant overrides can be
> configured via the platform dashboard (Layer 2 — database).

## Querying Statuses

To get the full list of statuses configured in a specific store:

```
GET /webapi/rest/order-statuses
```

Response:
```json
{
  "count": 12,
  "pages": 1,
  "page": 1,
  "list": [
    {
      "status_id": 1,
      "active": 0,
      "color": "#999999",
      "type": 0
    },
    {
      "status_id": 2,
      "active": 1,
      "color": "#00cc00",
      "type": 1
    }
  ]
}
```

### OrderStatus Properties

| Property    | Type    | Description                     |
|-------------|---------|----------------------------------|
| `status_id` | integer | Unique status ID                |
| `active`    | integer | Whether status is active (0/1)  |
| `color`     | string  | Hex color for UI display        |
| `type`      | integer | Status type category            |
