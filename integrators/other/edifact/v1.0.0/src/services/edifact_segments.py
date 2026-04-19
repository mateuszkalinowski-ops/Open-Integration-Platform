"""EDIFACT segment definitions for intermodal rail messages.

Provides segment tag metadata, qualifier lookup tables, and SMDG code lists
used by the parser and builder for COPRAR/COPARN/COHAOR/COARRI/IFTSTA/APERAK/CONTRL.
"""

from __future__ import annotations

MSG_TYPES = frozenset(
    {
        "COPRAR",
        "COPARN",
        "COHAOR",
        "COARRI",
        "CODECO",
        "BAPLIE",
        "IFTMIN",
        "IFTSTA",
        "APERAK",
        "CONTRL",
    }
)

VERSIONS = frozenset({"D95B", "D00B", "D03B", "SMDG2.0"})

FUNCTION_CODES = {
    "9": "original",
    "1": "cancel",
    "5": "replace",
    "4": "change",
    "31": "copy",
    "46": "provisional",
}

FUNCTION_CODE_REVERSE = {v: k for k, v in FUNCTION_CODES.items()}

TRANSPORT_MODE_CODES = {
    "1": "maritime",
    "2": "rail",
    "3": "road",
    "4": "air",
    "8": "inland_waterway",
}

EQUIPMENT_STATUS_CODES = {
    "1": "continental",
    "2": "export",
    "3": "import",
    "4": "transit",
    "5": "transhipment",
    "6": "repositioning",
}

FULL_EMPTY_CODES = {
    "4": "empty",
    "5": "full",
}

MOVEMENT_TYPE_CODES = {
    "1": "gate_in",
    "2": "gate_out",
    "3": "load",
    "4": "discharge",
    "5": "shift",
    "6": "restow",
    "7": "inspection",
}

LOCATION_QUALIFIER = {
    "5": "port_of_loading",
    "11": "port_of_discharge",
    "9": "place_of_loading",
    "12": "place_of_delivery",
    "147": "stowage_cell",
    "88": "place_of_receipt",
    "165": "terminal",
}

PARTY_QUALIFIER = {
    "CA": "carrier",
    "CF": "ship_agent",
    "CZ": "consignee",
    "FW": "freight_forwarder",
    "HE": "haulier",
    "SH": "shipper",
    "OO": "operator",
    "MR": "terminal_operator",
}

SMDG_STATUS_CODES = {
    "EAR": "Estimated arrival reported",
    "ARR": "Arrival reported",
    "GTI": "Gate in",
    "GTO": "Gate out",
    "DIS": "Discharged",
    "LOA": "Loaded",
    "CAN": "Cancelled",
    "VGM": "Verified gross mass",
    "DEP": "Departed",
    "ATA": "Actual time of arrival",
    "ATD": "Actual time of departure",
    "RST": "Restow",
    "SHF": "Shifted",
    "INS": "Inspection",
    "WGH": "Weighing",
    "PKU": "Pick up",
    "DLV": "Delivery",
}

TOS_STATUS_TO_SMDG = {
    "AWK_AWIZOWANY": "EAR",
    "AWK_ZAAKCEPTOWANY": "ARR",
    "ZDB_WJAZD_KOLEJOWY_POTWIERDZONY": "GTI",
    "PRZ_WYLADUNEK_ZAKONCZONY": "DIS",
    "PRZ_ZALADUNEK_ZAKONCZONY": "LOA",
    "ZDB_WYJAZD_KOLEJOWY_POTWIERDZONY": "GTO",
    "AWD_WJAZD_DROGOWY": "GTI",
    "AWD_WYJAZD_DROGOWY": "GTO",
    "PRZ_ANULOWANE": "CAN",
    "WJAZD_TIR_POTWIERDZONY": "GTI",
    "WYJAZD_TIR_POTWIERDZONY": "GTO",
    "PRZELAD_ZAKONCZONY": "DIS",
    "POCIAG_PRZYJECHAL": "ATA",
    "POCIAG_ODJECHAL": "ATD",
}

APERAK_ERROR_CODES = {
    "2": "Syntax error",
    "7": "Missing segment",
    "12": "Invalid value",
    "13": "Missing mandatory element",
    "14": "Data element too long",
    "15": "Data element too short",
    "22": "Invalid character",
    "27": "Dataset error",
    "35": "Too many occurrences",
}

SEAL_TYPE_CODES = {
    "AA": "wire_seal",
    "AB": "bolt_seal",
    "AE": "electronic_seal",
    "CA": "customs_seal",
    "SH": "shipper_seal",
}

DTM_QUALIFIER = {
    "132": "estimated_arrival",
    "133": "estimated_departure",
    "137": "document_date",
    "178": "actual_arrival",
    "186": "actual_departure",
    "2": "delivery_date",
    "191": "loading_date",
    "200": "pick_up_date",
    "63": "latest_date",
    "64": "earliest_date",
}
