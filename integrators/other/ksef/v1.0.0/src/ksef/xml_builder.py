"""Invoice XML builder for KSeF FA(3) schema.

Generates XML documents conforming to the FA(3) XSD schema
required by KSeF 2.0 from February 1, 2026.

Namespace: http://crd.gov.pl/wzor/2025/06/25/13775/

Supports two input formats:
- Simplified/internal dict (seller, buyer, items, ...)
- Raw KSeF JSON (podmiot1, podmiot2, fa with P_* fields)
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

logger = logging.getLogger(__name__)

_XSD_DIR = Path(__file__).resolve().parent.parent.parent / "xsd"

FA3_NAMESPACE = "http://crd.gov.pl/wzor/2025/06/25/13775/"
ETD_NAMESPACE = "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

# ---------------------------------------------------------------------------
# Raw KSeF JSON -> XML conversion
# ---------------------------------------------------------------------------

_RAW_KSEF_KEY_MAP: dict[str, str] = {
    "fa": "Fa",
    "podmiot1": "Podmiot1",
    "podmiot2": "Podmiot2",
    "daneIdentyfikacyjne": "DaneIdentyfikacyjne",
    "nip": "NIP",
    "nazwa": "Nazwa",
    "prefiksPodatnika": "PrefiksPodatnika",
    "adres": "Adres",
    "kodKraju": "KodKraju",
    "adresL1": "AdresL1",
    "adresL2": "AdresL2",
    "jST": "JST",
    "gV": "GV",
    "kodWaluty": "KodWaluty",
    "rodzajFaktury": "RodzajFaktury",
    "faWiersz": "FaWiersz",
    "nrWierszaFa": "NrWierszaFa",
    "adnotacje": "Adnotacje",
    "zwolnienie": "Zwolnienie",
    "noweSrodkiTransportu": "NoweSrodkiTransportu",
    "pMarzy": "PMarzy",
    "ppMarzyN": "P_PMarzyN",
    "platnosc": "Platnosc",
    "terminPlatnosci": "TerminPlatnosci",
    "termin": "Termin",
    "terminOpis": "TerminOpis",
    "ilosc": "Ilosc",
    "jednostka": "Jednostka",
    "zdarzeniePoczatkowe": "ZdarzeniePoczatkowe",
    "rachunekBankowy": "RachunekBankowy",
    "nrRb": "NrRB",
    "nazwaBanku": "NazwaBanku",
    "formaPlatnosci": "FormaPlatnosci",
    "zaplacono": "Zaplacono",
    "dataZaplaty": "DataZaplaty",
    "rachunekBankowyFakt662": "RachunekBankowyFakt662",
    "warunkiTransakcji": "WarunkiTransakcji",
    "zamowienie": "Zamowienie",
    "dodatkowyOpis": "DodatkowyOpis",
    "klucz": "Klucz",
    "wartosc": "Wartosc",
    "kursWalutyZ": "KursWalutyZ",
    "faWierszCtrl": "FaWierszCtrl",
    "liczbaWierszyFaktury": "LiczbaWierszyFaktury",
    "wartoscWierszyFaktury": "WartoscWierszyFaktury",
}

_P_FIELD_RE = re.compile(r"^p(\d+)([a-zA-Z]*)$")
_P_COMPOUND_RE = re.compile(r"^p(\d{2,})(\d)([a-zA-Z]*)$")

_ELEMENT_ORDER: dict[str, list[str]] = {
    "Faktura": ["Naglowek", "Podmiot1", "Podmiot2", "Fa"],
    "Podmiot1": ["PrefiksPodatnika", "DaneIdentyfikacyjne", "Adres"],
    "Podmiot2": ["NrEORI", "DaneIdentyfikacyjne", "Adres", "JST", "GV"],
    "DaneIdentyfikacyjne": ["NIP", "Nazwa"],
    "Adres": ["KodKraju", "AdresL1", "AdresL2"],
    "Fa": [
        "KodWaluty",
        "P_1",
        "P_1M",
        "P_2",
        "P_3",
        "P_4",
        "P_5",
        "P_6",
        "OkresFa",
        "P_13_1",
        "P_13_2",
        "P_13_3",
        "P_13_4",
        "P_13_5",
        "P_13_6",
        "P_13_7",
        "P_13_8",
        "P_13_9",
        "P_13_10",
        "P_13_11",
        "P_14_1",
        "P_14_2",
        "P_14_3",
        "P_14_4",
        "P_14_5",
        "P_14_1W",
        "P_14_2W",
        "P_14_3W",
        "P_14_4W",
        "P_14_5W",
        "P_15",
        "KursWalutyZ",
        "Adnotacje",
        "RodzajFaktury",
        "PrzyczynaKorekty",
        "TypKorekty",
        "DaneFaKorygowanej",
        "OkresFaKorygowanej",
        "NrFaKorygowanej",
        "OznaczenieFaZ",
        "FaWiersz",
        "FaWierszCtrl",
        "Platnosc",
        "WarunkiTransakcji",
        "Zamowienie",
        "DodatkowyOpis",
    ],
    "Adnotacje": [
        "P_16",
        "P_17",
        "P_18",
        "P_18A",
        "Zwolnienie",
        "NoweSrodkiTransportu",
        "P_23",
        "PMarzy",
    ],
    "Zwolnienie": ["P_19N", "P_19", "P_19A", "P_19B", "P_19C"],
    "NoweSrodkiTransportu": ["P_22N", "P_22", "P_22A"],
    "PMarzy": ["P_PMarzyN"],
    "FaWiersz": [
        "NrWierszaFa",
        "UU_ID",
        "P_7",
        "IndeksF",
        "CN",
        "P_8A",
        "P_8B",
        "P_9A",
        "P_9B",
        "P_10",
        "P_11",
        "P_11A",
        "P_11Vat",
        "P_12",
        "P_12_XII",
        "P_12_Zal_15",
        "KwotaAkcyzy",
        "GTU",
        "Procedura",
        "KursWaluty",
        "StanPrzed",
    ],
    "Platnosc": [
        "Zaplacono",
        "DataZaplaty",
        "TerminPlatnosci",
        "FormaPlatnosci",
        "RachunekBankowy",
        "RachunekBankowyFakt662",
    ],
    "TerminPlatnosci": ["Termin", "TerminOpis"],
    "TerminOpis": ["Ilosc", "Jednostka", "ZdarzeniePoczatkowe"],
    "RachunekBankowy": ["NrRB", "NazwaBanku", "OpisRachunku"],
}


def _resolve_xml_tag(key: str) -> str:
    """Map a raw KSeF JSON key to the corresponding XML element name."""
    if key in _RAW_KSEF_KEY_MAP:
        return _RAW_KSEF_KEY_MAP[key]

    m = _P_COMPOUND_RE.match(key)
    if m:
        prefix, suffix_digit, alpha = m.groups()
        tag = f"P_{prefix}_{suffix_digit}"
        if alpha:
            tag += alpha.upper() if len(alpha) == 1 else alpha
        return tag

    m = _P_FIELD_RE.match(key)
    if m:
        digits, alpha = m.groups()
        tag = f"P_{digits}"
        if alpha:
            tag += alpha.upper() if len(alpha) == 1 else alpha
        return tag

    return key[0].upper() + key[1:] if key else key


def _sorted_children(parent_tag: str, children: dict[str, Any]) -> list[tuple[str, Any]]:
    """Sort child elements according to FA(3) schema order."""
    order = _ELEMENT_ORDER.get(parent_tag)
    if not order:
        return list(children.items())

    order_map = {tag: i for i, tag in enumerate(order)}

    def sort_key(item: tuple[str, Any]) -> tuple[int, str]:
        tag = item[0]
        return (order_map.get(tag, len(order)), tag)

    return sorted(children.items(), key=sort_key)


def _raw_ksef_to_xml(parent: Element, tag: str, value: Any) -> None:
    """Recursively convert a raw KSeF JSON node to an XML sub-tree."""
    if isinstance(value, list):
        for item in value:
            _raw_ksef_to_xml(parent, tag, item)
        return

    if isinstance(value, dict):
        elem = SubElement(parent, tag)
        resolved: dict[str, Any] = {}
        for k, v in value.items():
            xml_tag = _resolve_xml_tag(k)
            resolved[xml_tag] = v
        for child_tag, child_val in _sorted_children(tag, resolved):
            _raw_ksef_to_xml(elem, child_tag, child_val)
        return

    elem = SubElement(parent, tag)
    if isinstance(value, float):
        elem.text = f"{value:.2f}"
    else:
        elem.text = str(value)


def _preprocess_raw_ksef(data: dict[str, Any]) -> dict[str, Any]:
    """Fix structural issues in raw KSeF JSON before XML generation.

    Handles differences between KSeF JSON key layout and FA(3) XSD:
    - PrefiksPodatnika is only valid in Podmiot1, not Podmiot2
    - P_19* fields belong inside Zwolnienie, not directly in Adnotacje
    - P_22* fields belong inside NoweSrodkiTransportu, not directly in Adnotacje
    """
    import copy

    data = copy.deepcopy(data)

    if "podmiot2" in data and "prefiksPodatnika" in data["podmiot2"]:
        del data["podmiot2"]["prefiksPodatnika"]

    if "fa" in data:
        fa = data["fa"]

        if "adnotacje" in fa:
            adn = fa["adnotacje"]

        zwol_fields = ("p19", "p19A", "p19B", "p19C")
        zwol = adn.get("zwolnienie", {})
        p19n_set = zwol.get("p19N") == 1
        for k in zwol_fields:
            if k in adn:
                val = adn.pop(k)
                if p19n_set or isinstance(val, int):
                    continue
                if "zwolnienie" not in adn:
                    adn["zwolnienie"] = {}
                adn["zwolnienie"][k] = val

            nst_keys = [k for k in ("p22", "p22A") if k in adn]
            if nst_keys:
                if "noweSrodkiTransportu" not in adn:
                    adn["noweSrodkiTransportu"] = {}
                for k in nst_keys:
                    adn["noweSrodkiTransportu"][k] = adn.pop(k)

    return data


def is_raw_ksef_format(data: dict[str, Any]) -> bool:
    return "fa" in data or "podmiot1" in data or "podmiot2" in data


def build_invoice_xml_from_raw_ksef(data: dict[str, Any]) -> bytes:
    """Build FA(3) XML from raw KSeF JSON (podmiot1, podmiot2, fa)."""
    data = _preprocess_raw_ksef(data)
    root = Element("Faktura")
    root.set("xmlns", FA3_NAMESPACE)
    root.set("xmlns:etd", ETD_NAMESPACE)
    root.set("xmlns:xsi", XSI_NAMESPACE)

    _add_header(root, {})

    if "podmiot1" in data:
        _raw_ksef_to_xml(root, "Podmiot1", data["podmiot1"])
    if "podmiot2" in data:
        _raw_ksef_to_xml(root, "Podmiot2", data["podmiot2"])
    if "fa" in data:
        _raw_ksef_to_xml(root, "Fa", data["fa"])

    xml_declaration = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_body = tostring(root, encoding="unicode").encode("utf-8")
    return xml_declaration + xml_body


# ---------------------------------------------------------------------------
# Simplified/internal format -> XML conversion
# ---------------------------------------------------------------------------


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


_xsd_schema_cache: Any = None


def _load_xsd_schema() -> Any:
    """Load and cache the FA(3) XSD schema for validation."""
    global _xsd_schema_cache
    if _xsd_schema_cache is not None:
        return _xsd_schema_cache

    schema_path = _XSD_DIR / "schemat.xsd"
    if not schema_path.exists():
        logger.warning("XSD schema not found at %s — skipping XSD validation", schema_path)
        return None

    try:
        from lxml import etree as lxml_etree

        parser = lxml_etree.XMLParser()
        parser.resolvers.add(_make_local_xsd_resolver())
        schema_doc = lxml_etree.parse(str(schema_path), parser)
        _xsd_schema_cache = lxml_etree.XMLSchema(schema_doc)
        logger.info("FA(3) XSD schema loaded from %s", schema_path)
    except Exception:
        logger.exception("Failed to load XSD schema")
        return None

    return _xsd_schema_cache


def _make_local_xsd_resolver() -> Any:
    """Create an lxml Resolver that maps remote XSD URLs to local files."""
    from lxml import etree as lxml_etree

    url_to_local = {
        "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/StrukturyDanych_v10-0E.xsd": "StrukturyDanych_v10-0E.xsd",
        "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/ElementarneTypyDanych_v10-0E.xsd": "ElementarneTypyDanych_v10-0E.xsd",
        "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/KodyKrajow_v10-0E.xsd": "KodyKrajow_v10-0E.xsd",
    }

    class _Resolver(lxml_etree.Resolver):
        def resolve(self, system_url: str, public_id: str, context: Any) -> Any:
            local_name = url_to_local.get(system_url)
            if local_name:
                local_path = _XSD_DIR / local_name
                if local_path.exists():
                    return self.resolve_filename(str(local_path), context)
            return None

    return _Resolver()


def validate_invoice_xml(xml_bytes: bytes) -> list[str]:
    """Validate invoice XML against the FA(3) XSD schema.

    Returns a list of validation errors (empty if valid).
    Falls back to basic structural checks if XSD is unavailable.
    """
    errors: list[str] = []

    schema = _load_xsd_schema()
    if schema is not None:
        try:
            from lxml import etree as lxml_etree

            doc = lxml_etree.fromstring(xml_bytes)
            if not schema.validate(doc):
                for err in schema.error_log:
                    errors.append(f"Line {err.line}: {err.message}")
            return errors
        except Exception as exc:
            return [f"XML parsing failed: {exc}"]

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
