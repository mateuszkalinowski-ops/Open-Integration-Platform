# DHL24 WebAPI v2 — API Reference

Source: https://dhl24.com.pl/en/webapi2/doc.html

## WSDL
- Production: https://dhl24.com.pl/webapi2 (v4.20.58)
- Sandbox: https://sandbox.dhl24.com.pl/webapi2

## Structures

### AuthData
Authorization structure required in every request:
- `username` (string) — Login
- `password` (string) — Password

### Address
- `name` (string) — Recipient name
- `postalCode` (string) — Postal code
- `city` (string) — City
- `street` (string) — Street
- `houseNumber` (string) — Building number
- `apartmentNumber` (string, optional) — Apartment number
- `contactPerson` (string) — Contact person name
- `contactPhone` (string) — Phone number
- `contactEmail` (string) — Email address

### PieceDefinition
- `type` (string) — Package type: PACKAGE, ENVELOPE, PALETTE
- `width` (int) — Width in cm
- `height` (int) — Height in cm
- `length` (int) — Length in cm
- `weight` (float) — Weight in kg
- `quantity` (int) — Number of parcels
- `nonStandard` (bool) — Non-standard flag

### ServiceDefinition
- `product` (string) — DHL product type (AH, PR, DZ, DW, etc.)
- `deliveryToNeighbour` (bool)
- `deliveryOnSaturday` (bool)
- `pickUpOnSaturday` (bool)
- `collectOnDelivery` (bool) — COD
- `collectOnDeliveryValue` (decimal)
- `collectOnDeliveryForm` (string) — CASH/BANK_TRANSFER
- `collectOnDeliveryReference` (string)
- `insurance` (bool)
- `insuranceValue` (decimal)
- `selfCollect` (bool) — Pickup at DHL point
- `deliveryEvening` (bool)
- `deliveryToLM` (bool)
- `returnOnDelivery` (bool)
- `proofOfDelivery` (bool)
- `predeliveryInformation` (bool)

### PaymentData
- `paymentMethod` (string) — BANK_TRANSFER/CASH
- `payerType` (string) — SHIPPER/RECEIVER/USER
- `accountNumber` (string) — DHL account number

## Methods

### createShipments
Creates 1-3 shipments.
- **Input**: AuthData + array of ShipmentFullData
- **Output**: Array of ShipmentBasicData (waybill number, label data)

### bookCourier
Books courier pickup for created shipments.
- **Input**: AuthData, pickupDate, pickupTimeFrom, pickupTimeTo, additionalInfo, shipmentIdList

### deleteShipments
Deletes shipments by waybill numbers.

### getLabels
Retrieves labels for shipments.
- **Input**: AuthData + ItemToPrint array (shipmentId, labelType)
- **labelType**: BLP (label), ZBLP (return label)
- **Output**: PDF bytes

### getTrackAndTraceInfo
Gets tracking events for a shipment.
- **Input**: AuthData, shipmentId

### getNearestServicepoints
Finds DHL service/pickup points.
- **Input**: AuthData, postcode, city, paymentPointsOnly

### getPostalCodeServices
Checks available services for a postal code.

### getReturnParams
Gets return shipment parameters.

### cancelCourierBooking
Cancels a courier booking.

### getMyShipments
Retrieves shipments list with filtering options.
