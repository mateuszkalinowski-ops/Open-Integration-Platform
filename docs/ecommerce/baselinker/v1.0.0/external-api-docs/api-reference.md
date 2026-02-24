# BaseLinker API Reference

> Source: https://api.baselinker.com/
> Last updated by BaseLinker: 2026-02-16
> Fetched: 2026-02-24

## Introduction

The API enables information exchange between an external system and BaseLinker.
Communication uses data in JSON format.

**Endpoint:** `POST https://api.baselinker.com/connector.php`

**Authentication:** `X-BLToken` HTTP header containing the API token generated in
BaseLinker panel under "Account & other → My account → API".

**POST parameters:**

| Parameter    | Description                                           |
|-------------|-------------------------------------------------------|
| `method`    | The name of the requested API method                  |
| `parameters`| Arguments of the requested function in JSON format    |

**Rate limit:** 100 requests per minute.

**Encoding:** UTF-8. Base64 content must have `+` replaced with `%2B` before sending.

### Sample request

```bash
curl 'https://api.baselinker.com/connector.php' \
  -H 'X-BLToken: 1-23-ABC' \
  --data-raw 'method=getOrders&parameters=%7B%22date_from%22%3A+1407341754%7D'
```

### Error response format

When `status` is `"ERROR"`, two additional fields are returned:

| Field           | Type   | Description              |
|----------------|--------|--------------------------|
| `error_message`| string | Human-readable error     |
| `error_code`   | string | Machine-readable code    |

---

## API Method Categories

### Product Catalog

| Method | Description |
|--------|-------------|
| `addInventoryPriceGroup` | Create/update a price group in BaseLinker storage |
| `deleteInventoryPriceGroup` | Remove a price group |
| `getInventoryPriceGroups` | Retrieve price groups |
| `addInventoryWarehouse` | Add/update a warehouse in BaseLinker inventories |
| `deleteInventoryWarehouse` | Remove a warehouse |
| `getInventoryWarehouses` | Retrieve list of warehouses |
| `addInventory` | Add/update a BaseLinker catalog |
| `deleteInventory` | Delete a catalog |
| `getInventories` | Retrieve list of catalogs |
| `addInventoryCategory` | Add/update a category in catalog |
| `deleteInventoryCategory` | Remove category (products in it are also removed) |
| `getInventoryCategories` | Retrieve categories for a catalog |
| `getInventoryTags` | Retrieve tags for a catalog |
| `addInventoryManufacturer` | Add/update a manufacturer |
| `deleteInventoryManufacturer` | Remove a manufacturer |
| `getInventoryManufacturers` | Retrieve manufacturers |
| `getInventoryExtraFields` | Retrieve extra fields for a catalog |
| `getInventoryIntegrations` | List integrations with overridable text values |
| `getInventoryAvailableTextFieldKeys` | List overridable text field keys per integration |
| `addInventoryProduct` | Add/update a product in catalog |
| `deleteInventoryProduct` | Remove a product from catalog |
| `getInventoryProductsData` | Retrieve detailed data for selected products |
| `getInventoryProductsList` | Retrieve basic data for products |
| `getInventoryProductsStock` | Retrieve stock data |
| `updateInventoryProductsStock` | Update stocks (max 1000 products/call) |
| `getInventoryProductsPrices` | Retrieve gross prices |
| `updateInventoryProductsPrices` | Bulk update gross prices (max 1000/call) |
| `getInventoryProductLogs` | Retrieve product change events |
| `runProductMacroTrigger` | Run personal trigger for product auto-actions |

### Inventory Documents

| Method | Description |
|--------|-------------|
| `addInventoryDocument` | Create a new inventory document (draft) |
| `setInventoryDocumentStatusConfirmed` | Confirm an inventory document |
| `getInventoryDocuments` | Retrieve list of inventory documents |
| `getInventoryDocumentItems` | Retrieve document items |
| `addInventoryDocumentItems` | Add items to a document |
| `getInventoryDocumentSeries` | Retrieve document series |

### Inventory Purchase Orders

| Method | Description |
|--------|-------------|
| `getInventoryPurchaseOrders` | Retrieve purchase orders |
| `getInventoryPurchaseOrderItems` | Retrieve purchase order items |
| `getInventoryPurchaseOrderSeries` | Retrieve purchase order series |
| `addInventoryPurchaseOrder` | Create a new purchase order |
| `addInventoryPurchaseOrderItems` | Add items to a purchase order |
| `setInventoryPurchaseOrderStatus` | Change purchase order status |

### Inventory Suppliers

| Method | Description |
|--------|-------------|
| `getInventorySuppliers` | Retrieve list of suppliers |
| `addInventorySupplier` | Add/update a supplier |
| `deleteInventorySupplier` | Remove a supplier |

### Inventory Payers

| Method | Description |
|--------|-------------|
| `getInventoryPayers` | Retrieve list of payers |
| `addInventoryPayer` | Add/update a payer |
| `deleteInventoryPayer` | Remove a payer |

### External Storages

| Method | Description |
|--------|-------------|
| `getExternalStoragesList` | Retrieve list of external storages |
| `getExternalStorageCategories` | Retrieve categories from external storage |
| `getExternalStorageProductsData` | Retrieve product data from external storage |
| `getExternalStorageProductsList` | Retrieve product list from external storage |
| `getExternalStorageProductsQuantity` | Retrieve stock from external storage |
| `getExternalStorageProductsPrices` | Retrieve prices from external storage |
| `updateExternalStorageProductsQuantity` | Bulk update stock in external storage (max 1000/call) |

### Orders

| Method | Description |
|--------|-------------|
| `getJournalList` | Download order events from last 3 days |
| `addOrder` | Add new order to order manager |
| `addOrderDuplicate` | Duplicate an existing order |
| `getOrderSources` | Get order source types with IDs |
| `getOrderExtraFields` | Get extra fields defined for orders |
| `getOrders` | Download orders with filters (max 100/call) |
| `getOrderTransactionData` | Retrieve transaction details for an order |
| `getOrdersByEmail` | Search orders by email |
| `getOrdersByPhone` | Search orders by phone |
| `deleteOrders` | Delete multiple orders |
| `addInvoice` | Issue an order invoice |
| `addInvoiceCorrection` | Issue an invoice correction |
| `getInvoices` | Download invoices (max 100/call) |
| `getSeries` | Get invoice/receipt numbering series |
| `getOrderStatusList` | Get order statuses |
| `getOrderPaymentsHistory` | Get payment history for an order |
| `getOrderPickPackHistory` | Get pick pack history for an order |
| `getNewReceipts` | Get receipts waiting to be issued |
| `getReceipts` | Get issued receipts (max 100/call) |
| `getReceipt` | Get a single receipt |
| `setOrderFields` | Edit order fields |
| `addOrderProduct` | Add product to order |
| `setOrderProductFields` | Edit order item data |
| `deleteOrderProduct` | Remove product from order |
| `setOrderPayment` | Add payment to order |
| `setOrderStatus` | Change order status |
| `setOrderStatuses` | Batch set order statuses |
| `setOrderReceipt` | Mark order with receipt issued |
| `addOrderInvoiceFile` | Add external invoice file |
| `addOrderReceiptFile` | Add external receipt file (PDF/JWS) |
| `addOrderBySplit` | Split products from order into new order |
| `setOrdersMerge` | Merge multiple orders |
| `getInvoiceFile` | Get invoice file |
| `runOrderMacroTrigger` | Run personal trigger for order auto-actions |
| `getPickPackCarts` | Get list of PickPack carts |

### Order Returns

| Method | Description |
|--------|-------------|
| `getOrderReturnJournalList` | Download return events from last 3 days |
| `addOrderReturn` | Add new order return |
| `getOrderReturnExtraFields` | Get extra fields for returns |
| `getOrderReturns` | Download order returns (max 100/call) |
| `getOrderReturnStatusList` | Get return statuses |
| `getOrderReturnPaymentsHistory` | Get payment history for a return |
| `setOrderReturnFields` | Edit return fields |
| `addOrderReturnProduct` | Add product to return |
| `setOrderReturnProductFields` | Edit return item data |
| `deleteOrderReturnProduct` | Remove product from return |
| `setOrderReturnRefund` | Mark return as refunded |
| `getOrderReturnReasonsList` | Get return reasons |
| `setOrderReturnStatus` | Change return status |
| `setOrderReturnStatuses` | Batch set return statuses |
| `runOrderReturnMacroTrigger` | Run personal trigger for return auto-actions |
| `getOrderReturnProductStatuses` | Get return item statuses |

### Courier Shipments

| Method | Description |
|--------|-------------|
| `createPackage` | Create shipment in courier system |
| `createPackageManual` | Manually add shipping number to order |
| `getCouriersList` | Retrieve available couriers |
| `getCourierFields` | Get form fields for courier shipments |
| `getCourierServices` | Get additional courier services |
| `getCourierAccounts` | Get courier accounts |
| `getLabel` | Download shipping label |
| `getProtocol` | Download parcel protocol |
| `getCourierDocument` | Download parcel document |
| `getOrderPackages` | Get shipments for order |
| `getPackageDetails` | Get detailed package info |
| `getCourierPackagesStatusHistory` | Get shipment status history (max 100/call) |
| `deleteCourierPackage` | Delete a shipment |
| `runRequestParcelPickup` | Request parcel pickup |
| `getRequestParcelPickupFields` | Get pickup request fields |

### Printouts

| Method | Description |
|--------|-------------|
| `getOrderPrintoutTemplates` | Get order printout templates |
| `getInventoryPrintoutTemplates` | Get inventory printout templates |

### Base Connect

| Method | Description |
|--------|-------------|
| `getConnectIntegrations` | Get Base Connect integrations |
| `getConnectIntegrationContractors` | Get contractors for an integration |
| `getConnectContractorCreditHistory` | Get contractor credit history |
| `setConnectContractorCreditLimit` | Set contractor credit limit |
| `addConnectContractorCreditSettlement` | Add manual credit settlement |

### Products Storage (OBSOLETE)

| Method | Description |
|--------|-------------|
| `getStoragesList` | Get available storages |
| `addCategory` | Add/update category |
| `addProduct` | Add/update product |
| `addProductVariant` | Add/update variant |
| `deleteCategory` | Remove category |
| `deleteProduct` | Remove product |
| `deleteProductVariant` | Remove variant |
| `getCategories` | Get categories |
| `getProductsData` | Get product data |
| `getProductsList` | Get product list |
| `getProductsQuantity` | Get stock |
| `getProductsPrices` | Get prices |
| `updateProductsQuantity` | Bulk update stock (max 1000/call) |
| `updateProductsPrices` | Bulk update prices (max 1000/call) |
