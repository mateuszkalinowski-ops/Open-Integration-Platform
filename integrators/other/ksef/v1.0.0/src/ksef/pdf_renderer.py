"""Render KSeF FA(3) invoice XML to PDF — official KSeF visualization style."""

from __future__ import annotations

import io
import logging
import os
from typing import Any
from xml.etree.ElementTree import Element, fromstring

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

_FONT_REGISTERED = False
_FONT_NAME = "Helvetica"
_FONT_NAME_BOLD = "Helvetica-Bold"

_DEJAVU_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]


def _register_fonts() -> None:
    global _FONT_REGISTERED, _FONT_NAME, _FONT_NAME_BOLD
    if _FONT_REGISTERED:
        return
    _FONT_REGISTERED = True

    regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    if os.path.exists(regular) and os.path.exists(bold):
        pdfmetrics.registerFont(TTFont("DejaVuSans", regular))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold))
        registerFontFamily("DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold")
        _FONT_NAME = "DejaVuSans"
        _FONT_NAME_BOLD = "DejaVuSans-Bold"
        logger.info("Registered DejaVuSans font for PDF rendering")
    elif os.path.exists(regular):
        pdfmetrics.registerFont(TTFont("DejaVuSans", regular))
        _FONT_NAME = "DejaVuSans"
        _FONT_NAME_BOLD = "DejaVuSans"
        logger.info("Registered DejaVuSans (regular only) for PDF rendering")


FA3_NS = "{http://crd.gov.pl/wzor/2025/06/25/13775/}"

_COLOR_TEXT = colors.HexColor("#333333")
_COLOR_LABEL = colors.HexColor("#555555")
_COLOR_RED = colors.HexColor("#C0392B")
_COLOR_LINE = colors.HexColor("#CCCCCC")
_COLOR_TABLE_BORDER = colors.HexColor("#BBBBBB")
_COLOR_TABLE_HEADER_BG = colors.HexColor("#F5F5F5")

PAYMENT_METHOD_LABELS = {
    "1": "Gotówka",
    "2": "Karta",
    "3": "Bon",
    "4": "Czek",
    "5": "Kredyt",
    "6": "Przelew",
    "7": "Płatność mobilna",
}

INVOICE_TYPE_LABELS = {
    "VAT": "Faktura podstawowa",
    "KOR": "Faktura korygująca",
    "ZAL": "Faktura zaliczkowa",
    "ROZ": "Faktura rozliczeniowa",
    "UPR": "Faktura uproszczona",
}

VAT_RATE_LABELS = {
    "23": "23%",
    "22": "22%",
    "8": "8%",
    "7": "7%",
    "5": "5%",
    "0": "0%",
    "zw": "zw",
    "np": "np.",
    "oo": "o.o.",
}


KSEF_VERIFY_URLS = {
    "test": "https://ksef-test.mf.gov.pl/web/verify",
    "demo": "https://ksef-demo.mf.gov.pl/web/verify",
    "production": "https://ksef.mf.gov.pl/web/verify",
}


def render_invoice_pdf(
    invoice_xml: str | bytes,
    ksef_number: str = "",
    environment: str = "demo",
) -> bytes:
    _register_fonts()

    if isinstance(invoice_xml, str):
        invoice_xml = invoice_xml.encode("utf-8")

    root = fromstring(invoice_xml)
    inv = _parse_invoice(root)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    s = _build_styles()
    elements: list[Any] = []

    _add_header(elements, s, inv, ksef_number)
    _hr(elements)
    _add_parties(elements, s, inv)
    _hr(elements)
    _add_details(elements, s, inv)
    _hr(elements)
    _add_line_items(elements, s, inv)
    _add_vat_summary(elements, s, inv)
    _hr(elements)
    _add_payment(elements, s, inv)
    _hr(elements)
    _add_footer(elements, s, ksef_number, environment)

    doc.build(elements)
    return buf.getvalue()


# ── XML parsing ──────────────────────────────────────────────────────


def _safe_float(val: str | float | int) -> float:
    try:
        return float(val) if val else 0.0
    except (ValueError, TypeError):
        return 0.0


def _ft(root: Element | None, path: str) -> str:
    if root is None:
        return ""
    parts = path.split("/")
    el = root
    for p in parts:
        child = el.find(f"{FA3_NS}{p}")
        if child is None:
            return ""
        el = child
    return (el.text or "").strip()


def _parse_invoice(root: Element) -> dict[str, Any]:
    fa = root.find(f"{FA3_NS}Fa") or root.find("Fa")

    inv: dict[str, Any] = {
        "invoice_number": _ft(fa, "P_2"),
        "issue_date": _ft(fa, "P_1"),
        "issue_place": _ft(fa, "P_1M"),
        "sale_date": _ft(fa, "P_6"),
        "currency": _ft(fa, "KodWaluty") or "PLN",
        "invoice_type": _ft(fa, "RodzajFaktury") or "VAT",
    }

    inv["seller"] = _parse_party(root, "Podmiot1")
    inv["buyer"] = _parse_party(root, "Podmiot2")
    inv["items"] = _parse_items(fa)

    total_net = _safe_float(_ft(fa, "P_13_1"))
    total_vat = _safe_float(_ft(fa, "P_14_1"))
    total_gross = _safe_float(_ft(fa, "P_15"))

    if total_net == 0 and inv["items"]:
        total_net = sum(_safe_float(i.get("net_amount", "0")) for i in inv["items"])
    if total_vat == 0 and inv["items"]:
        for item in inv["items"]:
            net = _safe_float(item.get("net_amount", "0"))
            rate = _safe_float(item.get("vat_rate", "0"))
            total_vat += net * rate / 100
    if total_gross == 0:
        total_gross = total_net + total_vat

    inv["total_net"] = f"{total_net:.2f}"
    inv["total_vat"] = f"{total_vat:.2f}"
    inv["total_gross"] = f"{total_gross:.2f}"

    payment = fa.find(f"{FA3_NS}Platnosc") if fa is not None else None
    if payment is not None:
        inv["payment"] = {
            "method": _ft(payment, "FormaPlatnosci"),
            "due_date": _ft(payment, "TerminPlatnosci/Termin"),
            "paid": _ft(payment, "Zaplacono") == "1",
            "payment_date": _ft(payment, "DataZaplaty"),
        }
    else:
        inv["payment"] = {}

    return inv


def _parse_party(root: Element, tag: str) -> dict[str, str]:
    podmiot = root.find(f"{FA3_NS}{tag}") or root.find(tag)
    if podmiot is None:
        return {"nip": "", "name": "", "address_line1": "", "address_line2": ""}
    return {
        "nip": _ft(podmiot, "DaneIdentyfikacyjne/NIP"),
        "name": _ft(podmiot, "DaneIdentyfikacyjne/Nazwa"),
        "address_line1": _ft(podmiot, "Adres/AdresL1"),
        "address_line2": _ft(podmiot, "Adres/AdresL2"),
    }


def _parse_items(fa: Element | None) -> list[dict[str, str]]:
    if fa is None:
        return []
    items = []
    for w in fa.findall(f"{FA3_NS}FaWiersz"):
        items.append(
            {
                "lp": _ft(w, "NrWierszaFa"),
                "description": _ft(w, "P_7"),
                "unit": _ft(w, "P_8A"),
                "quantity": _ft(w, "P_8B"),
                "unit_price_net": _ft(w, "P_9A"),
                "unit_price_gross": _ft(w, "P_9B"),
                "net_amount": _ft(w, "P_11"),
                "vat_rate": _ft(w, "P_12"),
            }
        )
    return items


# ── Styles ───────────────────────────────────────────────────────────


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    fn = _FONT_NAME
    fnb = _FONT_NAME_BOLD
    return {
        "ksef_title": ParagraphStyle(
            "KsefTitle",
            parent=base["Normal"],
            fontSize=14,
            leading=18,
            fontName=fn,
            textColor=_COLOR_TEXT,
        ),
        "inv_number": ParagraphStyle(
            "InvNumber",
            parent=base["Normal"],
            fontSize=16,
            leading=20,
            fontName=fnb,
            alignment=TA_RIGHT,
            textColor=_COLOR_TEXT,
        ),
        "inv_type": ParagraphStyle(
            "InvType",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            fontName=fn,
            alignment=TA_RIGHT,
            textColor=_COLOR_LABEL,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Normal"],
            fontSize=11,
            leading=14,
            fontName=fnb,
            textColor=_COLOR_TEXT,
            spaceBefore=2 * mm,
            spaceAfter=2 * mm,
        ),
        "label": ParagraphStyle(
            "Label",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            fontName=fnb,
            textColor=_COLOR_TEXT,
        ),
        "value": ParagraphStyle(
            "Value",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            fontName=fn,
            textColor=_COLOR_TEXT,
        ),
        "label_small": ParagraphStyle(
            "LabelSmall",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            fontName=fnb,
            textColor=_COLOR_LABEL,
        ),
        "value_small": ParagraphStyle(
            "ValueSmall",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            fontName=fn,
            textColor=_COLOR_TEXT,
        ),
        "sub_header": ParagraphStyle(
            "SubHeader",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            fontName=fn,
            textColor=_COLOR_LABEL,
            spaceAfter=1 * mm,
        ),
        "right": ParagraphStyle(
            "Right",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            fontName=fn,
            alignment=TA_RIGHT,
            textColor=_COLOR_TEXT,
        ),
        "right_bold": ParagraphStyle(
            "RightBold",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            fontName=fnb,
            alignment=TA_RIGHT,
            textColor=_COLOR_TEXT,
        ),
        "total": ParagraphStyle(
            "Total",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            fontName=fnb,
            alignment=TA_RIGHT,
            textColor=_COLOR_TEXT,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontSize=7,
            leading=9,
            fontName=fn,
            textColor=_COLOR_LABEL,
        ),
        "qr_title": ParagraphStyle(
            "QrTitle",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            fontName=fnb,
            alignment=TA_RIGHT,
            textColor=_COLOR_TEXT,
        ),
        "qr_label": ParagraphStyle(
            "QrLabel",
            parent=base["Normal"],
            fontSize=7,
            leading=9,
            fontName=fn,
            alignment=TA_CENTER,
            textColor=_COLOR_RED,
        ),
    }


# ── Helpers ──────────────────────────────────────────────────────────


def _hr(elements: list[Any], thickness: float = 0.5) -> None:
    elements.append(Spacer(1, 2 * mm))
    elements.append(
        HRFlowable(
            width="100%",
            thickness=thickness,
            color=_COLOR_LINE,
            spaceBefore=0,
            spaceAfter=0,
        )
    )
    elements.append(Spacer(1, 2 * mm))


def _label_value(s: dict, label: str, value: str) -> Paragraph:
    return Paragraph(f"<b>{label}:</b> {value}", s["value"])


# ── Section builders ─────────────────────────────────────────────────


def _add_header(
    elements: list[Any],
    s: dict[str, ParagraphStyle],
    inv: dict[str, Any],
    ksef_number: str,
) -> None:
    inv_type = INVOICE_TYPE_LABELS.get(inv["invoice_type"], f"Faktura {inv['invoice_type']}")
    inv_number = inv.get("invoice_number", "")

    title_text = 'Krajowy System <font color="#C0392B"><b>e</b></font> -Faktur'

    header_data = [
        [
            Paragraph(title_text, s["ksef_title"]),
            Paragraph("Numer faktury", s["inv_type"]),
        ]
    ]
    elements.append(
        Table(
            header_data,
            colWidths=[9 * cm, 8 * cm],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )
    )

    elements.append(Paragraph(inv_number, s["inv_number"]))
    elements.append(Paragraph(inv_type, s["inv_type"]))

    if ksef_number:
        elements.append(Paragraph(f"Numer KSeF: {ksef_number}", s["inv_type"]))


def _add_parties(
    elements: list[Any],
    s: dict[str, ParagraphStyle],
    inv: dict[str, Any],
) -> None:
    seller = inv.get("seller", {})
    buyer = inv.get("buyer", {})

    seller_cells = [
        [Paragraph("<b>Sprzedawca</b>", s["section"]), Paragraph("<b>Nabywca</b>", s["section"])],
    ]

    if seller.get("nip") or buyer.get("nip"):
        seller_cells.append(
            [
                _label_value(s, "NIP", seller.get("nip", "")),
                _label_value(s, "NIP", buyer.get("nip", "")),
            ]
        )

    seller_cells.append(
        [
            _label_value(s, "Nazwa", seller.get("name", "")),
            _label_value(s, "Nazwa", buyer.get("name", "")),
        ]
    )

    addr_s = seller.get("address_line1", "")
    if seller.get("address_line2"):
        addr_s += f"<br/>{seller['address_line2']}"
    addr_b = buyer.get("address_line1", "")
    if buyer.get("address_line2"):
        addr_b += f"<br/>{buyer['address_line2']}"

    if addr_s or addr_b:
        seller_cells.append(
            [
                Paragraph("Adres", s["sub_header"]),
                Paragraph("Adres", s["sub_header"]),
            ]
        )
        seller_cells.append(
            [
                Paragraph(addr_s or "-", s["value"]),
                Paragraph(addr_b or "-", s["value"]),
            ]
        )
        seller_cells.append(
            [
                Paragraph("PL", s["value"]),
                Paragraph("PL", s["value"]),
            ]
        )

    page_w = A4[0] - 4 * cm
    col_w = page_w / 2

    t = Table(seller_cells, colWidths=[col_w, col_w])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    elements.append(t)


def _add_details(
    elements: list[Any],
    s: dict[str, ParagraphStyle],
    inv: dict[str, Any],
) -> None:
    elements.append(Paragraph("<b>Szczegóły</b>", s["section"]))

    page_w = A4[0] - 4 * cm
    col_w = page_w / 2

    detail_rows = []

    row1 = []
    if inv.get("issue_date"):
        row1.append(_label_value(s, "Data wystawienia", inv["issue_date"]))
    else:
        row1.append(Paragraph("", s["value"]))
    if inv.get("sale_date"):
        row1.append(_label_value(s, "Data dostawy/wykonania usługi", inv["sale_date"]))
    else:
        row1.append(Paragraph("", s["value"]))
    detail_rows.append(row1)

    row2 = [_label_value(s, "Waluta", inv.get("currency", "PLN")), Paragraph("", s["value"])]
    detail_rows.append(row2)

    t = Table(detail_rows, colWidths=[col_w, col_w])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    elements.append(t)


def _add_line_items(
    elements: list[Any],
    s: dict[str, ParagraphStyle],
    inv: dict[str, Any],
) -> None:
    elements.append(Paragraph("<b>Pozycje</b>", s["section"]))
    elements.append(Spacer(1, 1 * mm))

    header = [
        Paragraph("<b>Lp.</b>", s["label_small"]),
        Paragraph("<b>Nazwa towaru lub usługi</b>", s["label_small"]),
        Paragraph("<b>Cena jedn. netto</b>", s["label_small"]),
        Paragraph("<b>Ilość</b>", s["label_small"]),
        Paragraph("<b>Miara</b>", s["label_small"]),
        Paragraph("<b>Vat</b>", s["label_small"]),
        Paragraph("<b>Wartość netto</b>", s["label_small"]),
    ]

    data = [header]
    for item in inv.get("items", []):
        vat_str = VAT_RATE_LABELS.get(item.get("vat_rate", ""), item.get("vat_rate", ""))
        price = item.get("unit_price_net") or item.get("unit_price_gross", "")
        data.append(
            [
                Paragraph(item.get("lp", ""), s["value_small"]),
                Paragraph(item.get("description", ""), s["value_small"]),
                Paragraph(price, s["value_small"]),
                Paragraph(item.get("quantity", ""), s["value_small"]),
                Paragraph(item.get("unit", ""), s["value_small"]),
                Paragraph(vat_str, s["value_small"]),
                Paragraph(item.get("net_amount", ""), s["value_small"]),
            ]
        )

    col_widths = [1 * cm, 6 * cm, 2.2 * cm, 1.5 * cm, 1.3 * cm, 1.3 * cm, 2.7 * cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _COLOR_TABLE_HEADER_BG),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, _COLOR_TABLE_BORDER),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, _COLOR_TABLE_BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t)

    currency = inv.get("currency", "PLN")
    gross = inv.get("total_gross", "0.00")
    elements.append(Spacer(1, 2 * mm))
    elements.append(
        Paragraph(
            f"Kwota należności ogółem: <b>{gross}{currency}</b>",
            s["total"],
        )
    )


def _add_vat_summary(
    elements: list[Any],
    s: dict[str, ParagraphStyle],
    inv: dict[str, Any],
) -> None:
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("<b>Podsumowanie VAT</b>", s["section"]))
    elements.append(Spacer(1, 1 * mm))

    header = [
        Paragraph("<b>Lp.</b>", s["label_small"]),
        Paragraph("<b>Stawka podatku</b>", s["label_small"]),
        Paragraph("<b>Kwota netto</b>", s["label_small"]),
        Paragraph("<b>Kwota podatku</b>", s["label_small"]),
        Paragraph("<b>Kwota brutto</b>", s["label_small"]),
    ]

    vat_groups: dict[str, dict[str, float]] = {}
    for item in inv.get("items", []):
        rate_key = item.get("vat_rate", "0")
        if rate_key not in vat_groups:
            vat_groups[rate_key] = {"net": 0.0, "vat": 0.0, "gross": 0.0}
        try:
            net = float(item.get("net_amount", 0))
            rate_val = float(rate_key) if rate_key.replace(".", "").isdigit() else 0
            vat_amount = net * rate_val / 100
            vat_groups[rate_key]["net"] += net
            vat_groups[rate_key]["vat"] += vat_amount
            vat_groups[rate_key]["gross"] += net + vat_amount
        except (ValueError, TypeError):
            pass

    data = [header]
    for idx, (rate_key, vals) in enumerate(vat_groups.items(), start=1):
        rate_label = VAT_RATE_LABELS.get(rate_key, f"{rate_key}%")
        data.append(
            [
                Paragraph(str(idx), s["value_small"]),
                Paragraph(rate_label, s["value_small"]),
                Paragraph(f"{vals['net']:.2f}", s["value_small"]),
                Paragraph(f"{vals['vat']:.2f}", s["value_small"]),
                Paragraph(f"{vals['gross']:.2f}", s["value_small"]),
            ]
        )

    col_widths = [1 * cm, 3.5 * cm, 3.5 * cm, 4 * cm, 4 * cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _COLOR_TABLE_HEADER_BG),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, _COLOR_TABLE_BORDER),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, _COLOR_TABLE_BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t)


def _add_payment(
    elements: list[Any],
    s: dict[str, ParagraphStyle],
    inv: dict[str, Any],
) -> None:
    elements.append(Paragraph("<b>Płatność</b>", s["section"]))

    payment = inv.get("payment", {})
    if not payment:
        return

    if payment.get("paid"):
        elements.append(_label_value(s, "Informacja o płatności", "Zapłacono"))
    if payment.get("payment_date"):
        elements.append(_label_value(s, "Data zapłaty", payment["payment_date"]))

    if payment.get("due_date"):
        elements.append(_label_value(s, "Termin płatności", payment["due_date"]))

    method = payment.get("method", "")
    if method:
        label = PAYMENT_METHOD_LABELS.get(method, method)
        elements.append(_label_value(s, "Forma płatności", label))

    currency = inv.get("currency", "PLN")
    gross = inv.get("total_gross", "0.00")
    elements.append(_label_value(s, "Kwota należności ogółem", f"{gross}{currency}"))
    elements.append(_label_value(s, "Waluta", currency))


def _make_qr_drawing(data: str, size: float = 35 * mm) -> Drawing:
    qr = QrCodeWidget(data, barLevel="M")
    qr.barWidth = size
    qr.barHeight = size
    d = Drawing(size, size)
    d.add(qr)
    return d


def _add_footer(
    elements: list[Any],
    s: dict[str, ParagraphStyle],
    ksef_number: str,
    environment: str = "demo",
) -> None:
    if ksef_number:
        _hr(elements)

        base_url = KSEF_VERIFY_URLS.get(environment, KSEF_VERIFY_URLS["demo"])
        verify_url = f"{base_url}/{ksef_number}"
        qr_drawing = _make_qr_drawing(verify_url)

        qr_title = Paragraph("Sprawdzenie faktury w KSeF", s["qr_title"])
        qr_number = Paragraph(ksef_number, s["qr_label"])

        qr_cell = [qr_drawing, Spacer(1, 2 * mm), qr_number]

        page_w = A4[0] - 4 * cm
        data = [
            [
                Paragraph("", s["footer"]),
                qr_title,
            ],
            [
                Paragraph(
                    "Dokument wygenerowany z Krajowego Systemu e-Faktur (KSeF).<br/>"
                    "Faktura ustrukturyzowana nie wymaga podpisu.",
                    s["footer"],
                ),
                qr_cell,
            ],
        ]

        t = Table(data, colWidths=[page_w - 5 * cm, 5 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(t)
    else:
        elements.append(Spacer(1, 8 * mm))
        elements.append(
            Paragraph(
                "Dokument wygenerowany z Krajowego Systemu e-Faktur (KSeF). "
                "Faktura ustrukturyzowana nie wymaga podpisu.",
                s["footer"],
            )
        )
