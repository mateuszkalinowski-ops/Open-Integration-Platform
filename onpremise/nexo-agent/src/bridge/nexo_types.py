"""Type mappings and utilities for converting between Nexo .NET types and Python models.

This module provides helper functions to safely extract data from .NET objects
returned by the InsERT Nexo SDK and convert them to Python/Pydantic models.
"""

import logging
from datetime import datetime
from typing import Any

from src.models.contractor import (
    ContractorAddress,
    ContractorContact,
    ContractorResponse,
    ContractorType,
)
from src.models.product import (
    ProductPriceInfo,
    ProductResponse,
    ProductSupplier,
    ProductType,
    ProductUnitOfMeasure,
)
from src.models.document import (
    DocumentParty,
    DocumentPayment,
    DocumentPosition,
    DocumentResponse,
    DocumentStatus,
    DocumentType,
)
from src.models.order import (
    OrderPosition,
    OrderResponse,
    OrderStatus,
    OrderType,
)
from src.models.stock import StockLevel

logger = logging.getLogger(__name__)


def _safe_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _safe_float(val: Any) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(val: Any) -> int:
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _safe_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    try:
        if isinstance(val, datetime):
            return val
        return datetime.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


def _net_datetime_to_python(net_dt: Any) -> datetime | None:
    """Convert a .NET DateTime to a Python datetime."""
    if net_dt is None:
        return None
    try:
        return datetime(
            year=net_dt.Year,
            month=net_dt.Month,
            day=net_dt.Day,
            hour=net_dt.Hour,
            minute=net_dt.Minute,
            second=net_dt.Second,
        )
    except Exception:
        return None


def _iterate_net_collection(collection: Any) -> list[Any]:
    """Safely iterate a .NET IEnumerable and return as Python list."""
    result = []
    if collection is None:
        return result
    try:
        enumerator = collection.GetEnumerator()
        while enumerator.MoveNext():
            result.append(enumerator.Current)
    except Exception:
        try:
            for item in collection:
                result.append(item)
        except Exception:
            logger.warning("Failed to iterate .NET collection")
    return result


def nexo_contractor_to_model(podmiot: Any) -> ContractorResponse:
    """Convert a Nexo Podmiot entity to a ContractorResponse model."""
    dane = podmiot

    is_company = hasattr(dane, "Firma") and dane.Firma is not None
    contractor_type = ContractorType.COMPANY if is_company else ContractorType.PERSON

    addresses: list[ContractorAddress] = []
    try:
        for addr in _iterate_net_collection(getattr(dane, "Adresy", None)):
            szcz = getattr(addr, "Szczegoly", addr)
            addresses.append(
                ContractorAddress(
                    address_type=_safe_str(getattr(addr, "Typ", "main")),
                    street=_safe_str(getattr(szcz, "Ulica", "")),
                    house_number=_safe_str(getattr(szcz, "NrDomu", "")),
                    apartment_number=_safe_str(getattr(szcz, "NrLokalu", "")),
                    postal_code=_safe_str(getattr(szcz, "KodPocztowy", "")),
                    city=_safe_str(getattr(szcz, "Miejscowosc", "")),
                    country=_safe_str(getattr(szcz, "KrajISO", "PL")),
                )
            )
    except Exception:
        logger.debug("Could not extract addresses from contractor")

    contacts: list[ContractorContact] = []
    try:
        for kontakt in _iterate_net_collection(getattr(dane, "Kontakty", None)):
            contacts.append(
                ContractorContact(
                    contact_type=_safe_str(getattr(kontakt, "Rodzaj", "")),
                    value=_safe_str(getattr(kontakt, "Wartosc", "")),
                    is_primary=bool(getattr(kontakt, "Podstawowy", False)),
                )
            )
    except Exception:
        logger.debug("Could not extract contacts from contractor")

    sygnatura = getattr(dane, "Sygnatura", None)
    symbol = _safe_str(getattr(sygnatura, "PelnaSygnatura", "")) if sygnatura else ""

    return ContractorResponse(
        id=_safe_int(getattr(dane, "Id", 0)),
        symbol=symbol,
        contractor_type=contractor_type,
        short_name=_safe_str(getattr(dane, "NazwaSkrocona", "")),
        full_name=_safe_str(getattr(dane, "NazwaPelna", getattr(dane, "NazwaSkrocona", ""))),
        nip=_safe_str(getattr(dane, "NIPSformatowany", getattr(dane, "NIP", ""))),
        regon=_safe_str(getattr(dane, "REGON", "")),
        first_name=_safe_str(getattr(dane, "Imie", "")),
        last_name=_safe_str(getattr(dane, "Nazwisko", "")),
        addresses=addresses,
        contacts=contacts,
    )


def nexo_product_to_model(asortyment: Any) -> ProductResponse:
    """Convert a Nexo Asortyment entity to a ProductResponse model."""
    dane = asortyment

    return ProductResponse(
        id=_safe_int(getattr(dane, "Id", 0)),
        symbol=_safe_str(getattr(dane, "Symbol", "")),
        product_type=ProductType.GOODS,
        name=_safe_str(getattr(dane, "Nazwa", "")),
        ean=_safe_str(getattr(dane, "EAN", "")),
        pkwiu=_safe_str(getattr(dane, "PKWiU", "")),
        vat_rate=_safe_str(getattr(dane, "StawkaVAT", "")),
        unit_of_measure=_safe_str(
            getattr(getattr(dane, "PodstawowaJednostkaMiaryAsortymentu", None), "Symbol", "szt")
        ),
        weight_kg=_safe_float(getattr(dane, "Waga", None)) or None,
        description=_safe_str(getattr(dane, "Opis", "")),
    )


def nexo_sales_document_to_model(dokument: Any) -> DocumentResponse:
    """Convert a Nexo DokumentDS (sales document) to a DocumentResponse."""
    dane = dokument

    number_obj = getattr(dane, "NumerWewnetrzny", None)
    number = _safe_str(getattr(number_obj, "PelnaSygnatura", "")) if number_obj else ""

    positions: list[DocumentPosition] = []
    try:
        for poz in _iterate_net_collection(getattr(dane, "Pozycje", None)):
            positions.append(
                DocumentPosition(
                    product_id=_safe_int(getattr(poz, "IdAsortymentu", 0)) or None,
                    product_symbol=_safe_str(getattr(poz, "SymbolAsortymentu", "")),
                    product_name=_safe_str(getattr(poz, "NazwaAsortymentu", "")),
                    quantity=_safe_float(getattr(poz, "Ilosc", 1)),
                    net_price=_safe_float(getattr(poz, "CenaNetto", 0)),
                    gross_price=_safe_float(getattr(poz, "CenaBrutto", 0)),
                    vat_rate=_safe_str(getattr(poz, "StawkaVAT", "")),
                )
            )
    except Exception:
        logger.debug("Could not extract positions from sales document")

    return DocumentResponse(
        id=_safe_int(getattr(dane, "Id", 0)),
        document_type=DocumentType.SALES_INVOICE,
        number=number,
        positions=positions,
        net_total=_safe_float(getattr(dane, "WartoscNetto", 0)),
        gross_total=_safe_float(getattr(dane, "WartoscBrutto", 0)),
        vat_total=_safe_float(getattr(dane, "WartoscVAT", 0)),
        issue_date=_net_datetime_to_python(getattr(dane, "DataWystawienia", None)),
        sale_date=_net_datetime_to_python(getattr(dane, "DataSprzedazy", None)),
    )


def nexo_warehouse_document_to_model(dokument: Any) -> DocumentResponse:
    """Convert a Nexo warehouse document (WZ/PZ) to a DocumentResponse."""
    dane = dokument

    number_obj = getattr(dane, "NumerWewnetrzny", None)
    number = _safe_str(getattr(number_obj, "PelnaSygnatura", "")) if number_obj else ""

    positions: list[DocumentPosition] = []
    try:
        for poz in _iterate_net_collection(getattr(dane, "Pozycje", None)):
            positions.append(
                DocumentPosition(
                    product_id=_safe_int(getattr(poz, "IdAsortymentu", 0)) or None,
                    product_symbol=_safe_str(getattr(poz, "SymbolAsortymentu", "")),
                    product_name=_safe_str(getattr(poz, "NazwaAsortymentu", "")),
                    quantity=_safe_float(getattr(poz, "Ilosc", 1)),
                )
            )
    except Exception:
        logger.debug("Could not extract positions from warehouse document")

    return DocumentResponse(
        id=_safe_int(getattr(dane, "Id", 0)),
        document_type=DocumentType.WAREHOUSE_ISSUE,
        number=number,
        positions=positions,
        issue_date=_net_datetime_to_python(getattr(dane, "DataWystawienia", None)),
    )


def nexo_order_to_model(zamowienie: Any, order_type: OrderType = OrderType.FROM_CUSTOMER) -> OrderResponse:
    """Convert a Nexo Zamówienie to an OrderResponse."""
    dane = zamowienie

    number_obj = getattr(dane, "NumerWewnetrzny", None)
    number = _safe_str(getattr(number_obj, "PelnaSygnatura", "")) if number_obj else ""

    positions: list[OrderPosition] = []
    try:
        for poz in _iterate_net_collection(getattr(dane, "Pozycje", None)):
            positions.append(
                OrderPosition(
                    product_id=_safe_int(getattr(poz, "IdAsortymentu", 0)) or None,
                    product_symbol=_safe_str(getattr(poz, "SymbolAsortymentu", "")),
                    product_name=_safe_str(getattr(poz, "NazwaAsortymentu", "")),
                    quantity=_safe_float(getattr(poz, "Ilosc", 1)),
                    net_price=_safe_float(getattr(poz, "CenaNetto", 0)),
                    gross_price=_safe_float(getattr(poz, "CenaBrutto", 0)),
                    vat_rate=_safe_str(getattr(poz, "StawkaVAT", "")),
                )
            )
    except Exception:
        logger.debug("Could not extract positions from order")

    return OrderResponse(
        id=_safe_int(getattr(dane, "Id", 0)),
        order_type=order_type,
        number=number,
        positions=positions,
        net_total=_safe_float(getattr(dane, "WartoscNetto", 0)),
        gross_total=_safe_float(getattr(dane, "WartoscBrutto", 0)),
        expected_date=_net_datetime_to_python(getattr(dane, "TerminRealizacji", None)),
    )


def nexo_stock_to_model(stan: Any, warehouse_symbol: str = "") -> StockLevel:
    """Convert Nexo stock data to a StockLevel model."""
    return StockLevel(
        product_symbol=_safe_str(getattr(stan, "SymbolAsortymentu", getattr(stan, "Symbol", ""))),
        product_name=_safe_str(getattr(stan, "NazwaAsortymentu", getattr(stan, "Nazwa", ""))),
        warehouse_symbol=warehouse_symbol or _safe_str(getattr(stan, "SymbolMagazynu", "")),
        quantity_available=_safe_float(getattr(stan, "StanDostepny", getattr(stan, "Dostepna", 0))),
        quantity_reserved=_safe_float(getattr(stan, "StanZarezerwowany", getattr(stan, "Zarezerwowana", 0))),
        quantity_total=_safe_float(getattr(stan, "StanCalkowity", getattr(stan, "Calkowita", 0))),
        unit=_safe_str(getattr(stan, "JednostkaMiary", "szt")),
    )
