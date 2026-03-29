"""Invoice XML builder for KSeF FA(3) schema.

Generates XML documents conforming to the FA(3) XSD schema
required by KSeF 2.0 from February 1, 2026.

Namespace: http://crd.gov.pl/wzor/2025/06/25/13775/
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

logger = logging.getLogger(__name__)

FA3_NAMESPACE = "http://crd.gov.pl/wzor/2025/06/25/13775/"
ETD_NAMESPACE = "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


def build_invoice_xml(invoice_data: dict[str, Any]) -> bytes:
    """Build an FA(3) invoice XML from structured data.

    Expected invoice_data structure:
    {
        "invoice_number": "FV/2026/001",
        "issue_date": "2026-03-29",
        "issue_place": "Warszawa",
        "sale_date": "2026-03-29",
        "currency": "PLN",
        "invoice_type": "VAT",
        "seller": {
            "nip": "1234567890",
            "name": "Firma Sprzedawca Sp. z o.o.",
            "address_line1": "ul. Przykładowa 1",
            "address_line2": "00-001 Warszawa"
        },
        "buyer": {
            "nip": "0987654321",
            "name": "Firma Nabywca S.A.",
            "address_line1": "ul. Testowa 5",
            "address_line2": "30-001 Kraków"
        },
        "items": [
            {
                "description": "Usługa informatyczna",
                "quantity": 1,
                "unit": "szt.",
                "unit_price_net": 10000.00,
                "net_amount": 10000.00,
                "vat_rate": 23
            }
        ],
        "total_net": 10000.00,
        "total_vat": 2300.00,
        "total_gross": 12300.00,
        "payment": {
            "method": "6",
            "paid": false,
            "due_date": "2026-04-28"
        }
    }
    """
    root = Element("Faktura")
    root.set("xmlns", FA3_NAMESPACE)
    root.set("xmlns:etd", ETD_NAMESPACE)
    root.set("xmlns:xsi", XSI_NAMESPACE)

    _add_header(root, invoice_data)
    _add_seller(root, invoice_data.get("seller", {}))
    _add_buyer(root, invoice_data.get("buyer", {}))

    fa = SubElement(root, "Fa")
    _add_invoice_body(fa, invoice_data)

    xml_declaration = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_body = tostring(root, encoding="unicode").encode("utf-8")
    return xml_declaration + xml_body


def _add_header(root: Element, data: dict[str, Any]) -> None:
    header = SubElement(root, "Naglowek")

    kod_formularza = SubElement(header, "KodFormularza")
    kod_formularza.text = "FA"
    kod_formularza.set("kodSystemowy", "FA (3)")
    kod_formularza.set("wersjaSchemy", "1-0E")

    wariant = SubElement(header, "WariantFormularza")
    wariant.text = "3"

    data_wytw = SubElement(header, "DataWytworzeniaFa")
    data_wytw.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    system_info = SubElement(header, "SystemInfo")
    system_info.text = "Open Integration Platform v1.0"


def _add_seller(root: Element, seller: dict[str, Any]) -> None:
    podmiot = SubElement(root, "Podmiot1")

    dane = SubElement(podmiot, "DaneIdentyfikacyjne")
    nip = SubElement(dane, "NIP")
    nip.text = seller.get("nip", "")

    nazwa = SubElement(dane, "Nazwa")
    nazwa.text = seller.get("name", "")

    adres = SubElement(podmiot, "Adres")
    _add_address(adres, seller)


def _add_buyer(root: Element, buyer: dict[str, Any]) -> None:
    podmiot = SubElement(root, "Podmiot2")

    dane = SubElement(podmiot, "DaneIdentyfikacyjne")

    buyer_nip = buyer.get("nip", "")
    if buyer_nip:
        nip_el = SubElement(dane, "NIP")
        nip_el.text = buyer_nip

    nazwa = SubElement(dane, "Nazwa")
    nazwa.text = buyer.get("name", "")

    adres = SubElement(podmiot, "Adres")
    _add_address(adres, buyer)

    jst = SubElement(podmiot, "JST")
    jst.text = str(buyer.get("jst", 2))

    gv = SubElement(podmiot, "GV")
    gv.text = str(buyer.get("gv", 2))


def _add_address(parent: Element, entity: dict[str, Any]) -> None:
    country = SubElement(parent, "KodKraju")
    country.text = entity.get("country", "PL")

    addr = entity.get("address", {})
    if isinstance(addr, dict):
        line1 = addr.get("street", "") or addr.get("address_line1", "")
        line2 = addr.get("postal_code", "")
        if addr.get("city"):
            line2 = f"{line2} {addr['city']}".strip()
        if not line2:
            line2 = addr.get("address_line2", "")
    else:
        line1 = entity.get("address_line1", "")
        line2 = entity.get("address_line2", "")

    if not line1:
        line1 = entity.get("address_line1", "")
    if not line2:
        line2 = entity.get("address_line2", "")

    addr_l1 = SubElement(parent, "AdresL1")
    addr_l1.text = line1 or "-"

    addr_l2 = SubElement(parent, "AdresL2")
    addr_l2.text = line2 or "-"


def _add_invoice_body(fa: Element, data: dict[str, Any]) -> None:
    """Add all Fa sub-elements in the correct order per FA(3) schema."""
    waluta = SubElement(fa, "KodWaluty")
    waluta.text = data.get("currency", "PLN")

    p1 = SubElement(fa, "P_1")
    p1.text = data.get("issue_date", date.today().isoformat())

    p1m = SubElement(fa, "P_1M")
    p1m.text = data.get("issue_place", "Polska")

    p2 = SubElement(fa, "P_2")
    inv_num = data.get("invoice_number", "")
    if not inv_num:
        from datetime import datetime

        inv_num = f"FV/{datetime.now().strftime('%Y/%m/%d/%H%M%S')}"
    p2.text = inv_num

    if data.get("sale_date"):
        p6 = SubElement(fa, "P_6")
        p6.text = data["sale_date"]

    _add_totals(fa, data)
    _add_adnotacje(fa, data)

    rodzaj = SubElement(fa, "RodzajFaktury")
    rodzaj.text = data.get("invoice_type", "VAT")

    _add_line_items(fa, data.get("items", []))
    _add_payment(fa, data.get("payment", {}))


def _item_net(item: dict[str, Any]) -> float:
    na = item.get("net_amount")
    if na is not None:
        return float(na)
    up = item.get("unit_price_net") or item.get("unit_price")
    qty = item.get("quantity")
    if up is not None and qty is not None:
        return float(up) * float(qty)
    return 0.0


def _add_totals(fa: Element, data: dict[str, Any]) -> None:
    items = data.get("items", [])
    total_net = data.get("total_net")
    total_vat = data.get("total_vat")
    total_gross = data.get("total_gross")

    if total_net is None and items:
        total_net = sum(_item_net(i) for i in items)
    if total_vat is None and items:
        total_vat = sum(_item_net(i) * _vat_rate_decimal(i.get("vat_rate", 0)) for i in items)
    if total_gross is None and total_net is not None and total_vat is not None:
        total_gross = total_net + total_vat

    if total_net is not None:
        el = SubElement(fa, "P_13_1")
        el.text = f"{total_net:.2f}"

    if total_vat is not None:
        el = SubElement(fa, "P_14_1")
        el.text = f"{total_vat:.2f}"

    if total_gross is not None:
        el = SubElement(fa, "P_15")
        el.text = f"{total_gross:.2f}"


def _add_adnotacje(fa: Element, data: dict[str, Any]) -> None:
    """Add required Adnotacje section per FA(3) schema order."""
    adnotacje = SubElement(fa, "Adnotacje")

    p16 = SubElement(adnotacje, "P_16")
    p16.text = str(data.get("p_16", 2))

    p17 = SubElement(adnotacje, "P_17")
    p17.text = str(data.get("p_17", 2))

    p18 = SubElement(adnotacje, "P_18")
    p18.text = str(data.get("p_18", 2))

    p18a = SubElement(adnotacje, "P_18A")
    p18a.text = str(data.get("p_18a", 2))

    zwolnienie = SubElement(adnotacje, "Zwolnienie")
    p19n = SubElement(zwolnienie, "P_19N")
    p19n.text = str(data.get("p_19n", 1))

    nowe_srodki = SubElement(adnotacje, "NoweSrodkiTransportu")
    p22n = SubElement(nowe_srodki, "P_22N")
    p22n.text = str(data.get("p_22n", 1))

    p_23 = SubElement(adnotacje, "P_23")
    p_23.text = str(data.get("p_23", 2))

    p_marzy = SubElement(adnotacje, "PMarzy")
    p_marzy_n = SubElement(p_marzy, "P_PMarzyN")
    p_marzy_n.text = str(data.get("p_pmarzy_n", 1))


def _add_line_items(fa: Element, items: list[dict[str, Any]]) -> None:
    for idx, item in enumerate(items, 1):
        wiersz = SubElement(fa, "FaWiersz")

        nr_wiersza = SubElement(wiersz, "NrWierszaFa")
        nr_wiersza.text = str(idx)

        desc = item.get("description") or item.get("name", "")
        if desc:
            p7 = SubElement(wiersz, "P_7")
            p7.text = desc

        if item.get("unit"):
            p8a = SubElement(wiersz, "P_8A")
            p8a.text = item["unit"]

        if item.get("quantity") is not None:
            p8b = SubElement(wiersz, "P_8B")
            p8b.text = str(item["quantity"])

        unit_price = item.get("unit_price_net") or item.get("unit_price")
        if unit_price is not None:
            p9a = SubElement(wiersz, "P_9A")
            p9a.text = f"{float(unit_price):.2f}"

        net_amount = item.get("net_amount")
        if net_amount is None and unit_price is not None and item.get("quantity") is not None:
            net_amount = float(unit_price) * float(item["quantity"])
        if net_amount is not None:
            p11 = SubElement(wiersz, "P_11")
            p11.text = f"{float(net_amount):.2f}"

        if item.get("vat_rate") is not None:
            p12 = SubElement(wiersz, "P_12")
            p12.text = str(item["vat_rate"])


def _add_payment(fa: Element, payment: dict[str, Any]) -> None:
    if not payment:
        return

    platnosc = SubElement(fa, "Platnosc")

    if payment.get("paid"):
        zaplacono = SubElement(platnosc, "Zaplacono")
        zaplacono.text = "1"
        if payment.get("payment_date"):
            data_zaplaty = SubElement(platnosc, "DataZaplaty")
            data_zaplaty.text = payment["payment_date"]

    if payment.get("due_date"):
        termin = SubElement(platnosc, "TerminPlatnosci")
        termin_el = SubElement(termin, "Termin")
        termin_el.text = payment["due_date"]

    if payment.get("method"):
        forma = SubElement(platnosc, "FormaPlatnosci")
        forma.text = str(payment["method"])

    if payment.get("bank_account"):
        rachunek = SubElement(platnosc, "RachunekBankowy")
        nr_rachunku = SubElement(rachunek, "NrRB")
        nr_rachunku.text = payment["bank_account"]


def _vat_rate_decimal(rate: int | float | str) -> float:
    """Convert VAT rate to decimal (e.g., 23 -> 0.23)."""
    try:
        r = float(rate)
        return r / 100.0 if r > 1 else r
    except (ValueError, TypeError):
        return 0.0


def validate_invoice_xml(xml_bytes: bytes) -> list[str]:
    """Basic structural validation of invoice XML.

    Returns a list of validation errors (empty if valid).
    Full XSD validation requires the FA(3) schema file.
    """
    errors: list[str] = []

    try:
        from xml.etree.ElementTree import fromstring

        root = fromstring(xml_bytes)
    except Exception as exc:
        return [f"Invalid XML: {exc}"]

    tag = root.tag
    local_tag = tag.split("}")[-1] if "}" in tag else tag
    if local_tag != "Faktura":
        errors.append(f"Root element must be 'Faktura', got '{local_tag}'")

    found_tags = {child.tag.split("}")[-1] if "}" in child.tag else child.tag for child in root}
    for req in ["Naglowek", "Podmiot1", "Podmiot2", "Fa"]:
        if req not in found_tags:
            errors.append(f"Missing required element: {req}")

    return errors
