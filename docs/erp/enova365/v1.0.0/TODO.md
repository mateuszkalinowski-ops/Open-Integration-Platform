# enova365 — Integration TODO

> Status: **Planning phase**
> Created: 2026-04-01
> Connector: `integrators/erp/enova365/v1.0.0/`

---

## Summary

enova365 (Soneta sp. z o.o.) to polski system ERP klasy enterprise, wykorzystywany przez 22 000+ organizacji. System udostepnia **Soneta WebAPI** — modul REST API oparty na HTTP/HTTPS z autentykacja JWT. Connector bedzie komunikowal sie z enova365 przez WebAPI, obslugujac moduly: Handel i magazyn, Finanse i ksiegowosc, CRM.

### Kluczowe ustalenia z analizy

1. **Soneta WebAPI** — REST API (nie SOAP) z kontrolerami dynamicznymi i statycznymi
2. **Autentykacja** — JWT token (od wersji 11.1), NIE OAuth2
3. **Licencja** — wymaga modulu WebAPI (lub legacy Harmonogram Zadan)
4. **Infrastruktura** — IIS + .NET 8 + MS SQL Server po stronie klienta
5. **Deployment** — dwa scenariusze: Multi (cloud) i Standard (on-premise z agentem)
6. **Dokumentacja API** — Soneta udostepnia Postman Collection (do pozyskania od partnera)
7. **Endpointy** — nie sa stale; zaleza od konfiguracji WebAPI serwisow na instancji klienta

---

## Phase 0: Dokumentacja i dostep do API

### 0.1 Pozyskanie dokumentacji Soneta WebAPI
- [ ] Uzyskac dokladna dokumentacje Soneta WebAPI (Postman Collection od partnera enova365)
- [ ] Uzyskac opis kontrolerow dynamicznych i statycznych
- [ ] Uzyskac schemat autentykacji JWT (login endpoint, token refresh, token expiry)
- [ ] Sprawdzic repozytorium GitHub `soneta/Soneta.Example.ImpersonateLogin` — przyklad logowania tokenem
- [ ] Sprawdzic repozytorium GitHub `soneta/Soneta.Example.EnovaIntegrator` — przyklad integratora
- [ ] Zapisac dokumentacje w `docs/erp/enova365/v1.0.0/external-api-docs/`

### 0.2 Sandbox / srodowisko testowe
- [ ] Zainstalowac instancje demo enova365 (lub uzyskac dostep do istniejacego demo)
  - Aprosystem udostepnia demo: `https://vps1.aprosystem.pl:5007/` (login: magazyn, haslo: kopytko)
  - Alternatywa: wlasna instalacja enova365 z licencja testowa
- [ ] Zainstalowac i skonfigurowac modul Soneta WebAPI na instancji testowej
- [ ] Skonfigurowac IIS z serwerem WebAPI
- [ ] Przetestowac autentykacje JWT na instancji testowej
- [ ] Zmapowac dostepne endpointy (kontrolery) na instancji testowej
- [ ] Udokumentowac sandbox setup w `docs/erp/enova365/v1.0.0/sandbox-setup.md`

### 0.3 Analiza modelu danych enova365
- [ ] Zmapowac model danych: Kontrahenci, Towary, Dokumenty handlowe, Zamowienia, Stany magazynowe
- [ ] Sprawdzic obsluge dodatkowych cech (custom fields) — dynamiczny odczyt/zapis
- [ ] Sprawdzic formaty odpowiedzi (JSON vs XML) i paginacje
- [ ] Sprawdzic rate limiting / throttling
- [ ] Uzupelnic `docs/erp/enova365/v1.0.0/API_MAPPING.md` na podstawie rzeczywistych danych

---

## Phase 1: Struktura projektu i autentykacja

### 1.1 Scaffold projektu
- [ ] Utworzyc `integrators/erp/enova365/v1.0.0/`
- [ ] Utworzyc strukture katalogow:
  ```
  integrators/erp/enova365/v1.0.0/
  ├── connector.yaml
  ├── Dockerfile
  ├── gunicorn.conf.py
  ├── requirements.txt
  ├── docker-compose.yml
  ├── .env.example
  └── src/
      ├── main.py
      ├── config.py
      ├── api/
      │   ├── dependencies.py
      │   └── routes.py
      ├── models/
      │   └── schemas.py
      └── services/
          ├── enova_client.py
          ├── auth.py
          └── account_manager.py
  ```
- [ ] Wzoruj sie na `integrators/erp/insert-nexo/v1.0.0/` (struktura, config, main.py)

### 1.2 Autentykacja JWT
- [ ] Zaimplementowac `services/auth.py`:
  - Login do enova365 WebAPI (endpoint logowania)
  - Przechowywanie JWT tokena
  - Automatyczny refresh tokena przed wygasnieciem
  - Obsluga bledu 401 (token expired) z ponownym logowaniem
- [ ] Przetestowac flow: login -> token -> request -> token refresh

### 1.3 HTTP Client
- [ ] Zaimplementowac `services/enova_client.py`:
  - httpx.AsyncClient z connection pooling
  - Circuit breaker (5 failures -> open -> reset po 30s)
  - Retry z exponential backoff (max 3 retries)
  - Timeout: 30s connect, 60s read
  - JWT token injection w headerach
  - Prometheus metrics (request count, latency)

### 1.4 connector.yaml
- [ ] Utworzyc manifest z:
  - `interface: erp`
  - `deployment: cloud` (scenariusz Multi) lub `hybrid` (scenariusz Standard)
  - Capabilities, events, actions (wzoruj sie na insert-nexo)
  - `config_schema` z polami: `api_url`, `operator_login`, `operator_password`, `database_name`
  - `credential_validation` z JWT test request
  - Logo i country: PL
- [ ] Pobrac logo enova365 i zapisac jako `/assets/logos/enova365.svg`

---

## Phase 2: Implementacja encji (ERP interface)

### 2.1 Contractors (Kontrahenci) — REQUIRED
- [ ] `GET /contractors` — lista z paginacja i wyszukiwaniem
- [ ] `GET /contractors/{id}` — szczegoly kontrahenta
- [ ] `GET /contractors/by-nip/{nip}` — wyszukiwanie po NIP
- [ ] `POST /contractors` — tworzenie
- [ ] `PUT /contractors/{id}` — aktualizacja
- [ ] `DELETE /contractors/{id}` — usuwanie
- [ ] Mapowanie pol: Platform <-> enova365 (Kod, Nazwa, NIP, REGON, Adresy, Kontakty)

### 2.2 Products (Towary) — REQUIRED
- [ ] `GET /products` — lista z paginacja i wyszukiwaniem
- [ ] `GET /products/{id}` — szczegoly
- [ ] `GET /products/by-ean/{ean}` — wyszukiwanie po EAN
- [ ] `POST /products` — tworzenie
- [ ] `PUT /products/{id}` — aktualizacja
- [ ] `DELETE /products/{id}` — usuwanie
- [ ] Mapowanie pol: Kod, Nazwa, EAN, PKWiU, StawkaVAT, Jednostka, Ceny

### 2.3 Orders (Zamowienia) — REQUIRED
- [ ] `GET /orders` — lista z filtrowaniem (typ, status, data)
- [ ] `GET /orders/{id}` — szczegoly z pozycjami
- [ ] `POST /orders` — tworzenie (od klientow ZK / do dostawcow ZD)
- [ ] `PUT /orders/{id}` — aktualizacja (status, pozycje)
- [ ] Mapowanie statusow zamowien enova365 -> ujednolicone statusy platformy

### 2.4 Stock Levels (Stany magazynowe) — REQUIRED
- [ ] `GET /stock` — wszystkie stany (z filtrowaniem po magazynie)
- [ ] `GET /stock/{product_id}` — stan dla konkretnego produktu
- [ ] Obsluga wielu magazynow

### 2.5 Sales Documents (Dokumenty sprzedazy) — OPTIONAL
- [ ] `GET /documents/sales` — lista z filtrowaniem
- [ ] `GET /documents/sales/{id}` — szczegoly z pozycjami i platnosci
- [ ] `POST /documents/sales` — tworzenie (FS faktura, PA paragon, FP proforma)
- [ ] Mapowanie typow dokumentow

### 2.6 Warehouse Documents (Dokumenty magazynowe) — OPTIONAL
- [ ] `GET /documents/warehouse` — lista
- [ ] `GET /documents/warehouse/{id}` — szczegoly
- [ ] `POST /documents/warehouse` — tworzenie (PZ przyjecie, WZ wydanie, MM przesuniecie)

---

## Phase 3: Eventy i sync

### 3.1 Background polling
- [ ] Zaimplementowac polling nowych/zmienionych zamowien (konfigurowalny interval)
- [ ] Zaimplementowac polling zmian stanow magazynowych
- [ ] Zaimplementowac polling nowych dokumentow
- [ ] Deduplikacja eventow (po ID + timestamp)

### 3.2 Kafka events
- [ ] `enova365.output.erp.orders.save` — nowe zamowienia
- [ ] `enova365.output.erp.orders.update` — zmiany statusow
- [ ] `enova365.output.erp.stock.sync` — zmiany stanow magazynowych
- [ ] `enova365.output.erp.contractors.save` — nowi kontrahenci
- [ ] `enova365.output.erp.products.save` — nowe produkty

### 3.3 Platform events
- [ ] `order.created` — nowe zamowienie
- [ ] `order.status_changed` — zmiana statusu
- [ ] `stock.level_changed` — zmiana stanu magazynowego
- [ ] `contractor.created` / `contractor.updated`
- [ ] `product.created` / `product.updated` / `product.price_changed`

---

## Phase 4: Docker i deployment

### 4.1 Dockerfile
- [ ] Multi-stage build (Python 3.12 slim)
- [ ] Non-root user
- [ ] Health check (`/health`)
- [ ] Pinned base image (nie `latest`)

### 4.2 docker-compose.yml
- [ ] Serwis `connector-enova365`
- [ ] Konfiguracja env vars
- [ ] Health check
- [ ] Network z platforma

### 4.3 Dodac do docker-compose.vps.yml
- [ ] Wpis `connector-enova365` (wzoruj sie na inne connectory w pliku)

---

## Phase 5: Testy

### 5.1 Unit testy (>80% coverage)
- [ ] Test autentykacji JWT (mock login, token refresh, expiry)
- [ ] Test CRUD kontrahentow (mock responses)
- [ ] Test CRUD produktow
- [ ] Test zamowien
- [ ] Test stanow magazynowych
- [ ] Test dokumentow sprzedazy i magazynowych
- [ ] Test circuit breaker i retry logic
- [ ] Test error handling (401, 404, 500)

### 5.2 Integration testy (sandbox)
- [ ] Test polaczenia z sandbox enova365
- [ ] Test full cycle: create contractor -> create product -> create order -> check stock
- [ ] Test paginacji na duzych zbiorach

### 5.3 Verification Agent
- [ ] Utworzyc `platform/verification-agent/src/checks/erp/enova365.py`
- [ ] Tier 3: functional smoke tests (list contractors, get product, create test order)
- [ ] Wzoruj sie na `checks/erp/__init__.py` i inne moduly weryfikacyjne

---

## Phase 6: Dokumentacja i finalizacja

### 6.1 Zaktualizowac dokumenty
- [ ] `docs/erp/enova365/v1.0.0/README.md` — finalna wersja z rzeczywistymi endpointami
- [ ] `docs/erp/enova365/v1.0.0/API_MAPPING.md` — finalne mapowanie pol
- [ ] `docs/erp/enova365/v1.0.0/CHANGELOG.md` — wpis 1.0.0
- [ ] `docs/erp/enova365/v1.0.0/sandbox-setup.md` — instrukcja sandboxa
- [ ] `docs/erp/enova365/v1.0.0/known-issues.md` — znane problemy

### 6.2 Zaktualizowac pliki platformy
- [ ] `docs/CONNECTORS.md` — dodac enova365 do tabeli connectorow (nr 37)
- [ ] `docs/ARCHITECTURE.md` — dodac enova365 do listy ERP connectorow (jezeli potrzebne)
- [ ] `AGENTS.md` — zaktualizowac count connectorow ERP (2 zamiast 1)

### 6.3 Walidator
- [ ] Utworzyc walidator credential dla enova365 (JWT login test)
- [ ] Zarejestrowac w platformie

---

## Ryzyka i pytania otwarte

### Ryzyka

| # | Ryzyko | Impact | Mitygacja |
|---|--------|--------|-----------|
| R1 | Brak publicznej dokumentacji API — endpointy zaleza od konfiguracji WebAPI | Wysoki | Uzyskac Postman Collection od Soneta/partnera; zbudowac adapter na kontrolery dynamiczne |
| R2 | Kazda instancja enova365 moze miec inne serwisy WebAPI | Sredni | Zaimplementowac discovery endpoint (lista dostepnych kontrolerow); dynamic schema |
| R3 | Wymagana licencja WebAPI po stronie klienta | Niski | Udokumentowac wymagania licencyjne w README; sprawdzic legacy Harmonogram Zadan |
| R4 | On-premise (Standard) wymaga dodatkowego agenta | Sredni | Wzoruj sie na insert-nexo hybrid; moze byc oddzielna faza (v2.0.0) |
| R5 | WebWCF (SOAP) moze byc potrzebne dla starszych instalacji | Niski | Na poczatek tylko REST (WebAPI); SOAP w przyszlej wersji |

### Pytania do rozstrzygniecia

1. **Priorytet deployment:** Zaczynamy od scenariusza Multi (cloud) czy Standard (on-premise)?
   - Rekomendacja: **Multi (cloud)** jako v1.0.0, on-premise jako v2.0.0
2. **Zakres modulow:** Czy Kadry i place (HR/Payroll) sa potrzebne w v1.0.0?
   - Rekomendacja: **Nie** — fokus na Handel, Finanse, CRM
3. **KSeF integracja:** Czy enova365 connector powinien obslugiwac KSeF (faktury ustrukturyzowane)?
   - enova365 ma wbudowana obsluge KSeF z API 2.0
   - Mamy juz oddzielny connector `other/ksef/v1.0.0` — mozna polaczyc przez Flow Engine
4. **Soneta Integrator vs custom WebAPI:** Czy klient ma juz zainstalowany Soneta Integrator (gotowe serwisy)?
   - Warto sprawdzic — moze zapewnic standardowe endpointy bez custom konfiguracji

---

## Estymacja czasu

| Phase | Opis | Czas (szacunkowo) |
|-------|------|-------------------|
| Phase 0 | Dokumentacja i sandbox | 2-3 dni |
| Phase 1 | Scaffold + auth + client | 2-3 dni |
| Phase 2 | Implementacja encji (6 grup) | 5-7 dni |
| Phase 3 | Eventy i sync | 2-3 dni |
| Phase 4 | Docker i deployment | 1 dzien |
| Phase 5 | Testy | 3-4 dni |
| Phase 6 | Dokumentacja i finalizacja | 1-2 dni |
| **TOTAL** | | **16-23 dni robocze** |

> Phase 0 jest blokujaca — bez dokumentacji API i sandboxa nie mozna zaczac implementacji.
