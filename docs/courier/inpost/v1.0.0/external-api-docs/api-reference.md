# InPost ShipX API v1 — API Reference

Source: https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/18153476

## Base URLs
- Production: https://api-shipx-pl.easypack24.net/
- Sandbox: https://sandbox-api-shipx-pl.easypack24.net/

## Authentication
All requests require Bearer token:
```
Authorization: Bearer {api_token}
```

## Endpoints

### Create Shipment
`POST /v1/organizations/{org_id}/shipments`

Request body:
```json
{
  "service": "inpost_locker_standard",
  "custom_attributes": {"target_point": "KRA01A", "sending_method": "dispatch_order"},
  "parcels": [{"dimensions": {"height": 100, "length": 200, "width": 150, "unit": "mm"}, "weight": {"amount": 5, "unit": "kg"}}],
  "receiver": {"address": {"building_number": "1", "city": "Kraków", "country_code": "PL", "post_code": "30-001", "street": "ul. Testowa"}, "email": "test@test.pl", "first_name": "Jan", "last_name": "Kowalski", "phone": "500100200"},
  "sender": {"...same structure..."},
  "reference": "ORDER-123",
  "cod": {"amount": 100.00, "currency": "PLN"},
  "insurance": {"amount": 500.00, "currency": "PLN"}
}
```

Response: Shipment object with `id`, `status`, `tracking_number`

### Get Shipment
`GET /v1/organizations/{org_id}/shipments?tracking_number={waybill}`

### Get Labels
`GET /v1/organizations/{org_id}/shipments/labels?shipment_ids[]={id}&type=A6`

Returns PDF bytes.

### Delete Shipment
`DELETE /v1/shipments/{order_id}`

### Track Shipment
`GET /v1/tracking/{waybill_number}`

### Get Points
`GET /v1/points?city={city}&post_code={code}`

Returns list of InPost locker/point locations with coordinates.

## Label Formats
- PDF: A4, A6
- ZPL: 203dpi, 300dpi
- EPL2

## Status Flow
created → offers_prepared → offer_selected → confirmed → dispatched_by_sender → collected_from_sender → taken_by_courier → adopted_at_source_branch → sent_from_source_branch → adopted_at_sorting_center → sent_from_sorting_center → adopted_at_target_branch → out_for_delivery → ready_to_pickup → delivered → returned_to_sender
