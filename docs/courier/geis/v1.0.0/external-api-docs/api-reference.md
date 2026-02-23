# Geis GService — API Reference

Source: https://www.geis.pl/en/download-tech-support

## WSDL
- Production: https://gservice.geis.pl/?wsdl
- Sandbox: https://gservicetest.geis.pl/?wsdl

## Authentication
Credentials included in every SOAP request:
- `CustomerCode` (string) — Geis customer account number
- `Password` (string) — Account password

## Shipment Types

### Domestic
Standard shipments within Poland. Created via `InsertOrder`.

### Export
International shipments. Created via `InsertExport` with additional customs and destination country data.

## Distribution Channels
Geis supports multiple distribution channels defining how the shipment is handled and delivered. Channel selection affects routing, delivery speed, and available services.

## Methods

### InsertOrder
Creates a new domestic shipment order.
- **Input**: Authentication, sender, receiver, parcel details, services, distribution channel
- **Output**: Shipment confirmation with waybill number
- **Notes**: For Polish domestic shipments only

### InsertExport
Creates a new export (international) shipment.
- **Input**: Authentication, sender, receiver, parcel details, customs data, destination country
- **Output**: Shipment confirmation with waybill number
- **Notes**: Requires additional customs/export documentation fields

### CreatePickUp
Schedules a courier pickup for created shipments.
- **Input**: Authentication, pickup date, time window, pickup address, shipment references
- **Output**: Pickup confirmation with scheduled time

### GetLabel
Retrieves shipping label for a shipment.
- **Input**: Authentication, waybill number, label format
- **Output**: Label content (PDF bytes)

### ShipmentStatus
Retrieves current status of a shipment.
- **Input**: Authentication, waybill number
- **Output**: Current status code and description with timestamp

### ShipmentDetail
Retrieves full shipment details.
- **Input**: Authentication, waybill number
- **Output**: Complete shipment data including sender, receiver, parcels, services, tracking events

### DeleteShipment
Deletes/cancels a shipment.
- **Input**: Authentication, waybill number
- **Output**: Deletion confirmation
- **Notes**: Only shipments not yet picked up can be deleted

### AssignRange
Assigns a range of waybill numbers for offline label printing.
- **Input**: Authentication, range size
- **Output**: Assigned waybill number range (from–to)
- **Notes**: Used when pre-printing labels before API submission

### IsHealthy
Health check for the SOAP service availability.
- **Input**: None (or minimal authentication)
- **Output**: Boolean health status
- **Notes**: Use for monitoring service availability before processing shipments

## Error Handling
SOAP faults returned for invalid requests. Check SOAP fault code and fault string for error details. Common errors:
- Invalid credentials
- Shipment not found
- Invalid address data
- Shipment already in transit (cannot delete)
- No available waybill ranges
