# BaseLinker API Changelog

> Source: https://api.baselinker.com/?changelog
> Fetched: 2026-02-24

*In the event of a parameter format change/removal of a parameter/method withdrawal,
existing integrations are supported with backward compatibility for six months after
publication of the change.*

---

| Date | Changes |
|------|---------|
| 2026-02-16 | Added `tax_no` field support in `getInventorySuppliers` and `addInventorySupplier`. Deprecated `contractor_id` param in `setConnectContractorCreditLimit` (use `connect_contractor_id`). |
| 2026-01-27 | Added `target_location_name` parameter to `addInventoryDocumentItems` and `getInventoryDocumentItems` for IT/MM transfer documents. |
| 2026-01-26 | Added `return_reason_comment` to `getOrderReturns`. Added `date_delivery_expected` to `addInventoryPurchaseOrder`. Added `parent_id` field in `getInventoryProductsData` and `getInventoryProductsList`. Added `notes` param to `addInventoryDocument`. Added `notes` to `getInventoryDocuments` response. |
| 2026-01-20 | Added `connected_source_object_type`/`connected_source_object_id` to `getInventoryDocuments`. Added `notes`, `source_object_type`, `source_object_id` to `getInventoryDocuments`. |
| 2025-10-21 | Added `setConnectContractorCreditLimit`. Deprecated `addConnectContractorCredit`. |
| 2025-09-23 | Added `addOrderDuplicate`. Added ASIN field support across product-related methods. |
| 2025-09-15 | Added `getOrderPrintoutTemplates` and `getInventoryPrintoutTemplates`. |
| 2025-09-08 | Added `getPackageDetails` and `setOrdersMerge`. |
| 2025-09-02 | Added `include_commission_data` and `include_connect_data` to `getOrders`. |
| 2025-08-18 | Added `order_product_id` field to `addOrderReturn` and `addOrderReturnProduct`. |
| 2025-08-12 | Added inventory document methods (`addInventoryDocument`, `addInventoryDocumentItems`, `setInventoryDocumentStatusConfirmed`), purchase order methods, supplier/payer methods, `addOrderBySplit`. |
| 2025-04-23 | Added `commission` parameter to `getOrders` (with `with_commission` flag). |
| 2025-03-18 | Added `getInventoryDocuments`, `getInventoryDocumentItems`, `getInventoryDocumentSeries`. |
| 2025-03-06 | Added `getInventoryPurchaseOrders`, `getInventoryPurchaseOrderItems`, `getInventoryPurchaseOrderSeries`. |
| 2025-02-19 | Added additional EANs support. Added `tags` to `addInventoryProduct` and `getInventoryProductsData`. Added `getInventoryTags`. Journal log type 21 (editing invoice data). |
| 2024-10-10 | Renamed parameters in Base Connect methods (backward compatible). |
| 2024-06-05 | Added Base Connect methods. Added `stock_erp_unit` to `getInventoryProductsData`. Replaced `getOrderTransactionDetails` with `getOrderTransactionData`. |
| 2024-05-16 | Added order return methods. |
| 2024-03-05 | Added `average_cost` to `addInventoryProduct`. |
| 2024-01-31 | Added `is_return` to `getOrderPackages`. |
| 2024-01-10 | Added `getOrderPickPackHistory`. |
| 2023-08-23 | Added `vat_rate` to `addInvoice`, `printer_name` to `setOrderReceipt`, `getInvoiceFile`. |
| 2023-08-16 | Added `setOrdersStatuses`, `runProductMacroTrigger`, `addOrderReceiptFile`, `issuer` to `getInvoices`. Corrected return types in `getOrders`. |
| 2023-02-14 | Added `return_shipment` to `createPackageManual`. |
| 2022-12-28 | Added `delivery_state`/`invoice_state` to `getOrders`, `addOrder`, `setOrderFields`. |
| 2022-06-29 | Added file upload for product extra fields. Added `comment` to `getOrderPaymentsHistory`. |
| 2022-06-14 | Added `filter_order_source`/`filter_order_source_id` to `getOrders`. Added `average_cost`/`average_landed_cost` to `getInventoryProductsData`. |
| 2022-05-11 | **(IMPORTANT)** Changed custom extra fields format in `getOrders`/`addOrder`/`setOrderFields`. Added bundle ID to `getOrders`. |
| 2022-04-20 | **(IMPORTANT)** All responses now return `Content-Type: application/json`. |
| 2022-04-14 | Added `getOrderExtraFields`. Added custom extra fields to `getOrders`/`addOrder`/`setOrderFields`. |
| 2022-01-28 | Added product source warehouse to `getOrders`/`addOrder`/`addOrderProduct`/`setOrderProductFields`. |
| 2021-12-28 | Added product location to order methods. |
| 2021-11-14 | **(IMPORTANT)** Changed IP addresses for `api.baselinker.com` (Cloudflare). |
| 2021-11-05 | **(IMPORTANT)** `X-BLToken` header authentication recommended. POST token param deprecated. |
| 2021-09-29 | **(IMPORTANT)** `tax_rate` can now be float (e.g. 5.5, 7.5 for OSS). |
| 2021-09-16 | Added `getOrderSources`, `custom_source_id` in `addOrder`, `getOrderTransactionDetails`. |
| 2021-01-28 | Removed `invoice_country`/`delivery_country` from `setOrderFields` (backward compatible). |
| 2020-11-18 | Added `get_external_invoices` to `getInvoices`. |
| 2020-09-07 | Added `external_id` to `getInvoices`. |
| 2020-08-18 | Added `package_id` param to `getLabel`/`deleteCourierPackage`. Added `courier_inner_number` to `createPackage`/`getOrderPackages`. Added `getReceipt`. |
| 2020-05-18 | Added `series_id` to `getInvoices`/`getNewReceipts`. |
| 2020-03-05 | Added `addInvoice` and `getSeries`. |
| 2020-02-27 | Added `delivery_point_id`. Added `external_invoice_number`. Changed `price_netto` → `price_brutto` in `addProduct`. |
| 2020-02-15 | Added `addOrderInvoiceFile`. |
| 2020-02-06 | Added `deleteCourierPackage`. |
| 2020-01-23 | Added `sku`/`ean` to `getNewReceipts`. |
| 2019-12-29 | Added `nip` to `getNewReceipts`. |
| 2019-12-12 | Added `getOrderPaymentsHistory`. |
| 2019-11-28 | **(IMPORTANT)** Changed `storage_id` format to `[type]_[id]`. Added external storage support. Changed pagination. |
