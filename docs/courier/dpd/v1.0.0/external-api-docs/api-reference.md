# DPD Poland Web Services — API Reference

Source: https://dpd.com.pl/integration

## WSDL Endpoints

### Package Services
- Production: https://dpdservices.dpd.com.pl/DPDPackageObjServicesService/DPDPackageObjServices?WSDL
- Sandbox: https://dpdservicesdemo.dpd.com.pl/DPDPackageObjServicesService/DPDPackageObjServices?WSDL

### Event/Tracking Services
- Production: https://dpdservices.dpd.com.pl/DPDPackageObjEventsService/DPDPackageObjEvents?WSDL
- Sandbox: https://dpdservicesdemo.dpd.com.pl/DPDPackageObjEventsService/DPDPackageObjEvents?WSDL

## Authentication
All requests require `authDataV1` structure:
- `login` (string) — Account login
- `password` (string) — Account password
- `masterFid` (int) — Master FID (numeric client identifier)

## Structures

### openUMLV3
Top-level shipment creation request:
- `packages` (array of packageOpenUMLV3) — List of packages
- `shipmentTime` (dateTime, optional) — Requested shipment date

### packageOpenUMLV3
Defines a single package (may contain multiple parcels):
- `parcels` (array of parcelOpenUMLV3) — List of parcels in this package
- `sender` (senderDPPV2) — Sender data
- `receiver` (receiverDPPV2) — Receiver data
- `payerType` (string) — SENDER / RECEIVER / THIRD_PARTY
- `thirdPartyFID` (int, optional) — FID of third-party payer
- `ref1` (string, optional) — Reference field 1
- `ref2` (string, optional) — Reference field 2
- `ref3` (string, optional) — Reference field 3
- `services` (servicesOpenUMLV3) — Additional services

### parcelOpenUMLV3
Defines a single parcel within a package:
- `sizeX` (int) — Width in cm
- `sizeY` (int) — Height in cm
- `sizeZ` (int) — Length in cm
- `weight` (float) — Weight in kg
- `content` (string, optional) — Content description
- `customerData1` (string, optional) — Custom data field

### senderDPPV2 / receiverDPPV2
Address structure for sender and receiver:
- `fid` (int, optional) — DPD client FID (for registered senders)
- `company` (string) — Company name
- `name` (string) — Contact person name
- `address` (string) — Street and building number
- `city` (string) — City
- `postalCode` (string) — Postal code (format: XX-XXX)
- `countryCode` (string) — ISO 3166-1 alpha-2 country code
- `phone` (string) — Phone number
- `email` (string) — Email address

### servicesOpenUMLV3
Additional services for a package:
- `declaredValue` (declaredValueV2, optional) — Declared value / insurance
  - `amount` (decimal) — Value amount
  - `currency` (string) — Currency code (PLN, EUR, etc.)
- `cod` (codV2, optional) — Cash on delivery
  - `amount` (decimal) — COD amount
  - `currency` (string) — Currency code
- `guarantee` (guaranteeV2, optional) — Delivery guarantee
  - `type` (string) — B2C / TIME0930 / TIME1200 / SATURDAY / TIMEFIXED
  - `value` (string, optional) — Fixed time value (HH:MM for TIMEFIXED)
- `cud` (bool, optional) — Documents return
- `rod` (bool, optional) — Return on delivery
- `selfCol` (selfColV2, optional) — Self-collection at DPD pickup point
  - `machineId` (string) — Pickup point ID
- `pallet` (bool, optional) — Pallet shipment flag
- `inPers` (bool, optional) — Delivery in person only
- `privPers` (bool, optional) — Delivery to private person

## Methods

### generatePackagesNumbersV4
Creates shipments and generates waybill numbers.
- **Input**: `authDataV1` + `openUMLV3` + `pkgNumsGenerationPolicyV1` (STOP_ON_FIRST_ERROR / ALL_OR_NOTHING / IGNORE_ERRORS)
- **Output**: `packagesGenerationResponseV3`
  - `packages` — Array of package results
    - `parcels` — Array with `waybill` (string), `status` (string)
    - `packageId` (int) — Internal package identifier
    - `validationDetails` — Validation messages if any

### generateSpedLabelsV4
Generates shipping labels in PDF format.
- **Input**: `authDataV1` + `dpdServicesParamsV2`
  - `session` (sessionDSPV1) — Session parameters
    - `sessionType` (string) — DOMESTIC / INTERNATIONAL
    - `packages` (array) — Array of package objects with `parcels` containing `waybill`
  - `outputDocFormatDSPEnumV1` (string) — PDF / LBLP (label printer format)
  - `outputDocPageFormatDSPEnumV1` (string) — A4 / LBL_PRINTER
  - `outputLabelType` (string) — BIC3 (standard label)
- **Output**: `outputDocumentV1`
  - `documentData` (base64Binary) — Label file content (PDF or LBLP)

### packagesPickupCallV4
Books a courier pickup for packages.
- **Input**: `authDataV1` + `dpdPickupCallParamsV3`
  - `orderType` (string) — DOMESTIC / INTERNATIONAL
  - `waybillsReady` (bool) — Whether labels are already printed
  - `pickupDate` (date) — Requested pickup date
  - `pickupTimeFrom` (time) — Pickup window start (HH:MM)
  - `pickupTimeTo` (time) — Pickup window end (HH:MM)
  - `contactInfo` (contactInfoDPPV1) — Pickup contact details
    - `name` (string) — Contact person
    - `phone` (string) — Phone number
    - `email` (string) — Email
  - `pickupAddress` (senderDPPV2) — Pickup address
- **Output**: `packagesPickupCallResponseV3`
  - `orderNumber` (string) — Pickup order confirmation number
  - `statusInfo` (statusInfoDPPV2) — Status message

### getEventsForWaybillV1
Retrieves tracking events for a waybill number.
- **Input**: `authDataV1` + `waybill` (string) + `language` (string, PL/EN)
- **Output**: `eventsForWaybillResponseV1`
  - `eventsList` — Array of tracking events
    - `eventTime` (dateTime) — Event timestamp
    - `eventDescription` (string) — Event description
    - `depot` (string) — Depot code
    - `depotName` (string) — Depot name
    - `country` (string) — Country code

### findPostalCodeV1
Validates a postal code and returns service availability.
- **Input**: `authDataV1` + `postalCode` (string)
- **Output**: Status and available services for the postal code

### getCourierAvailabilityV1
Checks courier availability for a pickup address on a given date.
- **Input**: `authDataV1` + `senderFID` or address + `pickupDate`
- **Output**: Available pickup time windows

## Error Handling
DPD returns structured fault messages:
- `errorCode` (string) — Machine-readable error code
- `errorDescription` (string) — Human-readable error description

Common error codes:
- `INVALID_LOGIN_DATA` — Authentication failed
- `INVALID_POSTAL_CODE` — Postal code not in DPD service area
- `WAYBILL_NOT_FOUND` — Waybill number does not exist
- `PICKUP_DATE_TOO_EARLY` — Pickup date is in the past
- `WEIGHT_EXCEEDED` — Parcel weight exceeds maximum allowed
- `RATE_LIMIT_EXCEEDED` — Too many requests (max 60/minute)
