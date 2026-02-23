# API Mapping — Pinquark WMS Integration REST API

This document maps every endpoint from the Pinquark Integration REST API documentation to the connector's proxy endpoints.

## Authentication

| WMS API Endpoint | Method | Connector Endpoint | Description |
|---|---|---|---|
| `/auth/sign-in` | POST | `/auth/sign-in` | Login with username/password → JWT tokens |
| `/auth/refresh-token` | POST | (handled internally) | Automatic token refresh via client |

JWT access token is valid for 24h, refresh token for 7 days. Bearer token header: `Authorization: Bearer <accessToken>`.

## Articles

| WMS API Endpoint | Method | Connector Endpoint | Description |
|---|---|---|---|
| `/articles` | GET | POST `/articles/get` | List all articles |
| `/articles/delete-commands` | GET | POST `/articles/get-delete-commands` | Get articles marked for deletion |
| `/articles` | POST | POST `/articles/create` | Create single article |
| `/articles/list` | POST | POST `/articles/create-list` | Create multiple articles |
| `/articles/delete-commands` | POST | POST `/articles/delete` | Delete single article |
| `/articles/delete-commands/list` | POST | POST `/articles/delete-list` | Delete multiple articles |

### Article fields

| Field | Type | Description |
|---|---|---|
| `erpId` | int | ERP system identifier |
| `wmsId` | int | WMS system identifier |
| `ean` | string | EAN barcode |
| `name` | string | Article name |
| `symbol` | string | Article symbol |
| `group` | string | Article group |
| `type` | string | Article type |
| `unit` | string | Base unit |
| `source` | string | Source system: `ERP` or `WMS` |
| `state` | int | Article state |
| `attributes` | Attribute[] | Generic attribute list |
| `images` | Image[] | Article images |
| `providers` | Provider[] | Supplier/provider info |
| `unitsOfMeasure` | UnitOfMeasure[] | Unit conversions with dimensions |

## Article Batches

| WMS API Endpoint | Method | Connector Endpoint | Description |
|---|---|---|---|
| `/article-batches` | GET | POST `/article-batches/get` | List all batches |
| `/article-batches` | POST | POST `/article-batches/create` | Create single batch |
| `/article-batches/list` | POST | POST `/article-batches/create-list` | Create multiple batches |

### Batch fields

| Field | Type | Description |
|---|---|---|
| `batchNumber` | string | Batch number |
| `eanCode` | string | EAN code |
| `erpArticleId` | int | Related article ERP ID |
| `batchOwner` | string | Batch owner name |
| `batchOwnerId` | int | Batch owner ID |
| `termValidity` | date | Batch expiry date |
| `attributes` | Attribute[] | Generic attribute list |

## Documents

| WMS API Endpoint | Method | Connector Endpoint | Description |
|---|---|---|---|
| `/documents` | GET | POST `/documents/get` | List all documents |
| `/documents/delete-commands` | GET | POST `/documents/get-delete-commands` | Get documents marked for deletion |
| `/documents` | POST | POST `/documents/create` | Create single document |
| `/documents/wrappers` | POST | POST `/documents/create-list` | Create multiple documents (with `continueOnFail`) |
| `/documents/delete-commands` | POST | POST `/documents/delete` | Delete single document |
| `/documents/delete-commands/list` | POST | POST `/documents/delete-list` | Delete multiple documents |

### Document fields

| Field | Type | Description |
|---|---|---|
| `erpId` | int | ERP document ID |
| `wmsId` | int | WMS document ID |
| `documentType` | string | Document type |
| `symbol` | string | Document symbol |
| `source` | string | `ERP` or `WMS` |
| `date` | date | Document date |
| `dueDate` | date | Due date |
| `erpCode` | string | ERP document code |
| `erpStatusSymbol` | string | ERP status symbol |
| `orderType` | string | Order type |
| `note` | string | Document note |
| `priority` | int | Priority level |
| `route` | string | Route info |
| `warehouseSymbol` | string | Warehouse symbol |
| `contractor` | ContractorRef | Contractor reference (erpId + source) |
| `contact` | Contact | Contact person details |
| `deliveryAddress` | Address | Delivery address |
| `positions` | Position[] | Document line items |
| `procedures` | string[] | WMS procedures |
| `attributes` | Attribute[] | Generic attribute list |

### Document wrapper (multiple create)

| Field | Type | Description |
|---|---|---|
| `continueOnFail` | boolean | `true` = save valid docs even if some fail; `false` = rollback all on any error |
| `documents` | Document[] | List of documents to create |

## Positions

| WMS API Endpoint | Method | Connector Endpoint | Description |
|---|---|---|---|
| `/positions` | GET | POST `/positions/get` | List all positions |
| `/positions/delete-commands` | GET | POST `/positions/get-delete-commands` | Get positions marked for deletion |
| `/positions` | POST | POST `/positions/create` | Create position(s) for a document |
| `/positions/list` | POST | POST `/positions/create-list` | Create positions for multiple documents |
| `/positions/delete-commands` | POST | POST `/positions/delete` | Delete single position |
| `/positions/delete-commands/list` | POST | POST `/positions/delete-list` | Delete multiple positions |

### Position fields

| Field | Type | Description |
|---|---|---|
| `documentId` | int | Parent document ID |
| `documentSource` | string | `ERP` or `WMS` |
| `no` | int | Position number |
| `erpId` | int | ERP position ID |
| `quantity` | number | Quantity |
| `statusSymbol` | string | Position status |
| `note` | string | Position note |
| `article` | Article | Article details (or just erpId for existing) |
| `articleBatch` | ArticleBatch | Batch info |
| `attributes` | Attribute[] | Generic attribute list |

## Contractors

| WMS API Endpoint | Method | Connector Endpoint | Description |
|---|---|---|---|
| `/contractors` | GET | POST `/contractors/get` | List all contractors |
| `/contractors/delete-commands` | GET | POST `/contractors/get-delete-commands` | Get contractors marked for deletion |
| `/contractors` | POST | POST `/contractors/create` | Create single contractor |
| `/contractors/list` | POST | POST `/contractors/create-list` | Create multiple contractors |
| `/contractors/delete-commands` | POST | POST `/contractors/delete` | Delete single contractor |
| `/contractors/delete-commands/list` | POST | POST `/contractors/delete-list` | Delete multiple contractors |

### Contractor fields

| Field | Type | Description |
|---|---|---|
| `erpId` | int | ERP contractor ID |
| `wmsId` | int | WMS contractor ID |
| `name` | string | Contractor name |
| `symbol` | string | Contractor symbol |
| `email` | string | Email |
| `phone` | string | Phone |
| `taxNumber` | string | Tax/NIP number |
| `isSupplier` | boolean | Is supplier flag |
| `supplierSymbol` | string | Supplier symbol |
| `source` | string | `ERP` or `WMS` |
| `description` | string | Description |
| `address` | Address | Primary address |
| `addresses` | Address[] | Additional addresses |
| `attributes` | Attribute[] | Generic attribute list |

## Feedback

| WMS API Endpoint | Method | Connector Endpoint | Description |
|---|---|---|---|
| `/feedbacks` | GET | POST `/feedbacks/get` | Get operation feedback |

### Feedback fields

| Field | Type | Description |
|---|---|---|
| `id` | int | Feedback ID |
| `action` | string | `SAVE` or `DELETE` |
| `entity` | string | `ARTICLE`, `CONTRACTOR`, `DOCUMENT`, etc. |
| `success` | boolean | Operation success flag |
| `errors` | map | Error details |
| `responseMessages` | map | Response messages |

## JSON Errors

| WMS API Endpoint | Method | Connector Endpoint | Description |
|---|---|---|---|
| `/errors` | GET | POST `/errors/get` | Get JSON parsing errors |

### Error fields

| Field | Type | Description |
|---|---|---|
| `body` | string | Original JSON body that caused the error |
| `createdDate` | datetime | Error timestamp |
| `topic` | string | Kafka topic where error originated |

## Generic Attribute System

All major entities (articles, documents, positions, contractors, batches) support a generic `attributes` array:

| Field | Type | Description |
|---|---|---|
| `symbol` | string | Attribute identifier |
| `type` | string | `DATE`, `DECIMAL`, `INT`, `TEXT`, `TIME` |
| `valueText` | string | Text value |
| `valueInt` | int | Integer value |
| `valueDecimal` | number | Decimal value |
| `valueDate` | date | Date value |
| `valueDateTo` | date | Date range end |
| `valueTime` | datetime | Time value |
| `status` | int | Attribute status |
| `filename` | string | Attached filename |
| `createdDate` | datetime | Creation timestamp |

## Delete Command Pattern

Articles use `uniqueCode` only. Documents, positions, and contractors additionally include `source` (`ERP`/`WMS`).
Positions also include `documentId`.
