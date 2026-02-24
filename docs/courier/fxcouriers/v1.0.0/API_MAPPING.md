# FX Couriers — API Mapping

## Order Creation: Platform -> FX Couriers

| Platform Field | FX Couriers Field | Notes |
|---|---|---|
| `company_id` | `company_id` | Direct mapping |
| `service_code` | `service_code` | e.g., "STANDARD" |
| `payment_method` | `payment_method` | CASH / TRANSFER |
| `comment` | `comment` | Free text |
| `sender.name` | `sender.name` | Sender company/person name |
| `sender.country_code` | `sender.country` | ISO 2-letter code |
| `sender.city` | `sender.city` | |
| `sender.postal_code` | `sender.postal_code` | Format: XX-XXX |
| `sender.street` | `sender.street` | |
| `sender.building_number` | `sender.house_number` | |
| `sender.apartment_number` | `sender.apartment_number` | Optional |
| `sender.contact_person` | `sender.contact_person` | |
| `sender.phone` | `sender.contact_phone` | |
| `sender.email` | `sender.contact_email` | |
| `receiver.name` | `recipient.name` | Recipient company/person name |
| `receiver.country_code` | `recipient.country` | ISO 2-letter code |
| `receiver.city` | `recipient.city` | |
| `receiver.postal_code` | `recipient.postal_code` | Format: XX-XXX |
| `receiver.street` | `recipient.street` | |
| `receiver.building_number` | `recipient.house_number` | |
| `receiver.apartment_number` | `recipient.apartment_number` | Optional |
| `receiver.contact_person` | `recipient.contact_person` | |
| `receiver.phone` | `recipient.contact_phone` | |
| `receiver.email` | `recipient.contact_email` | |
| `parcels[].content` | `items[].content` | Package content description |
| `parcels[].parcel_type` | `items[].package_type` | Default: "BOX" |
| `parcels[].quantity` | `items[].quantity` | |
| `parcels[].weight` | `items[].weight` | In kg |
| `parcels[].width` | `items[].width` | In cm |
| `parcels[].height` | `items[].height` | In cm |
| `parcels[].length` | `items[].length` | In cm |
| `parcels[].comment` | `items[].comment` | Per-item comment |

## Additional Services

| Service Code | Name | Description |
|---|---|---|
| `OPLATA_PALIWOWA` | Fuel surcharge | Automatic, scope: Order |
| `POBRANIE` | Cash on delivery | COD payment collection |
| `UBEZPIECZENIE` | Insurance | Package insurance, value in PLN |

## Order Status Mapping

| FX Couriers Status | Platform Status | Description |
|---|---|---|
| `NEW` | `CREATED` | Order just created |
| `WAITING_APPROVAL` | `CREATED` | Awaiting carrier approval |
| `ACCEPTED` | `CONFIRMED` | Accepted by carrier |
| `RUNNING` | `IN_TRANSIT` | In transit |
| `PICKUP` | `PICKED_UP` | Picked up from sender |
| `CLOSED` | `DELIVERED` | Delivered successfully |
| `RETURN` | `RETURNED` | Returned to sender |
| `PROBLEM` | `FAILED` | Delivery problem |
| `FAILED` | `FAILED` | Delivery failed |
| `CANCELLED` | `CANCELLED` | Order cancelled |

## Pickup (Shipment) Request Mapping

| Platform Field | FX Couriers Field | Notes |
|---|---|---|
| `pickup_date` | `pickup_date` | Format: YYYY-MM-DD |
| `pickup_time_from` | `pickup_time_from` | Format: HH:MM |
| `pickup_time_to` | `pickup_time_to` | Format: HH:MM |
| `order_ids` | `order_id_list` | Array of order IDs to pick up |
