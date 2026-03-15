"""Shared pytest fixtures for IdoSell integrator tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.api.dependencies import AppState, app_state
from src.config import IdoSellAccountConfig
from src.idosell.schemas import (
    IdoSellBillingAddress,
    IdoSellDeliveryAddress,
    IdoSellDescriptionLangData,
    IdoSellOrder,
    IdoSellOrderBaseCurrency,
    IdoSellOrderClient,
    IdoSellOrderClientAccount,
    IdoSellOrderDetails,
    IdoSellOrderDispatch,
    IdoSellOrderStatus_,
    IdoSellPayment,
    IdoSellProduct,
    IdoSellProductResult,
    IdoSellProductSizeData,
    IdoSellProductStocksData,
    IdoSellProductStocksQuantities,
    IdoSellProductUnit,
    IdoSellSizeAttribute,
)


@pytest.fixture
def account_config() -> IdoSellAccountConfig:
    return IdoSellAccountConfig(
        name="test-shop",
        shop_url="https://test.idosell.com",
        api_key="test-api-key-12345",
        api_version="v6",
        default_stock_id=1,
        default_currency="PLN",
        environment="sandbox",
    )


@pytest.fixture
def sample_idosell_order() -> IdoSellOrder:
    return IdoSellOrder(
        orderId="ORD-001",
        orderSerialNumber=12345,
        orderType="retail",
        order=IdoSellOrderDetails(
            stockId=1,
            orderNote="Proszę o szybką wysyłkę",
            orderStatus=IdoSellOrderStatus_(orderStatus="new"),
            dispatch=IdoSellOrderDispatch(courierId=1, courierName="InPost"),
            payments=IdoSellPayment(
                orderPaymentType="prepaid",
                orderBaseCurrency=IdoSellOrderBaseCurrency(
                    billingCurrency="PLN",
                    orderProductsCost=99.99,
                    orderDeliveryCost=12.50,
                ),
            ),
            productsResults=[
                IdoSellProductResult(
                    productId=100,
                    productName="Koszulka Polo",
                    productCode="POLO-001",
                    productQuantity=2.0,
                    productOrderPrice=49.99,
                ),
            ],
            orderAddDate="2026-02-20 10:00:00",
            orderChangeDate="2026-02-21 14:30:00",
        ),
        client=IdoSellOrderClient(
            clientAccount=IdoSellOrderClientAccount(
                clientId=500,
                clientEmail="jan@example.com",
                clientLogin="jan_kowalski",
            ),
            clientBillingAddress=IdoSellBillingAddress(
                clientFirstName="Jan",
                clientLastName="Kowalski",
                clientFirm="Firma ABC",
                clientStreet="ul. Testowa 1",
                clientZipCode="00-001",
                clientCity="Warszawa",
                clientCountryName="PL",
                clientPhone1="500100200",
            ),
            clientDeliveryAddress=IdoSellDeliveryAddress(
                clientDeliveryAddressFirstName="Jan",
                clientDeliveryAddressLastName="Kowalski",
                clientDeliveryAddressStreet="ul. Dostawcza 5",
                clientDeliveryAddressZipCode="00-002",
                clientDeliveryAddressCity="Kraków",
                clientDeliveryAddressCountry="PL",
                clientDeliveryAddressPhone1="500100201",
            ),
        ),
    )


@pytest.fixture
def sample_idosell_product() -> IdoSellProduct:
    return IdoSellProduct(
        productId=100,
        productDisplayedCode="POLO-001",
        productDescriptionsLangData=[
            IdoSellDescriptionLangData(
                langId="pol",
                productName="Koszulka Polo",
                productDescription="Bawełniana koszulka polo",
            ),
        ],
        categoryId=10,
        categoryName="Odzież",
        currencyId="PLN",
        productPosPrice=49.99,
        productUnit=IdoSellProductUnit(unitId=1, unitName="szt.", unitPrecision=0),
        productSizesAttributes=[
            IdoSellSizeAttribute(
                sizeId="1",
                productSizeCodeExternal="5901234567890",
                productRetailPrice=49.99,
            ),
        ],
        productStocksData=IdoSellProductStocksData(
            productStocksQuantities=[
                IdoSellProductStocksQuantities(
                    stockId=1,
                    productSizesData=[
                        IdoSellProductSizeData(
                            sizeId="1",
                            productSizeQuantity=150.0,
                            productSizeCodeExternal="5901234567890",
                        ),
                    ],
                ),
            ],
        ),
    )


@pytest.fixture
def mock_integration() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_app_state(mock_integration: AsyncMock, account_config: IdoSellAccountConfig) -> AppState:
    state = app_state
    state.integration = mock_integration
    state.health_checker = None

    mock_account_manager = MagicMock()
    mock_account_manager.get_account.return_value = account_config
    mock_account_manager.list_accounts.return_value = [account_config]
    state.account_manager = mock_account_manager

    return state
