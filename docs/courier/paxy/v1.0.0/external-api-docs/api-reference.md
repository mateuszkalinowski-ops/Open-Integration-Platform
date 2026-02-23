# Paxy — API Reference

Base URL: https://api.paxy.pl

## Authentication
Every request requires two custom headers:
- `CL-API-KEY` (string) — API key
- `CL-API-TOKEN` (string) — API token

## Carrier Identification
The `service_name` field encodes both carrier and service type. Split on the delimiter to extract:
- `carrier_code` — Identifies the courier company
- `carrier_type` — Identifies the specific service variant

## Workflow
Registry books must be created before parcels. Parcels are associated with a book for batch management and label printing.

## Endpoints

### POST /parcels
Creates a new parcel.
- **Headers**: CL-API-KEY, CL-API-TOKEN
- **Request Body**:
  - `book_id` (int) — Registry book ID (must exist)
  - `service_name` (string) — Service identifier (encodes carrier_code + carrier_type)
  - `sender` (object) — Sender address details
  - `receiver` (object) — Receiver address details
  - `parcels` (array) — Parcel dimensions and weight
  - `cod` (object, optional) — Cash on delivery settings
  - `insurance` (object, optional) — Insurance settings
  - `reference` (string, optional) — Client reference number
- **Response**: Parcel details with waybill number
- **Status Codes**: 201 Created, 400 Bad Request, 401 Unauthorized

### POST /books
Creates a new registry book.
- **Headers**: CL-API-KEY, CL-API-TOKEN
- **Request Body**:
  - `name` (string, optional) — Book name/description
  - `pickup_date` (string, optional) — Scheduled pickup date (YYYY-MM-DD)
- **Response**: Book details with ID
- **Status Codes**: 201 Created, 400 Bad Request, 401 Unauthorized
- **Notes**: Book must be created before creating parcels

### POST /trackings
Retrieves tracking information for parcels.
- **Headers**: CL-API-KEY, CL-API-TOKEN
- **Request Body**:
  - `waybills` (array of string) — List of waybill numbers to track
- **Response**: Array of tracking event lists per waybill
- **Status Codes**: 200 OK, 400 Bad Request, 401 Unauthorized

### POST /labels/print
Generates and retrieves labels for parcels.
- **Headers**: CL-API-KEY, CL-API-TOKEN
- **Request Body**:
  - `waybills` (array of string) — List of waybill numbers
  - `format` (string, optional) — Label format
- **Response**: PDF label data
- **Content-Type**: application/pdf
- **Status Codes**: 200 OK, 400 Bad Request, 401 Unauthorized

### DELETE /parcels/{waybill}
Cancels/deletes a parcel by waybill number.
- **Headers**: CL-API-KEY, CL-API-TOKEN
- **Path Parameters**:
  - `waybill` (string) — Waybill number of the parcel to cancel
- **Response**: Cancellation confirmation
- **Status Codes**: 200 OK, 404 Not Found, 401 Unauthorized
- **Notes**: Only parcels not yet picked up can be cancelled

## Error Handling
Errors returned as JSON with HTTP status codes:
- `400` — Invalid request data
- `401` — Invalid or missing API key/token
- `404` — Resource not found
- `500` — Internal server error
