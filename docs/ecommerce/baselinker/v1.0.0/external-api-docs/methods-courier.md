# BaseLinker API — Courier Shipment Methods (Detailed)

> Source: https://api.baselinker.com/
> Fetched: 2026-02-24

---

## createPackageManual

Manually add a shipping number and courier name to an order. Used for shipments
created outside BaseLinker.

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `order_id` | int | Yes | Order ID |
| `courier_code` | varchar(20) | Yes | Courier code (from `getCouriersList`) or custom name |
| `package_number` | varchar(40) | Yes | Shipping/consignment number |
| `pickup_date` | int | No | Dispatch date (unix timestamp) |
| `return_shipment` | bool | No | Mark as return shipment (default: false) |

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | varchar(30) | "SUCCESS" or "ERROR" |
| `package_id` | int | Created shipment ID |
| `package_number` | varchar(40) | Shipping number |

### Sample

```json
// Input
{
  "order_id": 6910995,
  "courier_code": "dhl",
  "package_number": "622222044730624327700197",
  "pickup_date": "1487006161",
  "return_shipment": true
}

// Output
{
  "status": "SUCCESS",
  "package_id": 77014697,
  "package_number": "622222044730624327700198"
}
```

---

## createPackage

Create a shipment in the system of the selected courier (full courier API integration).

> This method's parameters depend on the courier. Use `getCourierFields` to retrieve
> the form fields for each courier.

---

## getCouriersList

Retrieve list of available couriers.

---

## getCourierFields

Retrieve form fields for creating shipments for a selected courier.

---

## getCourierServices

Retrieve additional courier services (used for X-press, BrokerSystem, Wysyłam z Allegro,
ErliPRO couriers).

---

## getCourierAccounts

Retrieve list of accounts connected to a given courier.

---

## getLabel

Download shipping label (consignment) for a selected shipment.

---

## getProtocol

Download parcel protocol for selected shipments.

---

## getCourierDocument

Download a parcel document.

---

## getOrderPackages

Download shipments previously created for a selected order.

---

## getPackageDetails

Get detailed information about a package, including subpackages.

---

## getCourierPackagesStatusHistory

Retrieve status history for shipments. Max 100 shipments per call.

---

## deleteCourierPackage

Delete a previously created shipment (from BaseLinker and courier system if API allows).

---

## runRequestParcelPickup

Request parcel pickup for previously created shipments.

---

## getRequestParcelPickupFields

Retrieve additional fields for a parcel pickup request.
