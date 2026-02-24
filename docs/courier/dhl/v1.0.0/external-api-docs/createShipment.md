# DHL24 WebAPI v2 — createShipment (Grouping Method)

> Source: https://dhl24.com.pl/en/webapi2/doc/info/createShipment.html
> Fetched: 2026-02-24

Creates a shipment and optionally books a courier in one request.

## Input Parameters

### Top-level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authData` | AuthData | Yes | Authorization structure |

### shipmentInfo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dropOffType` | string | Yes | `REGULAR_PICKUP` — create without restrictions; `REQUEST_COURIER` — create + book courier; `COURIER_ONLY` — book courier only |
| `serviceType` | string | Yes | See Service Types table |
| `labelType` | string | Yes | `LP`, `BLP`, `LBLP`, `ZBLP`, `ZBLP300` |
| `content` | string(30) | Yes | Parcel content description |
| `comment` | string(100) | No | Additional comments (first 50 chars sent to courier) |
| `reference` | string(200) | No | Shipment reference number |
| `wayBill` | string(11) | No | Custom waybill number |
| `servicePointAccountNumber` | string | No | Required for SP product if receiver empty |

### Service Types

| Code | Description |
|------|-------------|
| `AH` | Domestic shipment |
| `09` | Domestic service 09 (delivery by 9:00) |
| `12` | Domestic service 12 (delivery by 12:00) |
| `DW` | Evening delivery shipment |
| `SP` | Delivery to DHL service point |
| `EK` | Connect shipment |
| `PI` | International shipment |
| `PR` | Premium product |
| `CP` | Connect Plus shipment |
| `CM` | Connect Plus Pallet shipment |

### billing

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `shippingPaymentType` | string | Yes | `SHIPPER`, `RECEIVER`, `USER` (third party) |
| `billingAccountNumber` | integer | Yes | Customer number to charge |
| `paymentType` | string | Yes | `BANK_TRANSFER` (agreement + SAP required) |
| `costsCenter` | string(20) | No | Cost center |

### specialServices (array of items)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `serviceType` | string | No | Service code (see table) |
| `serviceValue` | float | No | Value for insurance/COD |
| `textInstruction` | string(32) | No | Return document name (ROD) |
| `collectOnDeliveryForm` | string | No | COD refund form: `BANK_TRANSFER` |
| `eRodemail` | string(60) | No | Email for eROD service |

#### Special Service Codes

| Code | Description | Extra cost |
|------|-------------|------------|
| `1722` | Evening delivery (17:00–22:00) | Yes |
| `SOBOTA` | Saturday delivery | Yes |
| `NAD_SOBOTA` | Saturday pickup | Yes |
| `UBEZP` | Shipment insurance | Yes |
| `COD` | Cash on delivery | Yes |
| `PDI` | Pre-delivery information | Yes |
| `ROD` | Return of documents | Yes |
| `SAS` | Delivery to neighbour | Free |
| `ODB` | Self-pickup | Free |
| `AGEVER` | Age verification | Yes |

### shipmentTime

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `shipmentDate` | string | Yes | Date in YYYY-MM-DD |
| `shipmentStartHour` | string(32) | Yes | Start time HH:MM |
| `shipmentEndHour` | string(32) | Yes | End time HH:MM |

### shipper / receiver (address data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `addressType` | string(1) | Yes (receiver only) | `B` = business, `C` = consumer |
| `country` | string(2) | Yes (receiver) | Country code |
| `isPackstation` | bool | No | Delivery to DHL Parcelstation |
| `isPostfiliale` | bool | No | Delivery to DHL ServicePoint |
| `postnummer` | string(10) | No | Customer number (DE parcel lockers) |
| `name` | string(60) | Yes | Name (first+last or company) |
| `postalCode` | string | Yes | Postal code (without dash) |
| `city` | string(17) | Yes | City |
| `street` | string(35) | Yes | Street |
| `houseNumber` | string(10) | Yes | House number |
| `apartmentNumber` | string(10) | No | Apartment number |

#### Contact / preaviso

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `personName` | string(50) | No | Contact person name |
| `phoneNumber` | string(9) | No | Phone (9 digits) |
| `emailAddress` | string(60) | No | Email address |

### pieceList (array of items)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `ENVELOPE`, `PACKAGE`, `PALLET` |
| `weight` | integer | Yes* | Weight in kg (*not for ENVELOPE) |
| `width` | integer | Yes* | Width in cm |
| `height` | integer | Yes* | Height in cm |
| `length` | integer | Yes* | Length in cm |
| `quantity` | integer | Yes | Number of parcels |
| `nonStandard` | bool | No | Non-standard parcel flag |
| `euroReturn` | bool | No | Pallet return flag |
| `blpPieceId` | string(32) | No | Custom BLP parcel ID (JJD) |

### customs (international shipments outside EU)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customsType` | string(1) | Yes | `U` = simplified, `I` = individual |
| `costsOfShipment` | integer | Yes | Gross transport value |
| `currency` | string(3) | Yes | `GBP`, `PLN`, `EUR`, `CHF`, `USD` |
| `nipNr` | string(12) | Yes (individual) | NIP number |
| `eoriNr` | string(17) | Yes (individual) | EORI number |
| `vatRegistrationNumber` | string(15) | Yes | VAT registration number |
| `categoryOfItem` | string(2) | Yes | `9`=Other, `11`=Sale, `21`=Return, `31`=Gifts, `32`=Samples, `91`=Documents |
| `invoiceNr` | string(35) | Yes (individual) | Invoice number |
| `invoiceDate` | string(10) | Yes (individual) | Invoice date YYYY-MM-DD |
| `countryOfOrigin` | string(2) | No | ISO 3166-1 alpha-2 |

#### customsItem (array)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nameEn` | string(35) | Yes | English item name |
| `namePl` | string(35) | Yes (individual) | Polish item name |
| `quantity` | integer | Yes | Number of components |
| `weight` | float | Yes | Item weight |
| `value` | float | Yes | Item value |
| `tariffCode` | string(10) | Yes (individual) | Customs tariff code |

## Output Parameters

| Field | Type | Description |
|-------|------|-------------|
| `shipmentNotificationNumber` | string | Parcel ID (waybill) |
| `dispatchNotificationNumber` | string | Order ID (if courier booked) |
| `labelType` | string | Label type returned |
| `labelFormat` | string | MIME format |
| `labelContent` | string | Label content (base64) |
| `cn23MimeType` | string | CN23 customs doc type (simplified clearance) |
| `cn23Content` | string | CN23 content (base64) |
| `fvProformaMimeType` | string | Proforma invoice type |
| `fvProformaContent` | string | Proforma invoice (base64) |

## SOAP Request Example

```xml
<createShipment>
  <authData>
    <username>testuser</username>
    <password>testpass</password>
  </authData>
  <shipment>
    <shipmentInfo>
      <dropOffType>REQUEST_COURIER</dropOffType>
      <serviceType>AH</serviceType>
      <billing>
        <shippingPaymentType>SHIPPER</shippingPaymentType>
        <billingAccountNumber>1204663</billingAccountNumber>
        <paymentType>BANK_TRANSFER</paymentType>
      </billing>
      <shipmentTime>
        <shipmentDate>2026-02-24</shipmentDate>
        <shipmentStartHour>12:00</shipmentStartHour>
        <shipmentEndHour>15:00</shipmentEndHour>
      </shipmentTime>
      <labelType>BLP</labelType>
    </shipmentInfo>
    <content>Computer game</content>
    <ship>
      <shipper>
        <contact>
          <personName>Jan Kowalski</personName>
          <phoneNumber>123456789</phoneNumber>
          <emailAddress>jan@example.com</emailAddress>
        </contact>
        <address>
          <name>Jan Kowalski</name>
          <postalCode>00909</postalCode>
          <city>Warszawa</city>
          <street>Lesna</street>
          <houseNumber>9</houseNumber>
        </address>
      </shipper>
      <receiver>
        <contact>
          <personName>Anna Nowak</personName>
          <phoneNumber>987654321</phoneNumber>
          <emailAddress>anna@example.com</emailAddress>
        </contact>
        <address>
          <addressType>B</addressType>
          <country>PL</country>
          <name>Anna Nowak</name>
          <postalCode>02796</postalCode>
          <city>Warszawa</city>
          <street>Wawozowa</street>
          <houseNumber>2</houseNumber>
        </address>
      </receiver>
    </ship>
    <pieceList>
      <item>
        <type>PACKAGE</type>
        <weight>5</weight>
        <width>30</width>
        <height>20</height>
        <length>40</length>
        <quantity>1</quantity>
      </item>
    </pieceList>
  </shipment>
</createShipment>
```
