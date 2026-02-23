# API Mapping — SkanujFakture v1.0.0

Mapping of SkanujFakture API endpoints to Pinquark integrator endpoints.

## Base URL

| Environment | SkanujFakture API URL |
|------------|----------------------|
| Production | `https://skanujfakture.pl:8443/SFApi` |

## Authentication

| Aspect | SkanujFakture | Pinquark Integrator |
|--------|---------------|---------------------|
| Method | Basic Authentication (header `Authorization: Basic base64(login:password)`) | Configuration in `accounts.yaml` or env vars |
| Credentials | Login (email) + password | Stored in encrypted vault |

## Endpoints — Mapping

### Companies and entities

| SkanujFakture API | Pinquark Integrator | Method |
|-------------------|---------------------|--------|
| `/users/currentUser/companies` | `/companies?account_name=X` | GET |
| `/companies/{companyId}/companyEntities` | `/companies/{id}/entities?account_name=X` | GET |

### Documents

| SkanujFakture API | Pinquark Integrator | Method |
|-------------------|---------------------|--------|
| `/companies/{cId}/documents` | `/companies/{cId}/documents?account_name=X` | POST (upload) |
| `/companies/{cId}/documents/v2` | `/companies/{cId}/documents/v2?account_name=X` | POST (upload with type) |
| `/companies/{cId}/documents` | `/companies/{cId}/documents?account_name=X` | GET (list) |
| `/companies/{cId}/documents/simple` | `/companies/{cId}/documents/simple?account_name=X` | GET |
| `/companies/{cId}/documents/{dId}` | `/companies/{cId}/documents/{dId}?account_name=X` | PUT (update) |
| `/companies/{cId}/documents` | `/companies/{cId}/documents?account_name=X` | DELETE |
| `/companies/{cId}/documents/{dId}/file` | `/companies/{cId}/documents/{dId}/file?account_name=X` | GET |
| `/companies/{cId}/documents/{dId}/image` | `/companies/{cId}/documents/{dId}/image?account_name=X` | GET |

### Attributes

| SkanujFakture API | Pinquark Integrator | Method |
|-------------------|---------------------|--------|
| `/companies/{cId}/documents/{dId}/attributes` | `/companies/{cId}/documents/{dId}/attributes?account_name=X` | PUT |
| `/companies/{cId}/documents/{dId}/attributes` | `/companies/{cId}/documents/{dId}/attributes?account_name=X` | DELETE |

### Dictionaries (posting)

| SkanujFakture API | Pinquark Integrator | Method |
|-------------------|---------------------|--------|
| `/companies/{cId}/decrets?type=X` | `/companies/{cId}/dictionaries?type=X&account_name=Y` | GET |
| `/companies/{cId}/decrets?type=X` | `/companies/{cId}/dictionaries?type=X&account_name=Y` | POST |

### KSeF

| SkanujFakture API | Pinquark Integrator | Method |
|-------------------|---------------------|--------|
| `/companies/{cId}/documents/{dId}/ksef-xml` | `/companies/{cId}/documents/{dId}/ksef-xml?account_name=X` | GET |
| `/companies/{cId}/documents/{dId}/ksef-qr` | `/companies/{cId}/documents/{dId}/ksef-qr?account_name=X` | GET |
| `/companies/{cId}/ksef/online/FA3-1-0E` | `/companies/{cId}/ksef/invoice?account_name=X` | PUT |

## Document field mapping

### Document — main fields

| SkanujFakture Field | Type | Description |
|--------------------|-----|------|
| `id` | int | Document ID |
| `number` | string | Invoice number |
| `date` | datetime | Issue date |
| `operationDate` | datetime | Sale date |
| `inputDate` | datetime | Receipt date |
| `postingDate` | datetime | Posting date |
| `paymentDate` | datetime | Payment date |
| `netto` | float | Net value |
| `vat` | float | VAT value |
| `brutto` | float | Gross value |
| `amountToPay` | float | Amount to pay |
| `invoiceType` | string | `PURCHASE` / `SELL` |
| `scan` | string | Scan file name |

### Contractor

| Field | Type | Description |
|------|-----|------|
| `contractor.name` | string | Seller name |
| `contractor.nip` | string | Seller tax ID (NIP) |
| `contractor.address.city.city` | string | City |
| `contractor.address.street.street` | string | Street |
| `contractor.address.postCode.code` | string | Postal code |
| `contractor.address.houseNumber` | string | House number |

### Buyer (companyEntity)

| Field | Type | Description |
|------|-----|------|
| `companyEntity.contractorDTO.name` | string | Buyer name |
| `companyEntity.contractorDTO.nip` | string | Buyer tax ID (NIP) |

### VAT rates (documentVats)

| Field | Type | Description |
|------|-----|------|
| `rate.symbol` | string | Rate (e.g. "23", "8", "5") |
| `rate.rate` | float | Percentage value |
| `net` | float | Net per rate |
| `vat` | float | VAT per rate |
| `brutto` | float | Gross per rate |

### Invoice line items (documentItems)

| Field | Type | Description |
|------|-----|------|
| `name` | string | Product/service name |
| `units` | string | Unit of measure |
| `quantity` | float | Quantity |
| `netPrice` | float | Unit net price |
| `net` | float | Net value |
| `vat` | float | VAT value |
| `gross` | float | Gross value |

### Document statuses

| Status | ID | Description |
|--------|-----|------|
| `skanuje` | 1 | Scanning in progress |
| `do weryfikacji` | 2 | Requires verification |
| `zeskanowany` | 3 | Scanned (ready) |
| `wyeksportowany` | 4 | Exported |

### KSeF

| Field | Type | Description |
|------|-----|------|
| `ksef.ksefNumber` | string | KSeF number |
| `ksef.invoiceNumber` | string | Invoice number in KSeF |
| `ksef.issueDate` | string | Issue date |
| `ksef.sellerNip` | string | Seller tax ID (NIP) |
| `ksef.buyerNip` | string | Buyer tax ID (NIP) |
| `ksef.netAmount` | float | Net amount |
| `ksef.grossAmount` | float | Gross amount |
| `ksef.currency` | string | Currency |
| `ksef.schemaSystemCode` | string | Schema code (e.g. "FA (3)") |

## Dictionary types (posting)

| Type | Description |
|-----|------|
| `COST_TYPE` | Cost types |
| `COST_CENTER` | Cost centers |
| `ATTRIBUTE` | Attributes |
