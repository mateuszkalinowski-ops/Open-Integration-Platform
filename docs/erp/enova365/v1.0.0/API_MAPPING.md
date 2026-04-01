# enova365 — Field Mapping Reference

> **Note**: This mapping will be completed once the enova365 API documentation is available. Fields below are based on standard enova365 data model structure.

## Contractors (Kontrahenci)

| Platform Field | enova365 API Field | Notes |
|---|---|---|
| `id` | `Id` | Internal enova365 ID |
| `symbol` | `Kod` | Contractor code |
| `contractor_type` | `Typ` | Company / Person |
| `short_name` | `NazwaSkrocona` | |
| `full_name` | `Nazwa` | Full company name |
| `nip` | `NIP` | Tax identification number |
| `regon` | `REGON` | |
| `pesel` | `PESEL` | Person only |
| `first_name` | `Imie` | Person only |
| `last_name` | `Nazwisko` | Person only |
| `addresses[].street` | `Adres.Ulica` | |
| `addresses[].house_number` | `Adres.NrDomu` | |
| `addresses[].apartment_number` | `Adres.NrLokalu` | |
| `addresses[].postal_code` | `Adres.KodPocztowy` | |
| `addresses[].city` | `Adres.Miejscowosc` | |
| `contacts[].contact_type` | `Kontakt.Rodzaj` | phone, email, fax, www |
| `contacts[].value` | `Kontakt.Wartosc` | |

## Products (Towary / Asortyment)

| Platform Field | enova365 API Field | Notes |
|---|---|---|
| `id` | `Id` | |
| `symbol` | `Kod` | Product code |
| `name` | `Nazwa` | |
| `ean` | `EAN` | |
| `pkwiu` | `PKWiU` | |
| `vat_rate` | `StawkaVAT` | |
| `unit_of_measure` | `JednostkaPodstawowa` | |
| `weight_kg` | `Waga` | |
| `description` | `Opis` | |
| `product_type` | `Typ` | Towar / Usluga |

## Sales Documents (Dokumenty sprzedaży)

| Platform Field | enova365 API Field | Notes |
|---|---|---|
| `id` | `Id` | |
| `number` | `Numer.PelnyNumer` | Auto-generated |
| `document_type` | `Definicja` | FS (faktura), PA (paragon), FP (proforma) |
| `buyer_nip` | `Kontrahent.NIP` | |
| `buyer_name` | `Kontrahent.Nazwa` | |
| `net_total` | `WartoscNetto` | |
| `gross_total` | `WartoscBrutto` | |
| `vat_total` | `WartoscVAT` | |
| `issue_date` | `DataWystawienia` | |
| `sale_date` | `DataSprzedazy` | |
| `currency` | `Waluta` | |

## Warehouse Documents (Dokumenty magazynowe)

| Platform Field | enova365 API Field | Notes |
|---|---|---|
| `id` | `Id` | |
| `number` | `Numer.PelnyNumer` | |
| `document_type` | `Definicja` | PZ, WZ, MM |
| `contractor_name` | `Kontrahent.Nazwa` | |
| `net_total` | `WartoscNetto` | |
| `gross_total` | `WartoscBrutto` | |
| `issue_date` | `DataWystawienia` | |
| `warehouse` | `Magazyn.Kod` | |

## Orders (Zamówienia)

| Platform Field | enova365 API Field | Notes |
|---|---|---|
| `id` | `Id` | |
| `number` | `Numer.PelnyNumer` | |
| `order_type` | `Definicja` | ZK (od klientow), ZD (do dostawcow) |
| `contractor_symbol` | `Kontrahent.Kod` | |
| `contractor_name` | `Kontrahent.Nazwa` | |
| `net_total` | `WartoscNetto` | |
| `gross_total` | `WartoscBrutto` | |
| `expected_date` | `TerminRealizacji` | |
| `notes` | `Uwagi` | |
| `external_number` | `NumerObcy` | |

## Stock Levels (Stany magazynowe)

| Platform Field | enova365 API Field | Notes |
|---|---|---|
| `product_symbol` | `Towar.Kod` | |
| `product_name` | `Towar.Nazwa` | |
| `quantity_available` | `StanDostepny` | Per warehouse |
| `quantity_reserved` | `StanZarezerwowany` | |
| `quantity_total` | `StanCalkowity` | |
| `warehouse_symbol` | `Magazyn.Kod` | |
| `unit` | `JednostkaPodstawowa` | |
