# API Mapping — IdoSell ↔ Pinquark Unified Schemas

## Order Mapping

### IdoSellOrder → Order

| Pinquark Field | IdoSell Field | Notes |
|---|---|---|
| `external_id` | `orderId` | Falls back to `orderSerialNumber` |
| `status` | `order.orderStatus.orderStatus` | Mapped via status table below |
| `buyer.external_id` | `client.clientAccount.clientId` | |
| `buyer.email` | `client.clientAccount.clientEmail` | |
| `buyer.login` | `client.clientAccount.clientLogin` | |
| `buyer.first_name` | `client.clientDeliveryAddress.clientDeliveryAddressFirstName` | |
| `buyer.last_name` | `client.clientDeliveryAddress.clientDeliveryAddressLastName` | |
| `delivery_address.street` | `client.clientDeliveryAddress.clientDeliveryAddressStreet` | |
| `delivery_address.city` | `client.clientDeliveryAddress.clientDeliveryAddressCity` | |
| `delivery_address.postal_code` | `client.clientDeliveryAddress.clientDeliveryAddressZipCode` | |
| `delivery_address.country_code` | `client.clientDeliveryAddress.clientDeliveryAddressCountry` | Default: `PL` |
| `delivery_address.phone` | `client.clientDeliveryAddress.clientDeliveryAddressPhone1` | |
| `invoice_address.*` | `client.clientBillingAddress.*` | Same pattern as delivery |
| `total_amount` | `order.payments.orderBaseCurrency.orderProductsCost + orderDeliveryCost` | |
| `currency` | `order.payments.orderBaseCurrency.billingCurrency` | Default: `PLN` |
| `payment_type` | `order.payments.orderPaymentType` | |
| `delivery_method` | `order.dispatch.courierName` | |
| `notes` | `order.orderNote` or `order.clientNoteToOrder` | |
| `created_at` | `order.orderAddDate` | Format: `YYYY-MM-DD HH:MM:SS` |
| `updated_at` | `order.orderChangeDate` | Format: `YYYY-MM-DD HH:MM:SS` |

### Order Lines

| Pinquark Field | IdoSell Field | Notes |
|---|---|---|
| `external_id` | `productsResults[].productId` | |
| `product_id` | `productsResults[].productId` | |
| `sku` | `productsResults[].productCode` | |
| `name` | `productsResults[].productName` | |
| `quantity` | `productsResults[].productQuantity` | |
| `unit_price` | `productsResults[].productOrderPrice` | Gross price |

## Order Status Mapping

### IdoSell → Pinquark

| IdoSell Status | Pinquark Status |
|---|---|
| `new` | `NEW` |
| `payment_waiting` | `NEW` |
| `delivery_waiting` | `PROCESSING` |
| `on_order` | `PROCESSING` |
| `packed` | `PROCESSING` |
| `packed_fulfillment` | `PROCESSING` |
| `wait_for_packaging` | `PROCESSING` |
| `suspended` | `PROCESSING` |
| `blocked` | `PROCESSING` |
| `packed_ready` | `READY_FOR_SHIPMENT` |
| `ready` | `READY_FOR_SHIPMENT` |
| `wait_for_dispatch` | `READY_FOR_SHIPMENT` |
| `handled` | `SHIPPED` |
| `wait_for_receive` | `SHIPPED` |
| `finished` | `DELIVERED` |
| `finished_ext` | `DELIVERED` |
| `returned` | `RETURNED` |
| `complainted` | `RETURNED` |
| `canceled` | `CANCELLED` |
| `all_canceled` | `CANCELLED` |
| `false` | `CANCELLED` |
| `lost` | `CANCELLED` |
| `missing` | `CANCELLED` |
| `joined` | `CANCELLED` |

### Pinquark → IdoSell

| Pinquark Status | IdoSell Status |
|---|---|
| `NEW` | `new` |
| `PROCESSING` | `packed` |
| `READY_FOR_SHIPMENT` | `ready` |
| `SHIPPED` | `handled` |
| `DELIVERED` | `finished` |
| `CANCELLED` | `canceled` |
| `RETURNED` | `returned` |

## Product Mapping

### IdoSellProduct → Product

| Pinquark Field | IdoSell Field | Notes |
|---|---|---|
| `external_id` | `productId` | |
| `sku` | `productDisplayedCode` | |
| `ean` | `productSizesAttributes[0].productSizeCodeExternal` | First size variant |
| `name` | `productDescriptionsLangData[].productName` | Polish preferred (`pol`, `pl`) |
| `description` | `productDescriptionsLangData[].productDescription` | Polish preferred |
| `unit` | `productUnit.unitName` | Default: `szt.` |
| `price` | `productPosPrice` | POS price |
| `currency` | `currencyId` | Default: `PLN` |
| `stock_quantity` | Sum of `productStocksData.productStocksQuantities[].productSizesData[].productSizeQuantity` | Across all warehouses and sizes |

## Stock Sync Mapping

### StockItem → IdoSell Stock Update

| Pinquark Field | IdoSell Field | Notes |
|---|---|---|
| `sku` | `productIndex` | Product code/index |
| `ean` | `productSizeCodeExternal` | Size code |
| `warehouse_id` | `stockId` | Defaults to `default_stock_id` |
| `quantity` | `productSizeQuantity` | Absolute quantity |
