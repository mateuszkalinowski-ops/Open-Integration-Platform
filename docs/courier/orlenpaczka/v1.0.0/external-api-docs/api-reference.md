# Orlen Paczka (Paczka w Ruchu) — API Reference

Source: https://www.paczkawruchu.pl/integracje/

## Endpoint
- Production: https://api.orlenpaczka.pl/WebServicePwRProd/WebServicePwR.asmx

## Authentication
Every request requires:
- `PartnerID` (int) — Partner identifier
- `PartnerKey` (string) — Secret authentication key

## Methods

### GenerateBusinessPack
Creates a new shipment (business pack).
- **Input**: Sender data, receiver data, pickup point ID, parcel details, services (COD, insurance)
- **Output**: Pack number (waybill), label data, confirmation status
- **Notes**: Supports COD and insurance as optional services

### GiveMePackStatus
Retrieves current status of a shipment.
- **Input**: Pack number (waybill)
- **Output**: Current status code, status description, timestamp
- **Notes**: Returns the latest status event for the package

### PutCustomerPackCanceled
Cancels an existing shipment.
- **Input**: Pack number (waybill)
- **Output**: Cancellation confirmation
- **Notes**: Only packs not yet in transit can be cancelled

### LabelPrintDuplicateList
Retrieves label duplicates for printing.
- **Input**: Array of pack numbers
- **Output**: PDF label data for the requested packs
- **Notes**: Useful for reprinting lost or damaged labels

### GiveMeAllRUCHWithFilled
Retrieves list of all available pickup points with fill-level information.
- **Input**: Optional geographic filters
- **Output**: Array of pickup points with addresses, coordinates, working hours, and capacity status
- **Notes**: Used for pickup point selection UI and availability checking

## Return Packs
Return shipments are supported via dedicated return pack creation. The process:
1. Create a return pack with the original pack reference
2. Customer drops the return at a pickup point
3. Return tracked independently with its own waybill

## Services

| Service | Description |
|---------|-------------|
| COD | Cash on Delivery — collect payment from recipient |
| Insurance | Parcel value insurance |
| Return | Return pack creation for reverse logistics |

## Return Codes

Status/return codes from API responses:

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Authentication error |
| 2 | Invalid partner data |
| 3 | Invalid pack data |
| 4 | Pack not found |
| 5 | Pack already cancelled |
| 6 | Pack cannot be cancelled (in transit) |
| 99 | Internal server error |

## Error Handling
All methods return a result code and message. Non-zero result codes indicate errors. Always check the return code before processing response data.
