# DB Schenker TransportOrders API — API Reference

Source: WSDL at https://api2.schenker.pl/services/TransportOrders?wsdl

## WSDL
- Production: https://api2.schenker.pl/services/TransportOrders?wsdl
- Sandbox: https://testapi2.schenker.pl/services/TransportOrders?wsdl

## Authentication
HTTP Basic Auth — username and password sent as HTTP headers with every SOAP request.

## Reference Types

| Code | Name | Description |
|------|------|-------------|
| DWB  | Waybill | Schenker waybill number |
| COR  | Customer Order Reference | Client-side reference |
| PKG  | Package | Individual package reference |

## SSCC Support
Serial Shipping Container Code (SSCC) — 18-digit GS1 standard identifier for logistics units (pallets, parcels). Used for pallet-level tracking and identification within Schenker's network.

## Services

| Code | Description |
|------|-------------|
| 9    | Cash on Delivery (COD) |

## Methods

### createOrder
Creates a new transport order.
- **Input**: Order details including sender, receiver, parcels, services, references
- **Output**: Order confirmation with waybill number and SSCC codes
- **Notes**: Supports multi-parcel orders with individual SSCC per parcel

### cancelOrder
Cancels an existing transport order.
- **Input**: Waybill number (DWB reference)
- **Output**: Cancellation confirmation with status
- **Notes**: Only orders not yet picked up can be cancelled

### getOrderStatus
Retrieves current status of an order.
- **Input**: Reference number (DWB, COR, or PKG)
- **Output**: Current order status with timestamp and location

### getTracking
Retrieves full tracking history for a shipment.
- **Input**: Waybill number or reference
- **Output**: Array of tracking events with timestamps, locations, and status descriptions

### getDocuments
Retrieves shipping documents (labels, waybills).
- **Input**: Waybill number, document type
- **Output**: Document content (PDF bytes)
- **Notes**: Supports label and waybill document types

## Error Handling
SOAP faults returned for invalid requests. Common fault codes:
- Invalid credentials (HTTP 401)
- Order not found
- Order already cancelled
- Invalid address data
- Missing required fields
