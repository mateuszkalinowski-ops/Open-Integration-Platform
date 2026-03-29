"""Tests for KSeF XML invoice builder."""

from xml.etree.ElementTree import fromstring

import pytest

from src.ksef.xml_builder import build_invoice_xml, validate_invoice_xml


SAMPLE_INVOICE_DATA = {
    "invoice_number": "FV/2026/001",
    "issue_date": "2026-03-29",
    "sale_date": "2026-03-29",
    "currency": "PLN",
    "seller": {
        "nip": "1234567890",
        "name": "Firma Testowa Sp. z o.o.",
        "address": {
            "country": "PL",
            "city": "Warszawa",
            "street": "ul. Testowa 1",
            "postal_code": "00-001",
        },
    },
    "buyer": {
        "nip": "0987654321",
        "name": "Firma Nabywca S.A.",
        "address": {
            "country": "PL",
            "city": "Kraków",
            "street": "ul. Kupiecka 5",
            "postal_code": "30-001",
        },
    },
    "items": [
        {
            "description": "Usługa informatyczna",
            "quantity": 10,
            "unit": "godz.",
            "unit_price_net": 200.00,
            "net_amount": 2000.00,
            "vat_rate": 23,
            "vat_amount": 460.00,
            "gross_amount": 2460.00,
        },
        {
            "description": "Licencja oprogramowania",
            "quantity": 1,
            "unit": "szt.",
            "unit_price_net": 5000.00,
            "net_amount": 5000.00,
            "vat_rate": 23,
            "vat_amount": 1150.00,
            "gross_amount": 6150.00,
        },
    ],
    "total_net": 7000.00,
    "total_vat": 1610.00,
    "total_gross": 8610.00,
    "payment": {
        "method": "przelew",
        "due_date": "2026-04-28",
        "bank_account": "PL12345678901234567890123456",
    },
}


class TestBuildInvoiceXml:
    def test_generates_valid_xml(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        assert xml_bytes.startswith(b'<?xml version="1.0" encoding="UTF-8"?>')

    def test_root_element_is_faktura(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        content = xml_bytes.split(b"?>", 1)[1]
        root = fromstring(content)
        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        assert tag == "Faktura"

    def test_contains_seller_nip(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        assert b"1234567890" in xml_bytes

    def test_contains_buyer_nip(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        assert b"0987654321" in xml_bytes

    def test_contains_invoice_number(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        assert b"FV/2026/001" in xml_bytes

    def test_contains_line_items(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        xml_str = xml_bytes.decode("utf-8")
        assert "FaWiersz" in xml_str
        assert "Usługa informatyczna" in xml_str
        assert "Licencja oprogramowania" in xml_str

    def test_contains_totals(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        assert b"7000.00" in xml_bytes
        assert b"8610.00" in xml_bytes

    def test_contains_payment_info(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        assert b"przelew" in xml_bytes
        assert b"PL12345678901234567890123456" in xml_bytes

    def test_line_item_count(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        assert b"<LiczbaWierszyFaktur>2</LiczbaWierszyFaktur>" in xml_bytes

    def test_minimal_invoice(self) -> None:
        minimal = {
            "invoice_number": "FV/001",
            "seller": {"nip": "1111111111", "name": "Seller"},
            "buyer": {"nip": "2222222222", "name": "Buyer"},
            "items": [{"description": "Item", "quantity": 1, "net_amount": 100}],
            "total_gross": 123.00,
        }
        xml_bytes = build_invoice_xml(minimal)
        assert b"FV/001" in xml_bytes
        assert b"1111111111" in xml_bytes


class TestValidateInvoiceXml:
    def test_valid_xml_returns_no_errors(self) -> None:
        xml_bytes = build_invoice_xml(SAMPLE_INVOICE_DATA)
        errors = validate_invoice_xml(xml_bytes)
        assert errors == []

    def test_invalid_xml_returns_errors(self) -> None:
        errors = validate_invoice_xml(b"not xml at all")
        assert len(errors) > 0
        assert "Invalid XML" in errors[0]

    def test_wrong_root_element(self) -> None:
        errors = validate_invoice_xml(b"<Document><child/></Document>")
        assert any("Faktura" in e for e in errors)

    def test_missing_required_elements(self) -> None:
        errors = validate_invoice_xml(b"<Faktura><Naglowek/></Faktura>")
        missing = [e for e in errors if "Missing" in e]
        assert len(missing) > 0
