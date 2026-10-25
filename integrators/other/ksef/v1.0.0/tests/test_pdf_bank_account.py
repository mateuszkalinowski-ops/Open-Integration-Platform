"""Bank account (Platnosc/RachunekBankowy) on the invoice PDF."""

import re
from typing import Any
from xml.etree.ElementTree import fromstring

from reportlab.platypus import Paragraph
from src.ksef import pdf_renderer
from src.ksef.pdf_renderer import _add_payment, _build_styles, _format_account_number, _parse_invoice
from src.ksef.xml_builder import build_invoice_xml

from tests.test_xml_builder import SAMPLE_INVOICE_DATA

NS = pdf_renderer.FA3_NS.strip("{}")

MULTI_ACCOUNT_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="{NS}">
  <Fa>
    <KodWaluty>PLN</KodWaluty><P_1>2026-10-25</P_1><P_2>FV/10/10/2026</P_2><P_15>123.00</P_15>
    <Platnosc>
      <TerminPlatnosci><Termin>2026-11-01</Termin></TerminPlatnosci>
      <FormaPlatnosci>6</FormaPlatnosci>
      <RachunekBankowy><NrRB>PL58105015591000009033071052</NrRB><NazwaBanku>ING</NazwaBanku></RachunekBankowy>
      <RachunekBankowy>
        <NrRB>DE89370400440532013000</NrRB><SWIFT>COBADEFFXXX</SWIFT>
        <NazwaBanku>Commerz &amp; Bank</NazwaBanku><OpisRachunku>EUR</OpisRachunku>
      </RachunekBankowy>
      <RachunekBankowyFakt662><NrRB>PL61109010140000071219812874</NrRB></RachunekBankowyFakt662>
    </Platnosc>
  </Fa>
</Faktura>
"""


def _payment_lines(inv: dict[str, Any]) -> list[str]:
    elements: list[Any] = []
    _add_payment(elements, _build_styles(), inv)
    return [re.sub(r"<[^>]+>", "", e.text) for e in elements if isinstance(e, Paragraph)]


def test_format_account_number_in_groups_of_four() -> None:
    assert _format_account_number("PL58105015591000009033071052") == "PL58 1050 1559 1000 0090 3307 1052"
    assert _format_account_number("58 1050 1559 1000 0090 3307 1052") == "5810 5015 5910 0000 9033 0710 52"


def test_account_from_builder_xml_is_printed() -> None:
    inv = _parse_invoice(fromstring(build_invoice_xml(SAMPLE_INVOICE_DATA)))
    assert [a["number"] for a in inv["payment"]["bank_accounts"]] == ["PL12345678901234567890123456"]
    assert any(
        "Rachunek bankowy:" in line and "PL12 3456 7890 1234 5678 9012 3456" in line for line in _payment_lines(inv)
    )


def test_multiple_accounts_swift_description_and_factor() -> None:
    inv = _parse_invoice(fromstring(MULTI_ACCOUNT_XML.encode("utf-8")))
    lines = [line for line in _payment_lines(inv) if "Rachunek" in line]
    assert lines == [
        "Rachunek bankowy: PL58 1050 1559 1000 0090 3307 1052 (ING)",
        "Rachunek bankowy: DE89 3704 0044 0532 0130 00 (Commerz &amp; Bank), SWIFT: COBADEFFXXX — EUR",
        "Rachunek faktora: PL61 1090 1014 0000 0712 1981 2874",
    ]


def test_pdf_renders_with_accounts() -> None:
    pdf = pdf_renderer.render_invoice_pdf(MULTI_ACCOUNT_XML, ksef_number="5273148508-20261025-5CA9B7C00000-B3")
    assert pdf.startswith(b"%PDF")
