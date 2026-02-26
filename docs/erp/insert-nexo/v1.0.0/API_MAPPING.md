# InsERT Nexo — Field Mapping Reference

## Contractors (Podmioty)

| Platform Field | Nexo SDK Field | Notes |
|---|---|---|
| `id` | `Podmiot.Id` | Internal Nexo ID |
| `symbol` | `Podmiot.Sygnatura.PelnaSygnatura` | Auto-generated or manual |
| `contractor_type` | Company: `UtworzFirme()`, Person: `UtworzOsobe()` | |
| `short_name` | `Podmiot.NazwaSkrocona` | |
| `full_name` | `Podmiot.Firma.Nazwa` | Company only |
| `nip` | `Podmiot.NIPSformatowany` | Formatted NIP |
| `regon` | `Podmiot.REGON` | |
| `pesel` | `Podmiot.PESEL` | Person only |
| `first_name` | `Podmiot.Imie` | Person only |
| `last_name` | `Podmiot.Nazwisko` | Person only |
| `addresses[].street` | `Adres.Szczegoly.Ulica` | |
| `addresses[].house_number` | `Adres.Szczegoly.NrDomu` | |
| `addresses[].apartment_number` | `Adres.Szczegoly.NrLokalu` | |
| `addresses[].postal_code` | `Adres.Szczegoly.KodPocztowy` | |
| `addresses[].city` | `Adres.Szczegoly.Miejscowosc` | |
| `contacts[].contact_type` | `Kontakt.Rodzaj` | phone, email, fax, www |
| `contacts[].value` | `Kontakt.Wartosc` | |
| `contacts[].is_primary` | `Kontakt.Podstawowy` | |

## Products (Asortyment)

| Platform Field | Nexo SDK Field | Notes |
|---|---|---|
| `id` | `Asortyment.Id` | |
| `symbol` | `Asortyment.Symbol` | `AutoSymbol()` for auto |
| `name` | `Asortyment.Nazwa` | |
| `ean` | `Asortyment.EAN` | |
| `pkwiu` | `Asortyment.PKWiU` | |
| `vat_rate` | `Asortyment.StawkaVAT` | |
| `unit_of_measure` | `Asortyment.PodstawowaJednostkaMiaryAsortymentu.Symbol` | |
| `weight_kg` | `Asortyment.Waga` | |
| `description` | `Asortyment.Opis` | |
| `product_type` | Template: `Towar` / `Usluga` | Set via `WypelnijNaPodstawieSzablonu()` |
| `suppliers[].contractor_symbol` | via `IPodmioty.Znajdz()` | |
| `suppliers[].declared_price` | `DaneAsortymentuDlaPodmiotu.CenaDeklarowana` | |

## Sales Documents (DokumentySprzedazy)

| Platform Field | Nexo SDK Field | Notes |
|---|---|---|
| `id` | `DokumentDS.Id` | |
| `number` | `DokumentDS.NumerWewnetrzny.PelnaSygnatura` | Auto-generated |
| `document_type` | `UtworzFaktureSprzedazy()` / `UtworzParagon()` / `UtworzFaktureProforma()` | |
| `buyer_symbol` | `PodmiotyDokumentu.UstawZamawiajacegoWedlugSymbolu()` | |
| `receiver_symbol` | `PodmiotyDokumentu.UstawOdbiorceWedlugSymbolu()` | |
| `positions[].product_symbol` | `Pozycje.Dodaj(symbol)` | |
| `net_total` | `DokumentDS.WartoscNetto` | After `Przelicz()` |
| `gross_total` | `DokumentDS.WartoscBrutto` | After `Przelicz()` |
| `vat_total` | `DokumentDS.WartoscVAT` | After `Przelicz()` |
| `issue_date` | `DokumentDS.DataWystawienia` | |
| `sale_date` | `DokumentDS.DataSprzedazy` | |
| `payments` | `Platnosci.DodajDomyslnaPlatnoscNatychmiastowaNaKwoteDokumentu()` | |

## Warehouse Documents (WZ / PZ)

| Platform Field | Nexo SDK Field | Notes |
|---|---|---|
| `id` | `DokumentWZ.Id` / `DokumentPZ.Id` | |
| `number` | `.NumerWewnetrzny.PelnaSygnatura` | |
| WZ: `buyer_symbol` | `PodmiotyDokumentu.UstawOdbiorceWedlugSymbolu()` | |
| PZ: `buyer_symbol` | `PodmiotyDokumentu.UstawDostawceWedlugSymbolu()` | |
| `positions[].product_symbol` | `Pozycje.Dodaj(symbol)` | |

## Orders (Zamówienia)

| Platform Field | Nexo SDK Field | Notes |
|---|---|---|
| `id` | `ZamowienieZK.Id` / `ZamowienieZD.Id` | |
| `number` | `.NumerWewnetrzny.PelnaSygnatura` | |
| `order_type` | `from_customer` = `IZamowieniaOdKlientow`, `to_supplier` = `IZamowieniaDoDostawcow` | |
| `contractor_symbol` | `PodmiotyDokumentu.UstawZamawiajacegoWedlugSymbolu()` / `...DostawceWedlugSymbolu()` | |
| `positions[].product_symbol` | `Pozycje.Dodaj(symbol)` | |
| `net_total` | `.WartoscNetto` | After `Przelicz()` |
| `expected_date` | `.TerminRealizacji` | |
| `notes` | `.Uwagi` | |
| `external_number` | `.NumerZewnetrzny` | |

## Stock Levels

| Platform Field | Nexo SDK Field | Notes |
|---|---|---|
| `product_symbol` | `Asortyment.Symbol` | |
| `product_name` | `Asortyment.Nazwa` | |
| `quantity_available` | `StanyMagazynowe[].Dostepna` | Per warehouse |
| `quantity_reserved` | `StanyMagazynowe[].Zarezerwowana` | |
| `quantity_total` | `StanyMagazynowe[].Calkowita` | |
| `warehouse_symbol` | `StanyMagazynowe[].SymbolMagazynu` | |
| `unit` | `PodstawowaJednostkaMiaryAsortymentu.Symbol` | |
