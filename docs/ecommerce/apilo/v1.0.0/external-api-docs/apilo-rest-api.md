Apilo Rest API - Dokumentacja

Dokumentacja REST API dla Apilo

- Obsługa języków - Opcjonalnie
- Format daty
- Filtry dla list
- Obsługa zasobów API

Authorization

- postObtaining access_token and refresh_token tokens.

Connection

- getConnection info.
- getConnection test.

Finance document

- delDelete a document for accounting documents.
- postCreate a document for accounting documents.
- getGet list of accounting documents.
- getGet accounting document numbering series.

Order

- delDelete order tag.
- postCreate order tag.
- getOrder tags list.
- getGet shipment status map.
- getShipment detail.
- postAdd shipment to order.
- getList of order shipments.
- postAdd note to order.
- getGet order notes.
- getTag list.
- getGet Platform list.
- getGet Carrier Account list.
- getGet list of Carrier.
- getGet order Status types list.
- getGet Payment types list.
- getGet document types map.
- delDelete document for given order.
- getOrder Document detail.
- postCreate document for order.
- getGet simple list of documents for given order.
- getOrder Binary document.
- postAdd payment to Order.
- putUpdate order status.
- getGet order default shipping settings.
- getGet detailed order by given ID.
- postCreate a new order.
- getGet simple list of orders.

Warehouse

- getPrice lists.
- delDelete price.
- postPrice create and update.
- getPrices list.
- delDelete Product.
- getGet Product detail.
- patchProducts PATCH update.
- postProducts create.
- putProducts data update.
- getProducts list.
- postCategory create.
- getCategories list.
- getProducts Media list.
- patchProduct Attribute update.
- delProduct Attributes Delete.
- getProduct attribute list.
- patchAttribute update.
- postAttribute create.
- getAttribute List.

Sale

- getGet auctions list.
- getGet list of sales channels.

Media

- getGet media.
- postCreate new media attachment.

Shipment

- postGet shipment pick up date proposal.
- postConfirm shipment and order pickup.
- getGet list of shipment carrier documents.
- postCreates a new shipment from the submitted data.
- getGet list of shipment option need to create new shipment.
- getGet Carrier sending methods.
- getGet Carrier Account list.
- getGet a list of shipments tracking information for given filters.
- getGet list of shipments for given filters.
- getGet detailed shipment by given ID.

[API docs by Redocly](https://redocly.com/redoc/)

# Apilo REST API (2.0.0.5)

Download OpenAPI specification: [Download](https://developer.apilo.com/uploads/apilo/swagger.json)

## Dokumentacja REST API dla Apilo

Limit zapytań to 150req/min.

## Obsługa zasobów API

Dla wszystkich zasobów niezwiązanych z procesem autoryzacji należy dołączyć następujące nagłówki:

```
Accept: application/json
Content-Type: application/json
Authorization: Bearer access_token

```

Dla każdego zapytania (również autoryzacyjnych) należy określić typ mediów (nagłówek Accept oraz Content-Type), będzie to zawsze application/json. Zarówno dla zapytań wysyłanych na serwer jak i danych zwracanych przez serwer stosowany jest format danych (payload) JSON. Należy odpowiednio dla zapytań enkodować dane do tego formatu oraz dla odpowiedzi dekodować dane tego formatu.

Przesyłając dane do API: Pola opcjonalne można wypełnić lub przypisać im wartość null w przypadku zapytań POST/PUT lub nie przesyłać ich w przypadku filtrów GET. Pola obowiązkowe należy zawsze wypełnić właściwą wartością.

## Filtry dla list

Dla zasobów typu GET z listą wyników można stosować dodatkowe filtry manipulujące wynikami. Parametry należy przekazać w URL zaraz za znakiem kończącym adres zasobu, np.`.../api/orders/?limit=200` Dla list dostępne są dwa ogólne filtry:

`int``limit`- Limit zwracanych wyników (maksymalnie 2000)`int``offset`- Wskaźnik pozycji (0 - sam początek, 1 - pomija jeden rekord, 256 - pomija 256 rekordów)

## Format daty

Daty dla przesyłanych wartości (filtry oraz przesyłane obiekty metodą POST/PUT) stosowany jest format daty ISO 8601 w następującym formacie:`DateTimeIso``YYYY-MM-DDTHH-MM-SSZ`. W PHP jest to`DateTimeInterface::ATOM`. Domyślnie w takim formacie stosowany jest czas zulu (trzeba uwzględnić przesunięcie względem strefy czasowej). Czas Zulu można zastąpić lokalizacją strefy czasowej, np. w przypadku Polski jest to +0200 w przypadku czasu letniego lub +0100 w przypadku czasu podstawowego (przekazując strefę czasową w filtrze - parametr GET - należy pamiętać o zakodowaniu znaku plusa, w przeciwnym wypadku zostanie zinterpretowany jako spacja).

`2024-09-12T08:16:32+02:00`

## Obsługa języków - Opcjonalnie

`Nagłówek nie jest wymagany do prawidłowego działania zapytania wysłanego do serwera.`

Dla obsługi domyślnym językiem odpowiedzi jest język polski, w celu zmienienia języka należy dodać następujący nagłówek

```
Accept-Language: pl

```

Wartości które nagłówek może przyjąć to`pl``de``en``en-US``en-GB`.

Więcej informacji:

- [RFC 3282](https://datatracker.ietf.org/doc/html/rfc3282)
- [Accept-Language - HTTP | MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Language)

## Authorization

Autoryzacja API odbywa się za pomocą access tokenu ważnego 21 dni. Po wygaśnięciu (lub przed) access tokenu należy go odnowić korzystając z refresh tokenu (ważnego 2 miesiące). Aby pobrać parę kluczy access oraz refresh token należy utworzyć nową aplikację w systemie Apilo w zakładce Administracja/API Apilo. Domyślnie każdy wygenerowany klucz ma scope read oraz write.

## Obtaining access_token and refresh_token tokens.

This method allows you to get`access_token` and`refresh_token` through two scenarios:

- exchange of`refresh_token` for tokens (token refresh operation)
- exchanging`authorization_code` for tokens

##### Authorizations:

BasicAuth

##### Request Body schema: application/jsonrequired

Obtaining access_token and refresh_token tokens

grantType

required

string

Enum: "authorization_code" "refresh_token"

Authorization grant type

token

required

string

Authorization code when grant type is`authorization_code` or Refresh token when grant type is`refresh_token`

string or null (optional.)

Developer UUID (optional)

| developerId |
| --- |

### Responses

201

Credentials

401

Authorization failed

403

Invalid authorization code

422

Invalid Accept header value

post/rest/auth/token/

### Request samples

- Payload

Content type

application/json

Copy

`{"grantType": "authorization_code","token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJleGFtcGxlLmVycGJveC5wbCIsImV4cCI6MTYxNTg5NzYxOSwianRpIjoiOTc2YjYxYmItNWRkMC01MjIxLWExY2MtNzNiY2Q0MzVhNGMyIiwidHlwZSI6InJlZnJlc2hfdG9rZW4iLCJjbGllbnRfaWQiOjIsInBsYXRmb3JtX2lkIjoxLCJpYXQiOjE2MDc5NTMyMTl9.XH8X9cA0eb0RNlQJn8_jIQFDFVmKnOCDO0YWVvaM5B8","developerId": "abc8c088-f9e0-42a8-b2e7-3fa0e90aa1be"}`

### Response samples

- 422
- 403
- 401
- 201

Content type

application/json

Copy

`{"accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJleGFtcGxlLmVycGJveC5wbCIsImV4cCI6MTYwOTc2NzYxOSwianRpIjoiZTg0Yjg3MWItMjg1NS01NzVkLWJlYzMtNzdhMjcwOTdlOTYyIiwidHlwZSI6ImFjY2Vzc190b2tlbiIsImNsaWVudF9pZCI6MiwicGxhdGZvcm1faWQiOjEsImlhdCI6MTYwNzk1MzIxOX0.iQJ78Xqd7exf7M6l26iWS-Nor0AjxJKwsyHPwOFpJ-s","accessTokenExpireAt": "2021-01-04T14:40:19Z","refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJleGFtcGxlLmVycGJveC5wbCIsImV4cCI6MTYxNTg5NzYxOSwianRpIjoiOTc2YjYxYmItNWRkMC01MjIxLWExY2MtNzNiY2Q0MzVhNGMyIiwidHlwZSI6InJlZnJlc2hfdG9rZW4iLCJjbGllbnRfaWQiOjIsInBsYXRmb3JtX2lkIjoxLCJpYXQiOjE2MDc5NTMyMTl9.XH8X9cA0eb0RNlQJn8_jIQFDFVmKnOCDO0YWVvaM5B8","refreshTokenExpireAt": "2021-03-16T13:26:59Z"}`

## Connection

Connection and status information

## Connection test.

Test Api

##### Authorizations:

BearerAuth

### Responses

200

Hello

401

Authorization failed

get/rest/api/

### Response samples

- 401
- 200

Content type

application/json

Copy

`{"content": "string"}`

## Connection info.

Informacje o połączeniu

##### Authorizations:

BearerAuth

### Responses

200

Successfull operation

401

Authorization failed

get/rest/api/whoami/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"content": [{"clientId": 1,"name": "Api Key Name","validTo": "2024-07-10T10:04:31+0200"}]}`

## Finance document

Integration with document finances

## Get accounting document numbering series.

List of numbering series

##### Authorizations:

BearerAuth

##### query Parameters

integer

Enum: 1 5 10 31

Type of accounting document (1-Invoice, 5-Receipt, 10-Proforma, 31-Corrective invoice)

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| type |
| --- |
| offset |
| limit |

### Responses

200

Numbering series array

401

Authorization failed

get/rest/api/finance/document-configs/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"documentConfigs": [{"id": 1,"type": 1,"name": "Faktura (domyślnie)","status": 1},{"id": 2,"type": 31,"name": "Faktura korygująca (domyślnie)","status": 1},{"id": 3,"type": 5,"name": "Paragon (domyślnie)","status": 1},{"id": 4,"type": 10,"name": "Faktura pro forma (domyślnie)","status": 1}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Get list of accounting documents.

List of accounting documents

##### Authorizations:

BearerAuth

##### query Parameters

integer

Enum: 1 5 10 31

Type of accounting document (1-Invoice, 5-Receipt, 10-Proforma, 31-Corrective invoice)

integer

Enum: 1 2

A DocumentDocument of the specified type is created (1-printed, 2-exported to an external platform)

integer

Enum: 1 2

A DocumentDocument of the specified type is not created (1-printed, 2-exported to an external platform)

boolean

Only for type Receipt type (type=5)

Array of integers

ID of accounting document numbering series

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of finance document invoice at before date, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33+0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of finance document invoice at after date, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33+0200`

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| type |
| --- |
| hasDocumentDocumentType |
| hasNotDocumentDocumentType |
| isFiscal |
| documentConfig[] |
| invoiceBefore |
| invoiceAfter |
| offset |
| limit |

### Responses

200

Returns list of accounting documents

401

Authorization failed

get/rest/api/finance/documents/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"documents": [{"id": 3148,"documentNumber": "INV/3/12/2023","originalAmountTotalWithTax": "123.00","originalAmountTotalWithoutTax": "100.00","originalCurrencyExchangeValue": "1.0000","originalCurrency": "PLN","currency": "PLN","createdAt": "2023-11-24T08:33:07+0100","invoicedAt": "2023-11-20","soldAt": "2023-11-20","type": 5,"documentReceiver": {"id": 1121,"name": "Jan Kowalski","companyName": "Kowalsky Sp. z o.o.","companyTaxNumber": "1573091058","streetName": "ul. Pawia","streetNumber": "9","city": "Kraków","zipCode": "31-154","country": "PL","type": "company"},"documentIssuer": {"id": 1121,"name": "Jan Kowalski","companyName": "Kowalsky Sp. z o.o.","companyTaxNumber": "1573091058","streetName": "ul. Pawia","streetNumber": "9","city": "Kraków","zipCode": "31-154","country": "PL","type": "company"},"documentItems": [{"id": 329,"originalPriceWithTax": 123,"originalPriceWithoutTax": 100,"tax": 23,"quantity": 1,"originalAmountTotalWithTax": 100,"originalAmountTotalWithoutTax": 100,"originalAmountTotalTax": 100,"gtu": 2,"name": "FV/1/12/2020","sku": "P44/3-T1.2","ean": "400638133393","unit": "Szt.","type": 1}],"paymentType": 3,"orderId": "MA250302531"}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Create a document for accounting documents.

Create a document for accounting documents

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string

##### Request Body schema: application/jsonrequired

idExternal

required

integer

Unique document ID

number

required

string or null

Document number

status

required

string ( 4 - disabled, 1 - enabled)

Enum: 1 4

1-enabled/ok, 4-disabled/error

string

Enum: 1 2

1-printed (default), 2-exported to an external platform

object (DocumentDocumentCreatePreferencesDTO)

| type |
| --- |
| preferences |

### Responses

200

Document has not been created

201

Document has been created

401

Authorization failed

409

Document with the given idExternal already exists

422

Validation error

post/rest/api/finance/documents/{id}/documents/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"idExternal": 24,"number": "DOC/013/2023","status": 1,"type": 1,"preferences": {"message": "An error occurred while trying to print the receipt"}}`

### Response samples

- 422
- 409
- 401
- 201
- 200

Content type

application/json

Copy

`[ ]`

## Delete a document for accounting documents.

##### path Parameters

id

required

integer\d+

Internal ID of the document (e.g. 31)

idExternal

required

integer\d+

Unique document ID (e.g. 24)

### Responses

200

If deleted

401

Authorization failed

404

Not deleted

delete/rest/api/finance/documents/{id}/documents/{idExternal}/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"message": "string","code": 0,"description": "string","errors": [{ }],"field": "string"}`

## Order

Integration with orders

## Get simple list of orders.

Example URL for filters and sort:`/rest/api/orders/?orderStatus=7&createdAfter=2022-03-01T14%3A40%3A33%2B0200&order&sort=updatedAtDesc` The fields orderItems and addressCustomer will be returned conditionally from end of 2022

##### Authorizations:

BearerAuth

##### query Parameters

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

The date of order creation from in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33+0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of order creation from customer, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33+0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of order to customer, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33+0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Update date from in Apilo system, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33+0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Update date to in Apilo system, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33+0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Update date from in Apilo system, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33+0200`

integer [ 0 .. 1 ]

Determines whether a document exists for the order, takes the value of 1 or 0

string^[A-Za-z0-9\.|]{10,11}$

Order number in Apilo system, e.g.`AL0012345`

string <= 36 characters

External order number, e.g.`5200669628624`

integer >= 1

Order status according to the order status map

Array of integers [ items >= 1 ]

Array of Order Status according to the order status map, example:`/rest/api/orders/?orderStatusIds[]=1&orderStatusIds[]=2`

integer >= 1

Order Payment Status Order payment Status

integer >= 1

Order Payment type Order Payment Type

integer >= 1

Platform account Id Platform account Id

integer >= 1

Carrier account Id Carrier account Id

string [ 1 .. 128 ] characters

Client E-mail

integer

Enum: "createdAtAsc" "createdAtDesc" "updatedAtAsc" "updatedAtDesc" "orderedAtAsc" "orderedAtDesc"

Sort options

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| createdAfter |
| --- |
| createdBefore |
| orderedAfter |
| orderedBefore |
| updatedAfter |
| updatedBefore |
| isOrderDocument |
| id |
| idExternal |
| orderStatus |
| orderStatusIds[] |
| paymentStatus |
| paymentType |
| platformAccountId |
| carrierId |
| email |
| sort |
| offset |
| limit |

### Responses

200

Order array

401

Authorization failed

get/rest/api/orders/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"orders": [{"id": "AL231100017","status": 3,"idExternal": "WWW/341/2023","isInvoice": true,"paymentStatus": 2,"paymentType": 2,"originalCurrency": "PLN","isEncrypted": false,"createdAt": "2022-06-09T10:59:12Z","updatedAt": "2022-06-09T10:59:12Z","orderItems": [{"id": 1,"idExternal": "359","ean": "400638133393","sku": "P44/3-T1.2","originalName": "Samsung Galaxy S20 Plus Black 128GB 5G","originalCode": "PHONE-S20-128GB-B","originalPriceWithTax": "2799.99","originalPriceWithoutTax": "2799.99","media": null,"quantity": 2,"tax": "23.00","productSet": null,"status": 1,"unit": "Szt.","type": 1,"productId": 12345},{"id": 2,"idExternal": null,"ean": null,"sku": "ship-pp","originalName": "Wysyłka - Poczta Polska - Pocztex","originalCode": null,"originalPriceWithTax": "10.00","originalPriceWithoutTax": "10.00","media": null,"quantity": 1,"tax": null,"productSet": null,"status": 1,"unit": null,"type": 2,"productId": null}],"addressCustomer": {"id": 123,"name": "Jan Kowalski","phone": "+48 500 000 000","email": "jan.kowalski@apilo.com","streetName": "Testowa","streetNumber": "4b/12","city": "Kraków","zipCode": "31-154","country": "PL","department": "string","class": "company"},"platformId": 1,"isCanceledByBuyer": false,"carrierId": 1,"platformAccountId": 1}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Create a new order.

Create a new order

##### Authorizations:

BearerAuth

##### Request Body schema: application/json

platformId

required

integer >= 1

Sale platform account ID

string or null (Provided by external systems.) <= 36 characters

External order ID, e.g. on the sales platform

boolean

Does the customer want a VAT invoice?

string <= 128 characters

paymentStatus

required

string

Enum: 0 1 2 3

Payment status (`0-no payment`,`1-partially paid`,`2-paid in full/amount in accordance with the order`,`3-overpayment`)

paymentType

required

integer (integer.) >= 1

Payment method ID

originalCurrency

required

string = 3 characters

Order currency

originalAmountTotalWithoutTax

required

string or null [ 0.01 .. 99999999.99 ]

Value of the order items without tax

originalAmountTotalWithTax

required

string or null [ 0.01 .. 99999999.99 ]

Value of order items including tax

originalAmountTotalPaid

required

string or null [ 0 .. 99999999.99 ]

Gross amount paid by customer in original currency

string or null 

Minimal shipping date

string or null 

Maximum shipping date

object

Extra order fields

orderItems

required

Array of objects (RestOrderItemsDTO)

Order items list

Array of objects (Wpłaty klienta.)

Order payments list

addressCustomer

required

object (RestOrderAddressDTO)

addressDelivery

required

object (RestOrderAddressDTO2)

object (RestOrderAddressDTO3)

carrierAccount

required

integer >= 1

Carrier account ID

Array of objects (Array of objects.)

Order notes and comments

orderedAt

required

string or null (DateTime format.)

Date when the order was created by the customer

status

required

integer >= 1

Status ID

| idExternal |
| --- |
| isInvoice |
| customerLogin |
| sendDateMin |
| sendDateMax |
| preferences |
| orderPayments |
| addressInvoice |
| orderNotes |

### Responses

200

Order with the given idExternal already exists

201

Create order correctly 2

401

Authorization failed

404

Invalid platform ID

422

Validation error

post/rest/api/orders/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"platformId": 1,"idExternal": "WWW/341/2023","isInvoice": true,"customerLogin": "user123","paymentStatus": 2,"paymentType": 2,"originalCurrency": "PLN","originalAmountTotalWithoutTax": 1024.37,"originalAmountTotalWithTax": 1259.98,"originalAmountTotalPaid": 1259.98,"sendDateMin": "2022-03-07T00:00:00Z","sendDateMax": "2022-03-08T20:00:00Z","preferences": {"idUser": "user-12345"},"orderItems": [{"id": 1,"idExternal": "359","ean": "400638133393","sku": "P44/3-T1.2","originalName": "Samsung Galaxy S20 Plus Black 128GB 5G","originalCode": "PHONE-S20-128GB-B","originalPriceWithTax": "2799.99","originalPriceWithoutTax": "2799.99","media": null,"quantity": 2,"tax": "23.00","productSet": null,"status": 1,"unit": "Szt.","type": 1,"productId": 12345},{"id": 2,"idExternal": null,"ean": null,"sku": "ship-pp","originalName": "Wysyłka - Poczta Polska - Pocztex","originalCode": null,"originalPriceWithTax": "10.00","originalPriceWithoutTax": "10.00","media": null,"quantity": 1,"tax": null,"productSet": null,"status": 1,"unit": null,"type": 2,"productId": null}],"orderPayments": [{"idExternal": "PAY-123456","amount": 1259.98,"paymentDate": "2022-03-08T20:00:00Z","type": 1,"comment": "Komentarz do wpłaty"}],"addressCustomer": {"name": "Jan Kowalski","phone": "+48 500 000 000","email": "jan.kowalski@apilo.com","streetName": "Testowa","streetNumber": "4b/12","city": "Kraków","zipCode": "31-154","country": "PL","parcelIdExternal": "KRA32B","parcelName": "Paczkomat, ul. Testowa 12 (obok sklepu)","companyTaxNumber": "937-271-51-54","companyName": "Apilo Sp. z o.o."},"addressDelivery": {"name": "Jan Kowalski","phone": "+48 500 000 000","email": "jan.kowalski@apilo.com","streetName": "Testowa","streetNumber": "4b/12","city": "Kraków","zipCode": "31-154","country": "PL","parcelIdExternal": "KRA32B","parcelName": "Paczkomat, ul. Testowa 12 (obok sklepu)","companyTaxNumber": "937-271-51-54","companyName": "Apilo Sp. z o.o."},"addressInvoice": {"name": "Jan Kowalski","phone": "+48 500 000 000","email": "jan.kowalski@apilo.com","streetName": "Testowa","streetNumber": "4b/12","city": "Kraków","zipCode": "31-154","country": "PL","parcelIdExternal": "KRA32B","parcelName": "Paczkomat, ul. Testowa 12 (obok sklepu)","companyTaxNumber": "937-271-51-54","companyName": "Apilo Sp. z o.o."},"carrierAccount": 1,"orderNotes": [{"type": 2,"comment": "I'll ask for delivery next week at the earliest"}],"orderedAt": "2022-06-09T10:59:12+0100","status": 3}`

### Response samples

- 422
- 404
- 401
- 201
- 200

Content type

application/json

Copy

`{"id": "AA123456789"}`

## Get detailed order by given ID.

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

### Responses

200

Detailed order object

401

Authorization failed

404

Order not found

get/rest/api/orders/{id}/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"id": "AL231100017","status": 3,"idExternal": "WWW/341/2023","isInvoice": true,"customerLogin": "user123","paymentStatus": 2,"paymentType": 2,"originalCurrency": "PLN","originalAmountTotalWithoutTax": 1024.37,"originalAmountTotalWithTax": 1259.98,"originalAmountTotalPaid": 1259.98,"sendDateMin": "2022-03-07T00:00:00Z","sendDateMax": "2022-03-08T20:00:00Z","isEncrypted": false,"preferences": {"idUser": "user-12345"},"createdAt": "2022-06-09T10:59:12Z","updatedAt": "2022-06-09T10:59:12Z","orderItems": [{"id": 1,"idExternal": "359","ean": "400638133393","sku": "P44/3-T1.2","originalName": "Samsung Galaxy S20 Plus Black 128GB 5G","originalCode": "PHONE-S20-128GB-B","originalPriceWithTax": "2799.99","originalPriceWithoutTax": "2799.99","media": null,"quantity": 2,"tax": "23.00","productSet": null,"status": 1,"unit": "Szt.","type": 1,"productId": 12345},{"id": 2,"idExternal": null,"ean": null,"sku": "ship-pp","originalName": "Wysyłka - Poczta Polska - Pocztex","originalCode": null,"originalPriceWithTax": "10.00","originalPriceWithoutTax": "10.00","media": null,"quantity": 1,"tax": null,"productSet": null,"status": 1,"unit": null,"type": 2,"productId": null}],"orderPayments": [{"idExternal": "PAY-123456","amount": 1259.98,"paymentDate": "2022-03-08T20:00:00Z","type": 1,"comment": "Komentarz do wpłaty"}],"addressCustomer": {"id": 123,"name": "Jan Kowalski","phone": "+48 500 000 000","email": "jan.kowalski@apilo.com","streetName": "Testowa","streetNumber": "4b/12","city": "Kraków","zipCode": "31-154","country": "PL","department": "string","parcelIdExternal": "KRA32B","parcelName": "Paczkomat, ul. Testowa 12 (obok sklepu)","class": "company","companyTaxNumber": "937-271-51-54","companyName": "Apilo Sp. z o.o."},"addressDelivery": {"id": 123,"name": "Jan Kowalski","phone": "+48 500 000 000","email": "jan.kowalski@apilo.com","streetName": "Testowa","streetNumber": "4b/12","city": "Kraków","zipCode": "31-154","country": "PL","department": "string","parcelIdExternal": "KRA32B","parcelName": "Paczkomat, ul. Testowa 12 (obok sklepu)","class": "company","companyTaxNumber": "937-271-51-54","companyName": "Apilo Sp. z o.o."},"addressInvoice": {"id": 123,"name": "Jan Kowalski","phone": "+48 500 000 000","email": "jan.kowalski@apilo.com","streetName": "Testowa","streetNumber": "4b/12","city": "Kraków","zipCode": "31-154","country": "PL","department": "string","parcelIdExternal": "KRA32B","parcelName": "Paczkomat, ul. Testowa 12 (obok sklepu)","class": "company","companyTaxNumber": "937-271-51-54","companyName": "Apilo Sp. z o.o."},"carrierAccount": 1,"orderNotes": [{"id": 221,"type": 2,"createdAt": "2024-01-23T09:29:30+0100","comment": "I'll ask for delivery next week at the earliest"}],"orderedAt": "2022-06-09T10:59:12+0100","platformId": 1,"isCanceledByBuyer": false,"carrierId": 1,"platformAccountId": 1}`

## Get order default shipping settings.

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

### Responses

200

Default shipping settings object

401

Authorization failed

404

Order not found

422

'mappedDelivery' key is missing from input array

get/rest/api/orders/{id}/shipping-settings-defaults/

### Response samples

- 422
- 404
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

[https://client1000.apilo.com/admin/platform-account/mapping/1/1/](https://client1000.apilo.com/admin/platform-account/mapping/1/1/)

`{"mappedDelivery": {"carrierAccountId": "1","carrierMethod": "parcel_locker","_help": {"message": "You can change delivery mapping for this platform by visiting provided link.","href": ""}}}`

## Update order status.

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

##### Request Body schema: application/jsonrequired

status

required

integer (Status zamówienia.) >= 1

Status ID

### Responses

200

Change status correctly

304

No changes was made

400

Invalid status ID

401

Authorization failed

404

Order not found

put/rest/api/orders/{id}/status/

### Request samples

- Payload

Content type

application/json

Copy

`{"status": 3}`

### Response samples

- 404
- 401
- 400
- 304
- 200

Content type

application/json

Copy

`{"updates": "1"}`

## Add payment to Order.

Add payment to Orders

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

##### Request Body schema: application/jsonrequired

string [ 0 .. 64 ]

External payment ID

type

required

integer >= 1

Payment method ID

paymentDate

required

string or null 

Date of payment

amount

required

string or null [ 0.01 .. 9999999.99 ]

Amount of payment

string [ 0 .. 128 ] characters

| idExternal |
| --- |
| comment |

### Responses

200

Payment with the given idExternal already exists

201

Add payment correctly

401

Authorization failed

404

Order not found

post/rest/api/orders/{id}/payment/

### Request samples

- Payload

Content type

application/json

Copy

`{"idExternal": "PAY-123456","type": 1,"paymentDate": "2022-03-08T20:00:00Z","amount": 1259.98,"comment": "Credit card payment"}`

### Response samples

- 404
- 401
- 201
- 200

Content type

application/json

Copy

`[ ]`

## Order Binary document.

Binary contents of the document (or shipment label) file belongs to the specified order

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

document

required

string >= 1 \d+

ID of the document or shipment belongs to the Apilo order

### Responses

200

Binary content

401

Authorization failed

404

Media not found

get/rest/api/orders/{id}/media/{document}/

### Response samples

- 404
- 401

Content type

application/json

Copy

Expand all Collapse all

`{"message": "string","code": 0,"description": "string","errors": [{ }],"field": "string"}`

## Get simple list of documents for given order.

List of documents belongs to the indicated order

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

##### query Parameters

number >= 1

ID of the document

string <= 36 characters

External unique ID of the document

integer

External document number

integer

Document type - order document types endpoint

string^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

start date of document creation in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

string^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

end date of document creation in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

number >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

number [ 1 .. 512 ]

Limit of returned results, max 512 records

| id |
| --- |
| idExternal |
| number |
| type |
| createdAfter |
| createdBefore |
| offset |
| limit |

### Responses

200

Order document array

401

Authorization failed

get/rest/api/orders/{id}/documents/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"documents": [{"id": 1,"idExternal": "1","number": "FV/1/12/2020","priceWithTax": "123.00","priceWithoutTax": "100.00","currency": "PLN","currencyValue": "1.000","type": 16,"createdAt": "2023-11-24TT08:33:07+0100"}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Create document for order.

Create document for order

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

##### Request Body schema: application/jsonrequired

idExternal

required

string or null [ 1 .. 36 ] characters

External unique ID of the document - used for the update

string or null [ 1 .. 64 ] characters

External document number

string or null [ -99999999.99 .. 99999999.99 ]

The gross value

string or null [ -99999999.99 .. 99999999.99 ]

The net value

string or null (Currency type.) = 3 characters

Currency on the document

string or null [ -9999.9999 .. 9999.9999 ]

Currency exchange rate

type

required

integer or null (Enum document type, default 16.)

Document type - order document types endpoint

string (ID obtained after sending Media.)

Null or media UUID - media attachment endpoint

| number |
| --- |
| priceWithTax |
| priceWithoutTax |
| currency |
| currencyValue |
| media |

### Responses

200

Order document with the given idExternal already exists

201

Create document correctly

401

Authorization failed

404

Order not found

422

Validation fail

post/rest/api/orders/{id}/documents/

### Request samples

- Payload

Content type

application/json

Copy

`{"idExternal": "1","number": "FV/1/12/2020","priceWithTax": "123.00","priceWithoutTax": "100.00","currency": "PLN","currencyValue": "1.000","type": 16,"media": "2ed996a6-0b91-529c-9728-f2e59532e7bc"}`

### Response samples

- 422
- 404
- 401
- 201
- 200

Content type

application/json

Copy

`{"id": 1,"idExternal": "1","number": "FV/1/12/2020","priceWithTax": "123.00","priceWithoutTax": "100.00","currency": "PLN","currencyValue": "1.000","type": 16,"media": "2ed996a6-0b91-529c-9728-f2e59532e7bc","createdAt": "2023-11-24TT08:33:07+0100"}`

## Order Document detail.

Get detailed document by Id for given Order

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

document

required

string >= 1 \d+

ID of the document belongs to the Apilo order

### Responses

200

Order document model

401

Authorization failed

404

Document or Order not found

get/rest/api/orders/{id}/documents/{document}/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

`{"id": 1,"idExternal": "1","number": "FV/1/12/2020","priceWithTax": "123.00","priceWithoutTax": "100.00","currency": "PLN","currencyValue": "1.000","type": 16,"media": "2ed996a6-0b91-529c-9728-f2e59532e7bc","createdAt": "2023-11-24TT08:33:07+0100"}`

## Delete document for given order.

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

document

required

string >= 1 [0-9]+

ID of the document belongs to the Apilo order

### Responses

200

Delete document correctly

401

Authorization failed

404

Document not found

delete/rest/api/orders/{id}/documents/{document}/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

`[ ]`

## Get document types map.

Document types map

##### Authorizations:

BearerAuth

### Responses

200

Returns document types map

401

Authorization failed

get/rest/api/orders/documents/map/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`[{"id": 2,"key": "E_INVOICE","name": "Faktura sprzedaży","description": "Faktura sprzedaży","isBroker": null}]`

## Get Payment types list.

Get Payment types list

##### Authorizations:

BearerAuth

### Responses

200

Returns list of Payment type objects

401

Authorization failed

get/rest/api/orders/payment/map/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`[{"id": 1,"key": "PAYMENT_TYPE_BANK_TRANSFER","name": "Przelew bankowy","description": "przelew bankowy"},{"id": 2,"key": "PAYMENT_TYPE_COD","name": "Pobranie","description": "za pobraniem"},{"id": 3,"key": "PAYMENT_TYPE_SERVICE_PAYU","name": "PayU","description": "serwis PayU"}]`

## Get order Status types list.

Get Order Status types list

##### Authorizations:

BearerAuth

### Responses

200

Returns list of order Status objects

401

Authorization failed

get/rest/api/orders/status/map/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`[{"id": 7,"key": "STATUS_7","name": "Nowy","description": "Nowy"},{"id": 8,"key": "STATUS_8","name": "Niepotwierdzone","description": "Niepotwierdzone"},{"id": 9,"key": "STATUS_9","name": "W realizacji","description": "W realizacji"}]`

## Get list of Carrier.

##### Authorizations:

BearerAuth

### Responses

200

Returns list of Carrier objects

401

Authorization failed

get/rest/api/orders/carrier/map/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`[{"id": 3,"key": "CARRIER_253","name": "Inpost (Kurier, Paczkomaty, Allegro)","description": ""},{"id": 143,"key": "CARRIER_258","name": "Wysyłam z Allegro","description": ""},{"id": 5,"key": "CARRIER_257","name": "Poczta Polska","description": ""}]`

## Get Carrier Account list.

Get Carrrier Account List

##### Authorizations:

BearerAuth

### Responses

200

Returns list of Carrier Account objects

401

Authorization failed

get/rest/api/orders/carrier-account/map/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`[{"id": 22,"key": "CARRIER_ACCOUNT_143_22","name": "AllegroBroker Minipaczka","description": "Wysyłam z Allegro"},{"id": 23,"key": "CARRIER_ACCOUNT_143_23","name": "DPD PL - nowa umowa","description": "DPD Polska"},{"id": 15,"key": "CARRIER_ACCOUNT_3_15","name": "Inpost","description": "Inpost (Kurier, Paczkomaty, Allegro"}]`

## Get Platform list.

Get Platform list

##### Authorizations:

BearerAuth

### Responses

200

Returns list of Platform object

401

Authorization failed

get/rest/api/orders/platform/map/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`[{"id": 44,"key": "PLATFORM_ALLEGRO_44","name": "Allegro","description": "Allegro jankowalski"},{"id": 92,"key": "PLATFORM_AMAZON_92","name": "Amazon","description": "Amazon 4x kowalski janek"},{"id": 101,"key": "PLATFORM_EMPIK_101","name": "Empik","description": "Empik jan.kowalski@apilo.com"}]`

## Tag list.

List of tag

##### Authorizations:

BearerAuth

### Responses

200

Returns list of tag

401

Authorization failed

get/rest/api/orders/tag/map/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`[{"id": 9,"key": "TAG_9","name": "BezFV","description": "Bez faktury, kolor: purple-soft"},{"id": 5,"key": "TAG_5","name": "DR","description": "Do realizacji, kolor: purple-studio"},{"id": 8,"key": "TAG_8","name": "FV","description": "Klient chce fakturę, kolor: yellow-mint"}]`

## Get order notes.

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

### Responses

200

List of order notes

401

Authorization failed

404

Invalid platform ID

get/rest/api/orders/{id}/note/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

`{"type": 2,"createdAt": "2024-01-23T09:29:30+0100","comment": "I'll ask for delivery next week at the earliest"}`

## Add note to order.

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

##### Request Body schema: application/json

integer (1 - Message from client, 2 - Internal note.)

Default: 1

Enum: 1 2

Type of the note

comment

required

string <= 1024 characters

Note content

| type |
| --- |

### Responses

201

Order note created correctly

401

Authorization failed

404

Invalid platform ID

422

Validation error

post/rest/api/orders/{id}/note/

### Request samples

- Payload

Content type

application/json

Copy

`{"type": 2,"comment": "I'll ask for delivery next week at the earliest"}`

### Response samples

- 422
- 404
- 401
- 201

Content type

application/json

Copy

`[ ]`

## List of order shipments.

List of shipments belongs to the indicated order

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

##### query Parameters

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| offset |
| --- |
| limit |

### Responses

200

Shipments array

401

Authorization failed

get/rest/api/orders/{id}/shipment/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"list": [{"id": 1,"idExternal": "SH300021044869"},{"id": 2,"idExternal": "SH300021044870"},{"id": 3,"idExternal": "SH300021044871"}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Add shipment to order.

Shipment is created as order document, it can be see from here

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

##### Request Body schema: application/jsonrequired

string or null [ 0 .. 36 ] characters

External unique ID of the shipment

tracking

required

string [ 1 .. 64 ] characters

Shipment tracking number

carrierProviderId

required

integer

ID of Carrier ID. If you specify a value equal to 'manual carrier', there might be problems in passing the tracking number to the external integration.

string or null (DateTime format.)

Date of shipment

string

Null or media UUID - media attachment endpoint

| idExternal |
| --- |
| postDate |
| media |

### Responses

200

Shipment already exsists

201

Add shipment correctly

400

Courier account is not configuret yet

401

Authorization failed

422

Validation error

post/rest/api/orders/{id}/shipment/

### Request samples

- Payload

Content type

application/json

Copy

`{"idExternal": "312","tracking": "005842792564T","carrierProviderId": 1,"postDate": "2022-06-09T10:59:12+0100","media": "2ed996a6-0b91-529c-9728-f2e59532e7bc"}`

### Response samples

- 422
- 401
- 400
- 201
- 200

Content type

application/json

Copy

`{"id": 1,"idExternal": "312","tracking": "005842792564T","carrierProviderId": 1,"postDate": "2022-06-09T10:59:12+0100","media": "2ed996a6-0b91-529c-9728-f2e59532e7bc","status": 2}`

## Shipment detail.

Detail of specific shipment belongs to given order

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string [ 10 .. 11 ] characters ^[A-Za-z0-9\.|]{10,11}$

order number in Apilo system, e.g.`AL0012345`

shipment

required

string\d+

ID of the shipment belongs to the Apilo order

### Responses

200

Shipment model

401

Authorization failed

404

Document or Order not found

get/rest/api/orders/{id}/shipment/{shipment}/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

`{"id": 1,"idExternal": "312","tracking": "005842792564T","carrierProviderId": 1,"postDate": "2022-06-09T10:59:12+0100","media": "2ed996a6-0b91-529c-9728-f2e59532e7bc","status": 2}`

## Get shipment status map.

Shipment status map

##### Authorizations:

BearerAuth

### Responses

200

Returns shipment status map

401

Authorization failed

get/rest/api/orders/shipment/status/map/

### Response samples

- 200

Content type

application/json

Copy

Expand all Collapse all

`[{"id": "3","key": "CARRIER_253","name": "Inpost (Kurier, Paczkomaty, Allegro)","description": "Kurier"}]`

## Order tags list.

Order tags list

##### Authorizations:

BearerAuth

##### path Parameters

orderId

required

string

Order ID

##### query Parameters

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| offset |
| --- |
| limit |

### Responses

200

Returns list of order tags

401

Authorization failed

404

Order not found

get/rest/api/orders/{orderId}/tag/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"list": [{"id": "1","alias": "aliasExample","name": "name","color": "blue"}],"pageResultCount": "1","totalCount": "512","currentOffset": "0"}`

## Create order tag.

Create order tag

##### Authorizations:

BearerAuth

##### path Parameters

orderId

required

string

Order ID

##### Request Body schema: application/jsonrequired

tag

required

integer

Tag ID

### Responses

201

Create order tag correctly

304

No changes was made

401

Authorization failed

404

Order or tag not exist

post/rest/api/orders/{orderId}/tag/

### Request samples

- Payload

Content type

application/json

Copy

`{"tag": 1}`

### Response samples

- 404
- 401
- 304
- 201

Content type

application/json

Copy

`[ ]`

## Delete order tag.

Delete order tag

##### Authorizations:

BearerAuth

##### path Parameters

orderId

required

string

Order ID

tagId

required

string

Tag ID

### Responses

200

Delete order tag correctly

401

Authorization failed

404

Order tag not found

delete/rest/api/orders/{orderId}/tag/{tagId}/

### Response samples

- 404
- 401

Content type

application/json

Copy

Expand all Collapse all

`{"message": "string","code": 0,"description": "string","errors": [{ }],"field": "string"}`

## Warehouse

Warehouse manager - product, price, quantity

## Attribute List.

List of attributes

##### Authorizations:

BearerAuth

##### query Parameters

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| offset |
| --- |
| limit |

### Responses

200

Attributes array

401

Authorization failed

get/rest/api/warehouse/attribute/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"attributes": [{"id": 30,"type": 1,"name": "Manufacturer code","attributeFeatures": null},{"id": 31,"type": 17,"name": "Color","attributeFeatures": [{"id": 12,"value": "Red"},{"id": 13,"value": "Blue"},{"value": "Black"}]},{"id": 32,"type": 16,"name": "Materials","attributeFeatures": [{"id": 15,"value": "Plastic"},{"id": 16,"value": "Metal"}]}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Attribute create.

##### Authorizations:

BearerAuth

##### Request Body schema: application/json

attributes

required

Array of objects (List of Attributes.)

Attribute items list

### Responses

200

Nothing to create

201

Create attributes correctly

401

Authorization failed

422

Validation error

post/rest/api/warehouse/attribute/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"attributes": [{"id": 123,"type": 1,"name": "test1","values": [{"id": 1,"value": "test"}]},{"id": 123,"type": 16,"name": "test1","values": [{"id": 10,"value": "test"},{"id": 11,"value": "test"}]}]}`

### Response samples

- 422
- 401
- 201
- 200

Content type

application/json

Copy

`[ ]`

## Attribute update.

##### Authorizations:

BearerAuth

##### Request Body schema: application/json

```
Typ Wielu Wartości:
1 W celu utworzenia nowej wartości, wymagana jest podanie parametru attributeFeatures.id jako null,
2 W celu aktualicji istniejącej wartości wymagane jest podanie parametru attributeFeatures.id jako wartośc i podanie parametru value.
3 Nie podanie wartości, które powinny być zachowane, spowoduje ich usunięcie

```

attributes

required

Array of objects (List of Attributes.)

Attribute items list

### Responses

200

Attributes update correctly

401

Authorization failed

422

Validation error

patch/rest/api/warehouse/attribute/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"attributes": [{"id": 123,"type": 1,"name": "test1","values": [{"id": 1,"value": "test"}]},{"id": 123,"type": 16,"name": "test1","values": [{"id": 10,"value": "test"},{"id": 11,"value": "test"}]}]}`

### Response samples

- 422
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"attributes": [{"id": 123,"type": 1,"name": "test1","values": [{"id": 1,"value": "test"}]},{"id": 123,"type": 16,"name": "test1","values": [{"id": 10,"value": "test"},{"id": 11,"value": "test"}]}]}`

## Product attribute list.

list of product attributes

##### Authorizations:

BearerAuth

##### query Parameters

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| offset |
| --- |
| limit |

### Responses

200

Attributes array

401

Authorization failed

get/rest/api/warehouse/product/attributes/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"attributes": [{"id": 30,"type": 1,"name": "Manufacturer code","attributeFeatures": null},{"id": 31,"type": 16,"name": "Color","values": [{"id": 12},{"id": 13}]},{"id": 32,"type": 9,"name": "Materials","values": [{"id": 15,"value": "Plastic"},{"id": 16,"value": "Metal"}]},{"id": 33,"type": 1,"name": "Material","values": [{"id": 17,"value": "Plastic"}]},{"id": 34,"type": 2,"name": "IsMaterial","values": [{"id": 18,"value": false}]}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Product Attributes Delete.

Delete a product attributes

##### Authorizations:

BearerAuth

##### Request Body schema: application/jsonrequired

attributes

required

Array of objects (RestProductAttributeDTO2)

Product Attribute items list

### Responses

204

Delete product attributes complete

401

Authorization failed

delete/rest/api/warehouse/product/attributes/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"attributes": [{"id": 321,"productId": 462,"type": 1,"values": [{"id": 123}]}]}`

### Response samples

- 401
- 204

Content type

application/json

Copy

`[ ]`

## Product Attribute update.

Update a product attributes

##### Authorizations:

BearerAuth

##### Request Body schema: application/jsonrequired

Product Attributes

attributes

required

Array of objects (RestProductAttributeDTO3)

Product Attribute items list

### Responses

200

Product Attributes updated successfully

422

Validation error

patch/rest/api/warehouse/product/attributes/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"attributes": [{"id": 321,"productId": 462,"type": 1,"values": [{"value": "test","id": 123}]}]}`

### Response samples

- 422
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"attributes": [{"id": 30,"type": 1,"name": "Manufacturer code","attributeFeatures": null},{"id": 31,"type": 16,"name": "Color","values": [{"id": 12},{"id": 13}]},{"id": 32,"type": 9,"name": "Materials","values": [{"id": 15,"value": "Plastic"},{"id": 16,"value": "Metal"}]},{"id": 33,"type": 1,"name": "Material","values": [{"id": 17,"value": "Plastic"}]},{"id": 34,"type": 2,"name": "IsMaterial","values": [{"id": 18,"value": false}]}]}`

## Products Media list.

List of Product media

##### Authorizations:

BearerAuth

##### query Parameters

boolean

Array of integers

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| onlyMain |
| --- |
| productIds[] |
| offset |
| limit |

### Responses

200

Product media list

401

Authorization failed

422

Validation error

get/rest/api/warehouse/product/media/

### Response samples

- 422
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"media": [{"id": 0,"isMain": true,"productId": 0,"uuid": "string","extension": "string","link": "string"}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Categories list.

##### Authorizations:

BearerAuth

##### query Parameters

integer

Internal Apilo Id for category

integer >= 0

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records)

integer [ 1 .. 512 ]

Limit of returned results, max 512 records

| id |
| --- |
| offset |
| limit |

### Responses

200

Returns simple list of categories

get/rest/api/warehouse/category/

### Response samples

- 200

Content type

application/json

Copy

Expand all Collapse all

`{"categories": [{"id": "1","name": "Category name","parentIds": [1,2]}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Category create.

##### Authorizations:

BearerAuth

##### Request Body schema: application/jsonrequired

Category Creation

name

required

string (Category name.)

integer or null (Category parent Apilo ID or null.)

integer or null (Category sort parameter or null.)

| parentId |
| --- |
| sort |

### Responses

200

Nothing to create

201

Create categories correctly

401

Authorization failed

413

Too many Category objects submitted (max 512)

422

Validation error

post/rest/api/warehouse/category/

### Request samples

- Payload

Content type

application/json

Copy

`{"name": "Kategoria 1","parentId": 38,"sort": 2}`

### Response samples

- 422
- 413
- 401
- 201
- 200

Content type

application/json

Copy

`[ ]`

## Products list.

##### Authorizations:

BearerAuth

##### query Parameters

integer

string

string

string

any

Enum: 0 1 8

Product status (`0-inactive`,`1-active`,`8-archive`)

integer

Position indicator (0-beginning, 1-skips one record, 256 - skips 256 records), max 2000 records

integer

Limit of returned results

| id |
| --- |
| sku |
| name |
| ean |
| status |
| offset |
| limit |

### Responses

200

Returns simple list of products

get/rest/api/warehouse/product/

### Response samples

- 200

Content type

application/json

Copy

Expand all Collapse all

`{"products": [{"name": "Samsung Galxy S20 Plus Black 128GB","unit": "string","weight": 1.12,"priceWithoutTax": 100,"sku": "HG-331/P","ean": "4006381333931","id": 1234,"originalCode": "p12345","quantity": 15,"priceWithTax": 123,"tax": "23.00","status": 1}],"totalCount": 0}`

## Products data update.

Uwaga: Pole groupName jest deprecated i zostanie usunięte w przyszłości, Zamiast niego należy używać pola name, ponieważ obecnie obsługuje ono oba wymagania dotyczące nazewnictwa produktów.

##### Authorizations:

BearerAuth

##### Request Body schema: application/json

```
Aktualizacja danych identyfikacyjnych produktu możliwa jest wg. następujących zasad:
● Nie można dokonać zmiany pól id oraz originalCode ,
● Wypełniając pole id lub originalCode można dokonać aktualizacji wszystkich
pozostałych danych identyfikacyjnych (w tym sku oraz ean),
● nie przekazując pól id oraz originalCode można dokonać aktualizacji tylko danych
nie identyfikacyjnych produktu (za wyjątkiem ean)

```

Array

id

required

integer (Product ID in Apilo system.)

sku

required

string (SKU/Unique product ID.)

string (Product name.)

tax

required

string

status

required

integer

Enum: 0 1

string (Unique external ID, e.g. ID from external database.)

string (Product group name - fill this field when you want to set both product group name and product name. Deprecated please use the field name instead.)

Deprecated

Array of strings

Array of attribute ID

Array of strings <^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$> (UUID.) [ items <^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ > ]

Array of UUID uploaded media via Attachment endpoint or associative array of image URL - key attribute is reference

Array of integers[ items >= 1 ]

Array of category ID

string (European Article Number.)

quantity

required

integer ( Product inventory)

priceWithTax

required

string ( Product price including VAT)

number ( Product weight)

string ( Unit of measure)

string [ 1 .. 65535 ] characters

Long product description

string

Short product description, max 256 characters

| name |
| --- |
| originalCode |
| groupName |
| attributes |
| images |
| categories |
| ean |
| weight |
| unit |
| description |
| shortDescription |

### Responses

200

Update product correctly

304

No updates

400

Invalid payload

401

Authorization failed

413

Too many Product objects submitted (max 128)

422

Validation error

put/rest/api/warehouse/product/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

[https://example.com/images/example.jpg](https://example.com/images/example.jpg)

`[{"id": 341,"sku": "IT-005/C","name": "Samsung Galaxy S20 G980F Dual SIM Blue","tax": "23","status": 1,"originalCode": "46","groupName": null,"attributes": {"4": 5,"5": "Samsung"},"images": {"0": "2ed996a6-0b91-529c-9728-f2e59532e7bc","1": "1a1233cf-b69d-7f27-211e-36aff9ec373a","ref2": ""},"categories": [33,44,55],"ean": "0400638133393","quantity": 350,"priceWithTax": 100,"weight": 0.45,"unit": "KG","description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum dignissim, eros quis consectetur tincidunt, diam leo convallis ligula.","shortDescription": ""}]`

### Response samples

- 422
- 413
- 401
- 400
- 304
- 200

Content type

application/json

Copy

`{"updated": 1}`

## Products create.

Uwaga: Pole groupName jest deprecated i zostanie usunięte w przyszłości, Zamiast niego należy używać pola name, ponieważ obecnie obsługuje ono oba wymagania dotyczące nazewnictwa produktów.

##### Authorizations:

BearerAuth

##### Request Body schema: application/jsonrequired

```
1 Ponieważ pojedynczy produkt tworzony jest w systemie Apilo zawsze jako grupa
produktów z jedną kombinacją produktu, domyślnie nazwa grupy jest również nazwą
produktu. Aby “sterować” nazwą grupy produktów należy wypełnić dodatkowe pole o nazwie
groupName (np. groupName=Rolki agresywne EXTREM II name=Kolor niebieski

2 Przekazana tablica zdjęć może być tablicą asocjacyjną gdzie kluczem jest zewnętrzny
identyfikator zdjęcia (przydatne przy aktualizacji produktu - zostaną dodane tylko
nieistniejące pozycje w systemie Apilo), a wartością adres URL zdjęcia.
 * 

```

Array

string (Unique external ID, e.g. ID from external database.)

string (Product name.)

sku

required

string (SKU/Unique product ID.)

quantity

required

integer ( Product inventory)

priceWithTax

required

string ( Product price including VAT)

tax

required

string

status

required

integer

Enum: 0 1

string (Product group name - fill this field when you want to set both product group name and product name. Deprecated please use the field name instead.)

Deprecated

Array of strings

Array of attribute ID

Array of strings <^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$> (UUID.) [ items <^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ > ]

Array of UUID uploaded media via Attachment endpoint or associative array of image URL - key attribute is reference

Array of integers[ items >= 1 ]

Array of category ID

string (European Article Number.)

number ( Product weight)

string ( Unit of measure)

string [ 1 .. 65535 ] characters

Long product description

string

Short product description, max 256 characters

| originalCode |
| --- |
| name |
| groupName |
| attributes |
| images |
| categories |
| ean |
| weight |
| unit |
| description |
| shortDescription |

### Responses

200

No products was created

201

Create products correctly

400

Invalid payload

413

Too many Product objects submitted (max 128)

422

Validation error

post/rest/api/warehouse/product/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

[https://example.com/images/example.jpg](https://example.com/images/example.jpg)

`[{"originalCode": "46","name": "Samsung Galaxy S20 G980F Dual SIM Blue","sku": "IT-005/C","quantity": 350,"priceWithTax": 100,"tax": "23","status": 1,"groupName": null,"attributes": {"4": 5,"5": "Samsung"},"images": {"0": "2ed996a6-0b91-529c-9728-f2e59532e7bc","1": "1a1233cf-b69d-7f27-211e-36aff9ec373a","ref2": ""},"categories": [33,44,55],"ean": "0400638133393","weight": 0.45,"unit": "KG","description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum dignissim, eros quis consectetur tincidunt, diam leo convallis ligula.","shortDescription": ""}]`

### Response samples

- 422
- 413
- 400
- 201
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"products": [ ]}`

## Products PATCH update.

##### Authorizations:

BearerAuth

##### Request Body schema: application/json

Maksymalnie 512 rekordów, aktualizacja po id lub originalCode

Array

integer

Internal product ID in Apilo

string or null

External product identifier (unambiguous against API/channel)

integer

Product stock

string

Gross price

string

VAT rate (e.g. 23.00, -1.00 - tax exempt).

integer or null (status produktu)

Enum: 0 1 8

Product status (`0-inactive`,`1-active`,`8-archive`)

string or null

Product SKU

| id |
| --- |
| originalCode |
| quantity |
| priceWithTax |
| tax |
| status |
| sku |

### Responses

200

Update products correctly

304

No updates

400

Invalid payload

401

Authorization failed

413

Too many Product objects submitted (max 128)

422

Validation error

patch/rest/api/warehouse/product/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`[{"id": 1234,"originalCode": "p12345","quantity": 15,"priceWithTax": 123,"tax": "23.00","status": 1,"sku": "HG-331/P"}]`

### Response samples

- 422
- 413
- 401
- 400
- 304
- 200

Content type

application/json

Copy

`{"changes": 10}`

## Get Product detail.

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string\d+

### Responses

200

Returns detailed Product object

401

Authorization failed

404

Product not found

get/rest/api/warehouse/product/{id}/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"name": "BLACK 128GB","groupName": "Samsung Galxy S20 Plus","productGroupId": 123456,"categories": [12,44,149],"unit": "string","weight": 1.12,"priceWithoutTax": 100,"sku": "HG-331/P","ean": "4006381333931","id": 1234,"originalCode": "p12345","quantity": 15,"priceWithTax": 123,"tax": "23.00","status": 1}`

## Delete Product.

Delete Product

##### Authorizations:

BearerAuth

##### path Parameters

id

required

string\d+

### Responses

200

Delete product correctly

401

Authorization failed

404

Product not found

delete/rest/api/warehouse/product/{id}/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

`[ ]`

## Prices list.

List of prices

##### Authorizations:

BearerAuth

##### query Parameters

price

required

integer

Price list ID

integer

Start on record

integer

Limit of returned results, max 2000 records

| offset |
| --- |
| limit |

### Responses

200

Returns list of prices

401

Authorization failed

404

Prices not found

get/rest/api/warehouse/price-calculated/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"list": [{"id": 1,"price": 12,"product": 3,"customPriceWithTax": 14.9,"customPriceModify": 10,"customMode": 7}],"totalCount": 0}`

## Price create and update.

Create/update product price

##### Authorizations:

BearerAuth

##### Request Body schema: application/jsonrequired

product

required

integer

Unique product ID

price

required

integer

Unique price list ID

customPriceModify

required

number or integer or string

Custom price modify

customMode

required

integer

Enum: 3 5 6 7

```
3 - fixed - use to set direct price
5 - overhead - use to add/sub percentage to base price
6 - margin - use to set percent margin to base price (max 99.99)
7 - static - use to add/sub static value to base price
 

```

### Responses

201

Create/update price correctly

401

Authorization failed

422

Create/Update/Validation price failed

post/rest/api/warehouse/price-calculated/

### Request samples

- Payload

Content type

application/json

Copy

`{"product": 11,"price": 12,"customPriceModify": 11.12,"customMode": 3}`

### Response samples

- 422
- 401
- 201

Content type

application/json

Copy

`{"id": 0}`

## Delete price.

Delete product price

##### Authorizations:

BearerAuth

##### path Parameters

product

required

string >= 1

Unique product ID

price

required

string >= 1

Unique price list ID

### Responses

200

Delete price correctly

401

Authorization failed

404

Price not found

500

Delete price failed

delete/rest/api/warehouse/price-calculated/{product}/{price}/

### Response samples

- 500
- 404
- 401
- 200

Content type

application/json

Copy

`[ ]`

## Price lists.

List of price lists

##### Authorizations:

BearerAuth

### Responses

200

Returns list of price lists

401

Authorization failed

404

Price lists not found

get/rest/api/warehouse/price/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"list": [{"id": 1,"name": "Cennik"}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Sale

Sale

## Get list of sales channels.

##### Authorizations:

BearerAuth

### Responses

200

Return list of sales channels

401

Authorization failed

get/rest/api/sale/

### Response samples

- 401
- 200

Content type

application/json

Copy

`[ ]`

## Get auctions list.

##### Authorizations:

BearerAuth

### Responses

200

Returns list of auctions

401

Authorization failed

get/rest/api/sale/auction/

### Response samples

- 401
- 200

Content type

application/json

Copy

`[ ]`

## Media

Media attachment management

## Create new media attachment.

Create new media attachment

##### Authorizations:

BearerAuth

##### header Parameters

string

Extra file parameters (e.g. 'Content-Disposition: filename=invoice.pdf')

| Content-Disposition |
| --- |

##### Request Body schema: application/octet-streamrequired

You can create new media attachment for files with type application/pdf, image/jpeg, image/png, image/gif, image/webp

string 

### Responses

201

Create attachment correctly

401

Authorization failed

415

Invalid file type

422

Validation error

post/rest/api/media/

### Response samples

- 422
- 415
- 401
- 201

Content type

application/json

Copy

`{"uuid": "2ed996a6-0b91-529c-9728-f2e59532e7bc","name": "Invoice-22-12-2020.pdf","type": "application/pdf","expiresAt": "2022-03-08T20:00:00Z"}`

## Get media.

##### path Parameters

uuid

required

string[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F...Show pattern

UUID Media

### Responses

200

Binary Content

401

Authorization failed

404

Media not found

get/rest/api/media/{uuid}/

### Response samples

- 404
- 401

Content type

application/json

Copy

Expand all Collapse all

`{"message": "string","code": 0,"description": "string","errors": [{ }],"field": "string"}`

## Shipment

Shipment management

## Get detailed shipment by given ID.

##### path Parameters

id

required

string(\d+)

Shipment ID

### Responses

200

Detailed shipment object

401

Authorization failed

404

Shipment not found

get/rest/api/shipping/shipment/{id}/

### Response samples

- 404
- 401
- 200

Content type

application/json

Copy

`{"statusDate": "2023-11-24T08:33:07+0100","statusDescription": "readyToSend","statusCheckTimestamp": "2023-11-24T08:33:07+0100","receivedDate": "2023-11-24T08:33:07+0100","receivedDays": 2,"id": "123","carrierAccountId": "123","carrierBrokerId": "123","externalId": "312","orderId": "123","createdAt": "2023-11-24T08:33:07+0100","postDate": "2022-06-09T10:59:12+0100","status": 2,"method": "312","media": "2ed996a6-0b91-529c-9728-f2e59532e7bc"}`

## Get list of shipments for given filters.

##### query Parameters

Array of integers

Carrier account IDs

Array of integers

Carrier broker IDs

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of shipment creation from in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of shipment creation from in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

Array of integers

Items Enum: 0 1 2 21 9 31 32 100 101

Status of shipment (0 - New parcel, not yet shipped, 1 - The parcel is waiting in the waiting room, it has not been sent, 2 - A new parcel, registered in the courier's system but does not have a status yet, 21 - Package in delivery, 9 - Package removed, 31 - The parcel is waiting for collection (collection point, notice), 32 - Return of the parcel to the sender, other error, 100 - Parcel received, 101 - Return parcel delivered)

| carrierAccountId[] |
| --- |
| carrierBrokerId[] |
| postDateAfter |
| postDateBefore |
| status[] |

### Responses

200

Returns list of shipments

401

Authorization failed

get/rest/api/shipping/shipment/info/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"shipments": [{"id": "123","carrierAccountId": "123","carrierBrokerId": "123","externalId": "312","orderId": "123","createdAt": "2023-11-24T08:33:07+0100","postDate": "2022-06-09T10:59:12+0100","status": 2,"method": "312","media": "2ed996a6-0b91-529c-9728-f2e59532e7bc"}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Get a list of shipments tracking information for given filters.

List of shipments tracking

##### query Parameters

Array of integers

Carrier account IDs

Array of integers

Carrier broker IDs

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of shipment creation from in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of shipment creation from in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date by which the shipment was delivered, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date from which the shipment was delivered, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

Array of integers

Items Enum: 0 1 2 21 9 31 32 100 101

Status of shipment (0 - New parcel, not yet shipped, 1 - The parcel is waiting in the waiting room, it has not been sent, 2 - A new parcel, registered in the courier's system but does not have a status yet, 21 - Package in delivery, 9 - Package removed, 31 - The parcel is waiting for collection (collection point, notice), 32 - Return of the parcel to the sender, other error, 100 - Parcel received, 101 - Return parcel delivered)

| carrierAccountId[] |
| --- |
| carrierBrokerId[] |
| postDateAfter |
| postDateBefore |
| receivedDateAfter |
| receivedDateBefore |
| status[] |

### Responses

200

Returns list of shipments

401

Authorization failed

get/rest/api/shipping/shipment/tracking/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"shipments": [{"id": "123","externalId": "312","status": 2,"statusDate": "2023-11-24T08:33:07+0100","statusDescription": "Handed over to the courier","statusCheckTimestamp": "2023-11-24T08:33:07+0100","receivedDate": "2022-06-09T10:59:12+0100","receivedDays": "3"}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Get Carrier Account list.

Get Carrier Account List

### Responses

200

Returns list of Carrier Account

401

Authorization failed

422

Unprocessable Entity

get/rest/api/shipping/carrier-account/map/

### Response samples

- 422
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"carrierAccounts": [{"id": "3","key": "CARRIER_253","name": "Inpost (Kurier, Paczkomaty, Allegro)","description": "Kurier","options": {"isPickupInShipmentCreation": true,"isPickupInShipmentConfirmation": true,"isShipmentConfirmationRequired": true}}]}`

## Get Carrier sending methods.

##### path Parameters

id

required

string(\d+)

Carrier Account ID

### Responses

200

Returns list of Carrier Account sending methods

401

Authorization failed

404

Carrier Account not found

422

Unprocessable Entity

get/rest/api/shipping/carrier-account/{id}/method/

### Response samples

- 422
- 404
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"methods": [{"id": "parcel_locker","name": "Nadanie w paczkomacie"}]}`

## Get list of shipment option need to create new shipment.

List of shipment options need to create new shipment.

##### path Parameters

carrierAccountId

required

string(\d{1,5})

Carrier account ID

method

required

string

Delivery method

### Responses

200

Returns list of shipment options need to create new shipment.

401

Authorization failed

422

Unprocessable Entity

get/rest/api/shipping/carrier-account/{carrierAccountId}/method/{method}/map/

### Response samples

- 422
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"options": {"id": "options","type": "definition","label": "Shipping options","multiple": true,"properties": [{"id": "cod","type": "money","label": "Shipping COD"}],"required": ["cod","dropoffPoint"]},"parcels": {"id": "options","type": "definition","label": "Shipping options","multiple": true,"properties": [{"id": "cod","type": "money","label": "Shipping COD"}],"required": ["cod","dropoffPoint"]},"maxParcelsCount": "1"}`

## Creates a new shipment from the submitted data.

##### Request Body schema: application/jsonrequired

integer or null

Carrier account ID

(HouseAddressDTO (object or null)) or (CompanyAddressDTO (object or null)) or (ParcelAddressDTO (object or null))

string or null

Order ID

string or null 

Post date

string or null

Shipment methods can be downloaded from Get Carrier sending methods.

Array of RestShipmentOptionMoneyDTO (object) or RestShipmentOptionBooleanDTO (object) or RestShipmentOptionStringDTO (object) or RestShipmentOptionChoiceDTO (object) or RestShipmentOptionDimensionsDTO (object) or RestShipmentOptionIntegerDTO (object)

Options can be downloaded from Get list of shipment option need to create new shipment.

Array of objects (RestShipmentParcelDTO)

Options can be downloaded from Get list of shipment option need to create new shipment.

| carrierAccountId |
| --- |
| addressReceiver |
| orderId |
| postDate |
| method |
| options |
| parcels |

### Responses

200

Returns list of identifiers for created shipments.

401

Authorization failed

422

Unprocessable Entity

post/rest/api/shipping/shipment/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"carrierAccountId": "1","addressReceiver": {"type": "house","name": "Jan Kowalski","streetName": "Kwiatowa","streetNumber": "1","zipCode": "01-001","city": "Warszawa","country": "PL","phone": "48500600700","email": "jan.kowalski@poczta.op.pl"},"orderId": "MA123456789","postDate": "2024-07-14T13:41:18+00:00","method": "inpost_courier_standard","options": [{"id": "cod","type": "money","value": {"amount": "10000","currency": "PLN"}}],"parcels": [{"options": [{"id": "cod","type": "money","value": {"amount": "10000","currency": "PLN"}}]}]}`

### Response samples

- 422
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"shipments": [{"shipmentId": "123"}]}`

## Get list of shipment carrier documents.

List of carrier documents for carrier accounts

##### query Parameters

Array of integers

Carrier account IDs

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of shipment carrier document creation from in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

string ^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{...Show pattern

Date of shipment carrier document creation from in Apilo, takes the value of ISO 8601 date encoded to URL, e.g.`2022-03-01T14:40:33%2B0200`

| carrierAccountId[] |
| --- |
| createdAtAfter |
| createdAtBefore |

### Responses

200

Returns list of shipment carrier documents

401

Authorization failed

get/rest/api/shipping/carrier-document/

### Response samples

- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"documents": [{"id": "123","carrierAccountId": "123","createdAt": "2023-11-24T08:33:07+0100","type": 16,"media": "2ed996a6-0b91-529c-9728-f2e59532e7bc"}],"totalCount": 7398,"currentOffset": 0,"pageResultCount": 64}`

## Confirm shipment and order pickup.

##### Request Body schema: application/jsonrequired

shippingConfirmations

required

Array of objects (List of shipping confirmations.) [ 1 .. 128 ] properties

List of shipping confirmations

### Responses

201

Shipping confirmation created

400

The request body must contain at least one shipment confirmation

401

Authorization failed

413

The limit of 128 shipment confirmations has been exceeded

422

Validation error

post/rest/api/shipping/carrier-document/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"shippingConfirmations": [{"shipmentId": "123","type": "1","pickupId": "2024-06-12|09:00|18:00"}]}`

### Response samples

- 422
- 413
- 401
- 400
- 201

Content type

application/json

Copy

Expand all Collapse all

`{"shippingConfirmations": [{"id": "123","media": "2ed996a6-0b91-529c-9728-f2e59532e7bc","shipments": {"shipment": [{"id": 1},{"id": 2}]},"error": {"pickupError": true,"pickupErrorMessage": "The pickup date is not available","shippingConfirmationError": true,"shippingConfirmationErrorMessage": "Shipping confirmation already exists"}}]}`

## Get shipment pick up date proposal.

##### Request Body schema: application/json

shipments

required

Array of objects (List of shipment IDs.)

List of shipment IDs

### Responses

200

Pickup date proposals

401

Authorization failed

409

Validation error - Shipments are associated with different carrier accounts.

422

Validation error

post/rest/api/shipping/pickup-date-proposal/

### Request samples

- Payload

Content type

application/json

Copy

Expand all Collapse all

`{"shipments": {"shipment": [{"id": 1},{"id": 2}]}}`

### Response samples

- 422
- 409
- 401
- 200

Content type

application/json

Copy

Expand all Collapse all

`{"pickups": [{"shipmentId": "123","type": "1","pickupDate": [{"pickupId": "no_pickup"},{"pickupId": "working_days"},{"pickupId": "2024-06-12|09:00|18:00"},{"pickupId": "2023071210001300"}]}]}`