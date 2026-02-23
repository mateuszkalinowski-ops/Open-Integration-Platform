# Suus (Rohlig Suus Logistics) — API Reference

Source: https://cms.suus.com/uploads/documents-english/documentation-ws-wb-1-17-eng.pdf

## WSDL
- Production: https://wb.suus.com/webservice.php/project/Service?wsdl
- Sandbox: https://wbtest.suus.com/webservice.php/project/Service?wsdl

## Authentication
Every SOAP request includes an `auth` structure:
- `login` (string) — Account login
- `password` (string) — Account password

## Services

| Service Code | Name | Description |
|--------------|------|-------------|
| RohligCOD | Cash on Delivery | Collect payment from recipient on delivery |
| RohligUbezpieczenie3 | Insurance | Parcel value insurance coverage |

## Label Format

| Type | Description |
|------|-------------|
| labelA6 | A6-size shipping label (standard) |

## Methods

### addOrder
Creates a new transport order.
- **Input**: auth, order details (sender, receiver, parcels, services, references)
- **Output**: Order confirmation with waybill number
- **Notes**:
  - COD: include `RohligCOD` service with amount and bank account details
  - Insurance: include `RohligUbezpieczenie3` service with declared value
  - Multiple parcels supported per order

### Order Structure
- `sender` — Sender name, address, contact details
- `receiver` — Receiver name, address, contact details
- `parcels` — Array of parcel definitions (weight, dimensions, quantity)
- `services` — Array of service codes (`RohligCOD`, `RohligUbezpieczenie3`)
- `reference` — Client reference number
- `notes` — Additional delivery notes

### getEvents
Retrieves tracking events for a shipment.
- **Input**: auth, waybill number
- **Output**: Array of tracking events
- **Event Structure**:
  - `date` (datetime) — Event timestamp
  - `status` (string) — Status code
  - `description` (string) — Human-readable event description
  - `location` (string) — Event location

### getDocument
Retrieves a shipping document (label or waybill).
- **Input**: auth, waybill number, document type
- **Output**: Document content (PDF bytes)
- **Document Types**:
  - `labelA6` — A6-size shipping label
- **Notes**: Returns base64-encoded PDF content

## Error Handling
SOAP faults returned for invalid requests. Common errors:
- Authentication failure (invalid login/password)
- Order not found
- Invalid order data (missing required fields, invalid address)
- Service unavailable
