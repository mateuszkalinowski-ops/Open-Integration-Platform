# TOS Intermodal EDI Gateway — specyfikacja wdrożenia w OIP

**Wersja:** 1.0  
**Status:** Zaakceptowany plan implementacji  
**Adresat:** Agent pracujący w `Open-Integration-Platform` (OIP)  
**Powiązany projekt:** Pinquark TOS dla Clip Małaszewicze (`/Users/mateuszkalinowski/Downloads/pinquark_implementation/clip/TOS`)

---

## 0. TL;DR — co masz zrobić

Rozszerz **Open Integration Platform** tak, aby działała jako **EDI Gateway** dla intermodalnego terminala kolejowego Pinquark TOS (Clip Małaszewicze).

Konkretnie trzeba:

1. **Dodać brakujące komunikaty EDIFACT** do konektora `integrators/other/edifact` — COPRAR, COPARN, COHAOR, COARRI, IFTSTA, APERAK, CONTRL.
2. **Dodać parser/builder surowego EDIFACT** (segmenty `UNB+...UNH+...UNT+...UNZ`) — biblioteka `pydifact`.
3. **Sklonować konektor `pinquark-wms`** → utworzyć nowy konektor `integrators/wms/pinquark-tos` z mapowaniem na **reakcje TOS** zamiast WMS, ale **świadomie tego, że TOS nie ma out-of-box REST API** — działa przez mechanizm „Integracje własne" Pinquark (tabele `con_integration`, `con_token`).
4. **Udokumentować workflow** (przykładowe DAG-i) dla flow inbound (COPRAR → AWK) i outbound (polling `tos_audit_log` → CODECO/COARRI/APERAK).
5. **Zachować zasadę zero-impact** — zero zmian w `platform/core/`. Wszystko ma się dziać przez `connector.yaml` + nowe pliki w folderach konektorów.

> **Ważne uściślenie architektury (po analizie kodu TOS):** OIP komunikuje się z TOS **wyłącznie jako klient REST** (TOS = serwer, OIP = klient). Outbound EDI (CODECO, COARRI, APERAK, IFTSTA) NIE jest oparty o webhooki z TOS, tylko o **polling tabeli `tos_audit_log`** przez OIP. TOS już teraz loguje wszystkie zdarzenia biznesowe przez helper `tos_log_event` (92 wywołań w `tos_procedures.sql`) — ta tabela jest **gotowym outboxem**. Konsekwencje: zero modyfikacji istniejących procedur TOS, zero integracji typu Klient w `con_integration`, zero `tos_webhook_emit`. Patrz sekcja 14.6 — szczegółowy opis pull patternu z gotowym workflow YAML.

> **Drugie uściślenie — JEDEN STANDARD, NIE per-partner:** OIP jest **standardową bramką EDIFACT/SMDG**, do której operatorzy (Metrans, HHLA, Kombiverkehr, DB Cargo, PKP Cargo Connect itd.) **dostosowują się**, a nie odwrotnie. Workflowy są **partner-agnostyczne** — istnieje **jeden** workflow na komunikat (np. `coprar-inbound`), a różnice między partnerami sprowadzają się do parametrów konta (`account.yaml`): SFTP host, sender/receiver IDs, wersja EDIFACT (D.95B vs D.00B), SMDG profile (1.x/2.0). **Onboarding nowego partnera = dodanie jednego pliku account, BEZ pisania nowego workflow ani konektora.** Konsekwencje: konektor `edifact` parsuje/buduje wg standardu SMDG, partner-specific quirks (jeśli się pojawią) lokujemy w „SMDG profile" w schemach, nie w workflow. Patrz sekcja 6.

Po Twojej stronie: ~10 dni roboczych. Po stronie TOS dokumentacja i procedury są opisane w sekcji 12, a mechanizm rejestracji REST endpointów w Pinquark — **kluczowy** dla tego, jak Twój konektor `pinquark-tos` uderza w TOS — opisany jest w **sekcji 14**. **Przeczytaj sekcję 14 PRZED rozpoczęciem implementacji konektora `pinquark-tos`**, bo różni się on architektonicznie od `pinquark-wms`.

---

## 1. Kontekst biznesowy — po co to jest

### 1.1. Co to jest TOS Małaszewicze

**Pinquark TOS** (Terminal Operating System) — aplikacja low-code zbudowana na platformie Pinquark (PostgreSQL + EAV + procedury PL/pgSQL + JSON-owe ekrany), wdrażana dla:

- **Clip-Terminal Małaszewice** — duży intermodalny terminal kolejowo-drogowy na granicy Polski z Białorusią (przeładunek 1435 mm ↔ 1520 mm rosyjski tor szeroki).
- **Mała (Małaszewicze Małe)**, **Zabrze** — kolejne terminale tej samej grupy.

Terminale obsługują:
- Awizacje kolejowe (AWK) — pociągi przyjeżdżają, są rozładowywane, kontenery idą na plac/na ciężarówki.
- Awizacje drogowe (AWD) — ciężarówki zabierają lub przywożą kontenery.
- Operacje przeładunkowe (PRZ) — suwnice/reachstackery przenoszą kontenery między pociągiem, placem i ciężarówką.
- Bramy (ZDB) — zdarzenia bramowe (wjazd/wyjazd, OCR tablic, uszkodzenia).
- Zlecenia transportowe (KZT/DZT — kolejowe/drogowe).

### 1.2. Dlaczego potrzebny jest EDI

W realiach intermodalnych operatorów kolejowych — **HHLA**, **Metrans**, **Kombiverkehr**, **DB Cargo**, **PKP Cargo Connect**, **CTL Logistics** — komunikacja z terminalami odbywa się **wyłącznie przez EDIFACT** (głównie SMDG D.95B / D.00B). REST API ich nie interesuje. **Bez EDI TOS Małaszewicze nie zintegruje się z żadnym poważnym partnerem.**

Standardowy stack EDIFACT dla intermodal:

| Komunikat | Kierunek | Zastosowanie biznesowe |
|---|---|---|
| **COPRAR** (Container pre-announcement) | IN | Operator wysyła skład pociągu z listą wagonów i kontenerów *zanim* pociąg przyjedzie |
| **COPARN** (Container release/reservation) | IN | Awizacja odbioru/dostawy konkretnego kontenera (zwykle drogowo) |
| **COHAOR** (Handling order) | IN | Zlecenie wykonania konkretnej operacji (load/discharge/move) |
| **IFTMIN** (Booking message) | IN | Rezerwacja slotu / booking transportu |
| **CODECO** (Discharge/load confirmation, gate-in/out) | OUT | Potwierdzenie wykonania operacji bramowej lub przeładunkowej |
| **COARRI** (Container arrival report) | OUT | Raport przyjazdu/wyjazdu pociągu z kontenerami |
| **IFTSTA** (Status update) | OUT | Aktualizacja statusu dokumentu/kontenera (do shipping line) |
| **APERAK / CONTRL** | OUT | Acknowledgement techniczny (musi być wysłany w sekundach po odebraniu pliku) |

### 1.3. Dlaczego OIP zamiast osobnego mikroserwisu

OIP ma już ~80% potrzebnej infrastruktury:
- konektor `edifact` (częściowy — CODECO/BAPLIE/IFTMIN),
- konektor `ftp-sftp` z polling-iem (transport plików `.edi`),
- konektor `email-client` (część partnerów wysyła EDI mailem),
- konektor `pinquark-wms` (wzorzec do sklonowania dla TOS),
- Flow Engine + Workflow Engine (DAG, retry, mapowanie pól),
- Audit Trail (zastępuje tabele `tos_edi_message` w TOS),
- Dashboard Angular (operation log z drill-down — zastępuje ekrany kartoteki EDI w TOS),
- Verification Agent (cykliczne testy zdrowia integracji),
- multi-tenant (Małaszewicze + Mała + Zabrze izolowane),
- per-connector rate limiter, OAuth2 lifecycle, signature verification webhook ingestion.

Budowa osobnego `tos-edi-gateway` to ~10 tygodni roboty + duplikacja istniejącej infrastruktury OIP. Wykorzystanie OIP to ~5 tygodni.

---

## 2. Architektura docelowa

```
┌─────────────────┐                    ┌──────────────────────────────────────────┐
│   Partner EDI   │                    │     Open Integration Platform            │
│  (HHLA/Metrans/ │                    │                                          │
│   Kombiverkehr) │                    │  ┌────────────┐    ┌──────────────────┐  │
│                 │                    │  │ Connector: │    │  Flow Engine     │  │
│   ┌────────┐    │  EDIFACT/.edi      │  │  ftp-sftp  │ ──►│  (DAG router)    │  │
│   │  SFTP  │ ◄──┼────────────────────┼──┤  (polling) │    └────────┬─────────┘  │
│   └────────┘    │   pliki .edi       │  └────────────┘             │            │
│                 │                    │                             ▼            │
│   ┌────────┐    │  EDIFACT przez     │  ┌────────────┐    ┌──────────────────┐  │
│   │  AS2   │    │  email             │  │ Connector: │    │  Connector:      │  │
│   └────────┘    │  ───────────────── │  │ email      │    │  edifact         │  │
│                 │                    │  │ -client    │    │  • parse raw EDI │  │
│                 │                    │  └────────────┘    │  • build raw EDI │  │
└─────────────────┘                    │                    │  • walidacja     │  │
                                       │                    │    SMDG/UNECE    │  │
                                       │                    └────────┬─────────┘  │
                                       │                             │            │
                                       │                             ▼            │
                                       │                    ┌──────────────────┐  │
                                       │                    │ Connector:       │  │
                                       │                    │ pinquark-tos     │  │
                                       │                    │ (do utworzenia)  │  │
                                       │                    │ • woła reakcje:  │  │
                                       │                    │   tos_*          │  │
                                       │                    └────────┬─────────┘  │
                                       │                             │            │
                                       │  ┌────────────────────┐     │            │
                                       │  │ Workflow:          │     │            │
                                       │  │ tos-poll-events    │     │            │
                                       │  │ (scheduler co 30s) │ ────┘            │
                                       │  │ POST get_events_*  │                  │
                                       │  └────────────────────┘                  │
                                       └─────────────────────────────┬────────────┘
                                                                     │ REST
                                                                     │ Bearer + token-mer
                                                                     ▼
                                                          ┌──────────────────────┐
                                                          │  Pinquark TOS        │
                                                          │  PostgreSQL          │
                                                          │  procedury PL/pgSQL  │
                                                          │  reakcje (40):       │
                                                          │   tos_notification_* │
                                                          │   tos_train_*        │
                                                          │   tos_movement_*     │
                                                          │   tos_gate_*_confirm │
                                                          │   tos_operation_*    │
                                                          │   tos_get_events_*   │
                                                          │   (outbound polling) │
                                                          └──────────────────────┘
                                                          │  tos_audit_log       │
                                                          │  (gotowy outbox,     │
                                                          │   92 wywołań         │
                                                          │   tos_log_event)     │
                                                          └──────────────────────┘
```

### 2.1. Flow inbound (partner → TOS)

1. Partner uploaduje plik `.edi` (np. `COPRAR_HHLA_20260419_001.edi`) na SFTP.
2. Konektor `ftp-sftp` z włączonym polling-iem co 60 s wykrywa plik → emituje event `file.new`.
3. Flow Engine matchuje workflow z trigger `ftp-sftp.file.new` i filtrem `path: /inbound/hhla/COPRAR_*.edi`.
4. Workflow wywołuje `edifact.coprar.parse` (raw EDI → JSON).
5. Workflow buduje APERAK (ACK) i wysyła z powrotem na SFTP partnera (musi być w ciągu sekund — wymóg SMDG).
6. Workflow wywołuje `pinquark-tos.tos_notification_rail_save` — tworzy AWK w TOS.
7. Foreach po wagonach: `pinquark-tos.tos_train_wagon_add`.
8. Foreach po kontenerach: `pinquark-tos.tos_train_container_add`.
9. Audit trail OIP zapisuje pełny przepływ z drill-down per krok.

### 2.2. Flow outbound (TOS → partner) — pull pattern

1. Procedura biznesowa TOS (`tos_gate_road_entry_confirm`, `tos_operation_complete`, `tos_notification_rail_approve`, ...) kończy się sukcesem i — jak dotychczas — wywołuje `PERFORM tos_log_event(module, event_type, doc_id, doc_symbol, user_id, user_login, details)`. **Procedury TOS pozostają bez zmian.**
2. Helper `tos_log_event` wstawia rekord do `tos_audit_log` (już istniejące zachowanie, wykorzystywane 92× w produkcji).
3. **Workflow OIP `tos-poll-events`** (scheduled co 30s) wywołuje `POST /integration/tos_get_events_since` z aktualnym kursorem `last_audit_id`.
4. TOS odpowiada listą nowych eventów (nawet 1000 na request, max 5000) z `max_id`.
5. OIP w `foreach` po eventach robi switch po `event_type`:
   - `WJAZD_TIR_POTWIERDZONY` → workflow `outbound-codeco-gate-in` → `edifact.codeco.build` → `ftp-sftp.file.upload` → CODECO do partnera (Metrans/HHLA).
   - `PRZELAD_ZAKONCZONY` → workflow `outbound-coarri-operation` → COARRI do partnera.
   - `AWK_RAIL_ZATWIERDZONA` → workflow `outbound-aperak-positive` → APERAK do nadawcy preadvice.
   - itd. (pełna mapa: sekcja 14.6.5).
6. Workflow czeka na zwrotny APERAK od partnera (timeout 5 min) — jeśli brak, retry/alert.
7. Po pomyślnym przejściu wszystkich eventów OIP zapisuje `state.last_audit_id = max_id`. Przy crashu OIP — przy restarcie wczytuje kursor i podejmuje od ostatniego potwierdzonego ID (**at-least-once delivery**).

> Szczegóły: sekcja 14.6 (architektura pull patternu, gotowe procedury PL/pgSQL `tos_get_events_since`/`tos_get_doc_status_changes_since`, gotowy YAML workflow `tos-poll-events`).

---

## 3. Co konkretnie zrobić — checklista zadań

### Zadanie 1 — Rozszerz konektor `edifact`

Lokalizacja: `integrators/other/edifact/v1.0.0/`

#### 1.1. Dodaj parser/builder raw EDIFACT

Nowe pliki:
- `src/services/edifact_parser.py` — parser pliku `.edi` → dict (oparty o `pydifact`).
- `src/services/edifact_builder.py` — builder dict → string `.edi` z walidacją segmentów UNB/UNH/UNT/UNZ i numeracją sekwencyjną per partner.
- `src/services/edifact_segments.py` — wspólny słownik segmentów: BGM, DTM, NAD, RFF, EQD, CTA, COM, LOC, FTX, MEA, GID, EQA, TPL, TDT, EQN, GDS, SGP, IMP itd.

Dodaj do `requirements.txt`:
```
pydifact==0.13.0
```

API parsera (przykład):
```python
from src.services.edifact_parser import parse_edifact

result = parse_edifact(content_bytes)
# → {
#     "msg_type": "COPRAR",
#     "version": "D00B",
#     "interchange_ref": "REF12345",
#     "message_ref": "MSG001",
#     "sender_id": "HHLA",
#     "receiver_id": "PLMSC",
#     "payload": { ... domain JSON ... },
# }
```

API buildera:
```python
from src.services.edifact_builder import build_edifact

content = build_edifact(
    msg_type="CODECO",
    version="D00B",
    sender_id="PLMSC",
    receiver_id="HHLA",
    payload={...},
    sequence_provider=sequence_provider,
)
```

`sequence_provider` to interfejs do nadawania kolejnych numerów UNB/UNH per partner — domyślnie używaj prostego in-memory + persist do JSON na dysku w `config/sequences/{partner}.json`.

#### 1.2. Dodaj nowe komunikaty (schemas + routes + actions)

Dla każdego komunikatu z poniższej listy utwórz:
- moduł w `src/schemas/<msg>.py` (na wzór `codeco.py`),
- routes w `src/api/routes.py` (sekcja per komunikat),
- metody w `src/services/edifact_client.py` (parse, build, optional forward),
- aktualizacja `connector.yaml` (capabilities, events, actions, action_routes, action_fields, output_fields, rate_limits),
- testy w `tests/test_<msg>.py`.

**Lista komunikatów do dodania:**

##### COPRAR (Container Pre-Advice — preadvice pociągu)

Najczęściej spotykany w intermodal kolejowym. Operator wysyła **przed przyjazdem pociągu** pełną listę wagonów i kontenerów.

Schema (kluczowe pola):
```python
class CoprarMessage(BaseModel):
    document_id: str
    function_code: FunctionCode  # original/replace/cancel
    train_no: str                 # numer pociągu
    eta: datetime                 # planowany przyjazd
    etd: datetime | None          # planowany wyjazd (jeśli przejazdowy)
    carrier: Party                # przewoźnik
    pol: Location                 # port of loading (UN/LOCODE)
    pod: Location                 # port of discharge (UN/LOCODE)
    wagons: list[WagonGroup]      # wagony w kolejności w składzie

class WagonGroup(BaseModel):
    wagon_no: str
    wagon_type: str | None         # np. Sgnss, Lgs
    sequence_no: int               # pozycja w pociągu
    containers: list[ContainerOnWagon]

class ContainerOnWagon(BaseModel):
    container_no: str               # ISO 6346
    iso_size_type: str              # 22G1, 45G1, 42G1...
    seal_no: str | None
    weight_kg: float
    is_empty: bool
    dangerous_goods: list[DangerousGoods]
    booking_ref: str | None
    bl_ref: str | None              # bill of lading
    shipper: Party | None
    consignee: Party | None
    pol: Location | None
    pod: Location | None
```

Routes:
- `POST /coprar/messages` — przyjmij JSON, opcjonalnie zbuduj EDI, opcjonalnie forward do TOS.
- `POST /coprar/parse` — przyjmij raw EDI w body (`Content-Type: application/edifact`), zwróć JSON.
- `POST /coprar/build` — przyjmij JSON, zwróć raw EDI (`{"content_base64": "..."}`).
- `GET /coprar/messages` — lista (filtry: account_name, train_no, date_from, date_to).
- `GET /coprar/messages/{id}`.

Actions w `connector.yaml`:
```yaml
actions:
  - coprar.parse           # raw EDI → JSON
  - coprar.build           # JSON → raw EDI
  - coprar.create          # JSON → forward do TOS (zachowanie jak codeco.create)
  - coprar.list
  - coprar.get
```

##### COPARN (Container Release/Reservation Order)

Awizacja odbioru lub dostawy konkretnego kontenera (najczęściej drogowo). Mapuje się na **AWD** w TOS.

Schema:
```python
class CoparnMessage(BaseModel):
    document_id: str
    function_code: FunctionCode
    operation_type: Literal["release", "reservation", "drop_off", "pick_up"]
    container_no: str | None        # może nie być znany przy reservation
    iso_size_type: str
    is_empty: bool
    booking_ref: str | None
    bl_ref: str | None
    pickup_window_from: datetime | None
    pickup_window_to: datetime | None
    haulier: Party | None           # przewoźnik drogowy
    carrier: Party                  # shipping line
    truck_plate: str | None         # jeśli znany
    driver_name: str | None
    references: list[Reference]
```

##### COHAOR (Container Special Handling Order)

Zlecenie konkretnej operacji (load/discharge/move/inspection). Mapuje się na **PRZ** w TOS.

Schema:
```python
class CohaorMessage(BaseModel):
    document_id: str
    function_code: FunctionCode
    operation_code: Literal["load", "discharge", "shift", "inspection", "weighing", "reefer_check"]
    container_no: str
    location_from: Location | None
    location_to: Location | None
    requested_time: datetime
    priority: int = 5
    special_instructions: list[FreeText]
```

##### COARRI (Container Discharge/Loading Report)

Raport przeprowadzonej operacji przeładunkowej — ile wyładowane, ile załadowane, status każdego kontenera.

Schema:
```python
class CoarriMessage(BaseModel):
    document_id: str
    function_code: FunctionCode
    operation_type: Literal["discharge", "loading"]
    transport: Transport            # jaki pociąg/statek
    completion_time: datetime
    containers: list[CoarriContainer]

class CoarriContainer(BaseModel):
    container_no: str
    status: Literal["completed", "shortage", "damaged", "rejected"]
    actual_position: Location | None
    seal_no: str | None
    weight_kg: float | None
    damages: list[DamageReport] = []
```

##### IFTSTA (Multimodal Status Report)

Aktualizacja statusu wysyłana przy każdej zmianie statusu dokumentu/kontenera. Wysyłana do shipping line po stronie OUT.

Schema:
```python
class IftstaMessage(BaseModel):
    document_id: str
    function_code: FunctionCode
    status_code: str                # SMDG kod, np. "VGM" (verified gross mass), "GTI" (gate-in), "GTO" (gate-out)
    status_time: datetime
    container_no: str | None
    transport: Transport | None
    location: Location | None
    references: list[Reference]
    free_text: list[FreeText]
```

Mapowanie statusów TOS → SMDG IFTSTA (tabela do zaszycia w buildery):

| Status TOS | SMDG kod | Opis |
|---|---|---|
| AWK Awizowany | `EAR` | Estimated arrival reported |
| AWK Zaakceptowany | `ARR` | Arrival reported |
| ZDB Wjazd kolejowy potwierdzony | `GTI` | Gate in |
| PRZ Wyładunek zakończony | `DIS` | Discharged |
| PRZ Załadunek zakończony | `LOA` | Loaded |
| ZDB Wyjazd kolejowy potwierdzony | `GTO` | Gate out |
| AWD Wjazd drogowy | `GTI` | Gate in (truck) |
| AWD Wyjazd drogowy | `GTO` | Gate out (truck) |
| PRZ Anulowane | `CAN` | Cancelled |

##### APERAK (Application Error and Acknowledgement) — OUT

ACK techniczny wysyłany **automatycznie** po sparsowaniu każdego inbound. Musi być w ciągu sekund od odebrania.

Schema:
```python
class AperakMessage(BaseModel):
    document_id: str               # wygenerowany
    referenced_message_ref: str    # UNH ref oryginalnego komunikatu
    referenced_interchange_ref: str # UNB ref
    response_type: Literal["accepted", "rejected", "accepted_with_errors"]
    errors: list[AperakError] = []

class AperakError(BaseModel):
    error_code: str               # np. "12" (segment missing), "27" (dataset error)
    segment_position: int | None
    free_text: str
```

##### CONTRL (Syntax Acknowledgement) — OUT

Niższy poziom niż APERAK — potwierdza tylko poprawność składni (UNH/UNT są zbieżne, segmenty obowiązkowe są obecne). APERAK potwierdza poprawność biznesową.

Schema (analogiczne do APERAK ale z `syntax_status: ok|error`).

#### 1.3. Wersjonowanie EDIFACT per partner

Różni partnerzy używają różnych wersji:
- HHLA: SMDG 2.0 (nadbudówka nad D.00B)
- Metrans: zazwyczaj D.95B (legacy)
- Kombiverkehr: D.00B
- DB Cargo: D.00B + custom enrichment

Rozszerz `account_manager.py` aby konto miało pole:
```python
class EdifactAccount(BaseModel):
    name: str
    base_url: str = ""              # opcjonalne — gdy używamy forward-mode
    api_key: str = ""
    edifact_version: Literal["D95B", "D00B", "D03B", "SMDG2.0"] = "D00B"
    sender_id: str                  # qualifier UNB
    receiver_id: str                # qualifier UNB
    transport_type: Literal["sftp", "as2", "email", "rest"] = "sftp"
    transport_config: dict          # delegowane do innych konektorów
    sequence_state_path: str | None # ścieżka do JSON z numeracją UNB/UNH
```

W buildery przekazuj `version` aby dobrać właściwy template segmentów.

#### 1.4. Walidacja słowników

Rozszerz `src/validators/edifact_validator.py`:
- `validate_iso_size_type` (np. 22G1, 45G1) — kody ISO 6346.
- `validate_un_locode` (już jest).
- `validate_imdg_class` (już jest).
- `validate_smdg_status_code` (lista kodów SMDG dla IFTSTA).
- `validate_seal_type`.

#### 1.5. Aktualizuj `connector.yaml`

- Dodaj wszystkie nowe `capabilities`, `events`, `actions`.
- Dodaj `action_routes` dla każdego nowego endpointu.
- Dodaj `action_fields` i `output_fields`.
- Zaktualizuj `description` aby uwzględniała intermodal rail (nie tylko maritime).
- Dodaj do `config_schema` pole `edifact_version` i `sender_id`/`receiver_id` per account.

#### 1.6. Testy

W `tests/`:
- `test_coprar.py` — happy path + cancel + replace + złe ISO codes.
- `test_coparn.py`.
- `test_cohaor.py`.
- `test_coarri.py` — w tym scenariusz partial discharge (część kontenerów ze statusem `shortage`).
- `test_iftsta.py` — mapowanie wszystkich statusów TOS na kody SMDG.
- `test_aperak.py` — generowanie ACK natychmiast po parse.
- `test_parser.py` — parsowanie kilku rzeczywistych przykładów `.edi` (skopiuj fixtures z `tests/fixtures/edifact/`).
- `test_builder.py` — round-trip parse → build → parse i porównanie.

Fixtures z przykładowymi plikami EDIFACT:
```
tests/fixtures/edifact/
├── coprar/
│   ├── coprar_hhla_basic.edi
│   ├── coprar_metrans_d95b.edi
│   └── coprar_cancel.edi
├── coparn/
│   └── coparn_release.edi
├── cohaor/
│   └── cohaor_load.edi
├── coarri/
│   └── coarri_partial.edi
└── iftsta/
    └── iftsta_gtin.edi
```

Pliki testowe wygeneruj samodzielnie (zgodnie ze specyfikacją SMDG) lub poproś o nie autora projektu.

---

### Zadanie 2 — Utwórz nowy konektor `pinquark-tos`

Lokalizacja: `integrators/wms/pinquark-tos/v1.0.0/`

> ⚠️ **PRZECZYTAJ NAJPIERW SEKCJĘ 14.** TOS, w odróżnieniu od WMS, **nie ma out-of-box aplikacji REST**. Każdy endpoint musi być zarejestrowany jako „Integracja typu Serwis" w tabeli `con_integration` Pinquark. Sekcja 14 opisuje cały mechanizm + zawiera gotowy generator SQL (`setup_tos_integrations.sql`), który dostarczasz jako artefakt razem z konektorem (`integrators/wms/pinquark-tos/v1.0.0/sql/setup_tos_integrations.sql`) i opisujesz w README.

**Strategia:** sklonuj `integrators/wms/pinquark-wms/v1.0.0/` i przebuduj mapping na reakcje TOS.

#### 2.1. Klucze różnice vs `pinquark-wms`

| Aspekt | `pinquark-wms` | `pinquark-tos` |
|---|---|---|
| Kategoria | `wms` | `wms` (taka sama, oba to systemy magazynowe Pinquark) |
| `display_name` | "Pinquark WMS" | "Pinquark TOS" |
| `interface` | `wms` | `tos` (terminal operating system) |
| Out-of-box REST API | **TAK** — aplikacja `integration-rest` na :8090 z endpointami `/articles`, `/documents` itd. | **NIE** — TOS to platforma low-code bez wbudowanych endpointów; każdy endpoint trzeba **zarejestrować** ręcznie jako „Integracja własna typu Serwis" (patrz **sekcja 14**) |
| Auth | Bearer JWT | Bearer JWT + nagłówek `token-mer: <token>` (token z tabeli `con_token`) |
| URL endpointu | Stały `/articles`, `/documents`, `/positions`, `/contractors` | Generowany dynamicznie po rejestracji integracji — `/{integration_name}` lub konfigurowalny w `con_integration.data` JSON. **Domyślny pattern dla TOS:** `/{integration_name}` gdzie `integration_name` ustawiamy taki sam jak nazwa reakcji (`tos_notification_rail_save` → `POST /tos_notification_rail_save`). |
| Procedura wykonywana | Aplikacja Java parsuje JSON → wstawia do bazy WMS | Aplikacja Pinquark wywołuje **reakcję** (`app_reaction`) z tabeli `con_integration.app_reaction_id` → reakcja uruchamia procedurę PL/pgSQL (`tos_*`) |
| Dodanie nowego endpointu | Wymaga zmian w kodzie aplikacji Java + redeploy | **INSERT do `con_integration` + powiązanie z tokenem przez `con_integration_token`** — żywy efekt natychmiast |

#### 2.2. Lista akcji do zaimplementowania

Każda akcja = wywołanie REST do reakcji TOS. URL pattern: `POST {base_url}/integration/{reaction_name}` z nagłówkiem `token-mer: <token>` i body JSON.

| Action | Endpoint TOS | Opis |
|---|---|---|
| `awk.create` | `/integration/tos_notification_rail_save` | Tworzy/aktualizuje awizację kolejową |
| `awk.approve` | `/integration/tos_notification_rail_approve` | Zatwierdza AWK → tworzy KZT |
| `awk.cancel` | `/integration/tos_notification_rail_cancel` | Anuluje AWK kaskadowo |
| `awk.copy` | `/integration/tos_notification_rail_copy` | Klonuje AWK |
| `awk.create_outbound` | `/integration/tos_notification_rail_create_outbound` | Awizacja wyjazdowa |
| `awd.create` | `/integration/tos_notification_road_save` | Awizacja drogowa |
| `awd.approve` | `/integration/tos_notification_road_approve` | |
| `awd.cancel` | `/integration/tos_notification_road_cancel` | |
| `awd.generate_pickup` | `/integration/tos_awd_generate_pickup` | AWD odbiorcza |
| `train.add_wagon` | `/integration/tos_train_wagon_add` | Dodaje wagon do AWK |
| `train.add_container` | `/integration/tos_train_container_add` | Dodaje kontener do wagonu |
| `train.move_wagon_up` | `/integration/tos_wagon_move_up` | Zmiana kolejności |
| `train.move_wagon_down` | `/integration/tos_wagon_move_down` | |
| `gate.rail_entry_confirm` | `/integration/tos_gate_rail_entry_confirm` | Potwierdza wjazd pociągu |
| `gate.rail_entry_reject` | `/integration/tos_gate_rail_entry_reject` | Odrzuca wjazd |
| `gate.rail_exit_confirm` | `/integration/tos_gate_rail_exit_confirm` | Wyjazd pociągu |
| `gate.road_entry_confirm` | `/integration/tos_gate_road_entry_confirm` | Wjazd ciężarówki (rejestracja) |
| `gate.road_zdb_confirm` | `/integration/tos_gate_road_zdb_confirm` | Otwarcie szlabanu |
| `gate.road_exit_prepare` | `/integration/tos_gate_road_exit_prepare` | Przygotowanie wyjazdu |
| `gate.road_entry_reject` | `/integration/tos_gate_road_entry_reject` | |
| `gate.ocr_override` | `/integration/tos_gate_ocr_override` | Korekta OCR tablic |
| `gate.assign_track` | `/integration/tos_gate_assign_track` | Przypisanie toru |
| `movement.save` | `/integration/tos_movement_save` | Zapis dokumentu PRZ |
| `movement.execute` | `/integration/tos_movement_execute` | Start operacji |
| `movement.complete` | `/integration/tos_movement_complete` | Zakończenie PRZ |
| `operation.unload_save` | `/integration/tos_operation_unload_save` | Operacja wyładunku |
| `operation.load_save` | `/integration/tos_operation_load_save` | Operacja załadunku |
| `operation.transload_save` | `/integration/tos_operation_transload_save` | Przeładunek |
| `operation.move_save` | `/integration/tos_operation_move_save` | Przesunięcie |
| `operation.start` | `/integration/tos_operation_start` | |
| `operation.complete` | `/integration/tos_operation_complete` | Zakończenie operacji suwnicy |
| `operation.cancel` | `/integration/tos_operation_cancel` | |
| `zt_rail.save` | `/integration/tos_zt_rail_save` | Zlecenie kolejowe |
| `zt_road.save` | `/integration/tos_zt_road_save` | Zlecenie drogowe |
| `zt.change_status` | `/integration/tos_zt_change_status` | |
| `damage.report` | `/integration/tos_damage_report_save` | Zgłoszenie uszkodzenia |
| `photo.save` | `/integration/tos_photo_save` | Zdjęcie kontenera |
| `parking.queue_register` | `/integration/tos_parking_queue_register` | Wjazd na parking |
| `parking.queue_call_to_gate` | `/integration/tos_parking_queue_call_to_gate` | Wezwanie z parkingu |
| `validate.vehicle_number` | `/integration/tos_validate_vehicle_number` | Walidacja numeru rejestracyjnego |
| `validate.container_code` | `/integration/tos_validate_container_code` | Walidacja kodu ISO 6346 |
| `validate.slot_availability` | `/integration/tos_validate_slot_availability` | Sprawdzenie dostępności slotu |

Pełna lista źródłowych nazw funkcji w `/Users/mateuszkalinowski/Downloads/pinquark_implementation/clip/TOS/tos_procedures.sql`. Każda funkcja przyjmuje pojedynczy parametr `p_data json` i zwraca `jsonb` ze strukturą:

```json
{
  "status": "OK" | "ERROR",
  "message": "...",
  "data": { ...specyficzne dla operacji... }
}
```

#### 2.3. Konwencja payload-u TOS

Reakcje TOS przyjmują JSON z przemieszanymi:
- standardowymi polami WMS (`wmsContractorId`, `warehouseSymbol`, `note`),
- atrybutami EAV w postaci `attributes: [{symbol: "TOS_DOC_TRAIN_NO", valueText: "MET-204"}, ...]`,
- specyficznymi sekcjami (`wagons: []`, `containers: []`).

Przykład payload dla `tos_notification_rail_save`:
```json
{
  "wmsContractorId": 123,
  "warehouseSymbol": "MAL01",
  "tos_train_no": "MET-204",
  "tos_doc_planned_arrival": "2026-04-20T14:30:00Z",
  "carrier_id": 456,
  "attributes": [
    {"symbol": "TOS_DOC_BOOKING_REF", "valueText": "BK-2026-0042"},
    {"symbol": "TOS_DOC_BL_REF", "valueText": "MEDU1234567"}
  ]
}
```

W `connector.yaml` zdefiniuj `action_fields` szczegółowo dla każdej akcji — patrz `pinquark-wms/v1.0.0/connector.yaml` jako wzorzec (sekcja `action_fields:`).

#### 2.4. Struktura plików (klon `pinquark-wms`)

```
integrators/wms/pinquark-tos/v1.0.0/
├── .env.example
├── Dockerfile
├── connector.yaml          # nowy — z mapowaniem na reakcje TOS
├── docker-compose.yml
├── requirements.txt
└── src/
    ├── __init__.py
    ├── api/
    │   ├── dependencies.py
    │   └── routes.py       # routing per action → klient TOS
    ├── config.py
    ├── main.py
    ├── schemas/
    │   ├── awk.py
    │   ├── awd.py
    │   ├── train.py
    │   ├── gate.py
    │   ├── movement.py
    │   └── common.py
    └── services/
        ├── account_manager.py
        └── tos_client.py    # klient REST do Pinquark TOS z token-mer
```

#### 2.5. Klient REST TOS

W `src/services/tos_client.py`:

```python
class TosClient:
    def __init__(self, base_url: str, bearer_token: str, mer_token: str, account_name: str):
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.mer_token = mer_token
        self.account_name = account_name
        self._client: httpx.AsyncClient | None = None

    async def _request_with_retry(self, reaction_name: str, payload: dict) -> dict:
        client = await self._get_client()
        response = await client.post(
            f"/integration/{reaction_name}",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "token-mer": self.mer_token,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") == "ERROR":
            raise TosClientError(
                status_code=400,
                message=result.get("message", "TOS reaction failed"),
                details=result,
            )
        return result

    async def call_reaction(self, reaction_name: str, payload: dict) -> dict:
        return await self._request_with_retry(reaction_name, payload)
```

Akcje routes w `src/api/routes.py` mapują się 1:1 do `tos_client.call_reaction(reaction_name, payload)`.

#### 2.6. Health check

W `tos_client`:
```python
async def check_health(self) -> dict:
    response = await client.get("/integration/health", headers={"token-mer": self.mer_token})
    return {"status": "healthy"} if response.status_code == 200 else {"status": "unhealthy"}
```

(Endpoint `/integration/health` w Pinquark TOS to standardowy ping platformy.)

---

### Zadanie 3 — Workflow templates

Lokalizacja: `docs/workflows/tos-edi/`

Utwórz dokumentację z gotowymi YAML-ami workflow do importu w UI OIP. Workflowy są **partner-agnostyczne** — istnieje **jeden workflow per komunikat EDIFACT** (nie n × m: komunikat × partner), a różnice między partnerami sprowadzają się do parametrów konta (`account.yaml`). Onboarding nowego partnera = dodanie jednego pliku account, **zero nowych workflow ani konektorów**.

> Wszystkie workflowy używają `account: "{{trigger.account}}"` (inbound) lub `account: "{{partner.edi_account}}"` (outbound) — nazwa konta jest wstrzykiwana z eventu lub z partner registry, **nigdy nie hardcodowana**. To gwarantuje że ten sam YAML obsługuje N partnerów.

#### 3.1. Inbound (generyczny): COPRAR → TOS AWK Rail

Plik: `docs/workflows/tos-edi/01_coprar_inbound.yaml`

```yaml
name: "COPRAR → TOS AWK Rail (SMDG D.95B/D.00B/SMDG 2.0)"
description: |
  Generyczny workflow obsługi COPRAR (preadvice pociągu).
  Pobiera plik z SFTP DOWOLNEGO partnera (Metrans, HHLA, Kombi,
  DB Cargo, PKP Cargo Connect itd.), waliduje wg standardu SMDG,
  wysyła APERAK ACK, tworzy AWK w TOS z wagonami i kontenerami.

  Workflow jest partner-agnostyczny: account jest wstrzykiwany
  przez trigger.account (FTP konta partnera) i mapowany na konto
  EDIFACT przez partner registry.

trigger:
  connector: ftp-sftp
  event: file.new
  # WAŻNE: filter NIE zawęża do konkretnego partnera.
  # Każdy partner ma osobny account FTP z własnym remote_path,
  # ale używa tego samego workflow.
  filter:
    path_pattern: "**/COPRAR_*.edi"     # match w katalogach inbound dowolnego partnera

nodes:

  # 1) Z konta SFTP wyciągnij identyfikator partnera (lookup w partner registry)
  - id: resolve-partner
    type: action
    connector: oip-internal
    action: partner_registry.resolve_by_ftp_account
    input:
      ftp_account: "{{ trigger.account }}"
    # output: { partner_code, edifact_account, smdg_profile, sender_id, receiver_id }

  # 2) Sparsuj COPRAR — konektor edifact używa standardu SMDG, nie zależy od partnera
  - id: parse-edi
    type: action
    connector: edifact
    account: "{{ resolve-partner.edifact_account }}"   # wstrzyknięte z registry
    action: coprar.parse
    input:
      content_base64: "{{ trigger.content_base64 }}"

  # 3) Wyślij APERAK ACK z powrotem na ten sam SFTP
  - id: build-aperak
    type: action
    connector: edifact
    account: "{{ resolve-partner.edifact_account }}"
    action: aperak.build
    input:
      referenced_message_ref: "{{ parse-edi.message_ref }}"
      referenced_interchange_ref: "{{ parse-edi.interchange_ref }}"
      response_type: "accepted"

  - id: send-aperak
    type: action
    connector: ftp-sftp
    account: "{{ trigger.account }}"
    action: file.upload
    input:
      remote_path: "/outbound/APERAK_{{ parse-edi.message_ref }}.edi"
      content_base64: "{{ build-aperak.content_base64 }}"

  # 4) Stwórz AWK w TOS — TOS jest jeden, account zawsze 'clip-malaszewicze'
  - id: create-awk
    type: action
    connector: pinquark-tos
    account: clip-malaszewicze
    action: awk.create
    mapping:
      - from: "parse-edi.payload.train_no"          -> to: "tos_train_no"
      - from: "parse-edi.payload.eta"               -> to: "tos_doc_planned_arrival"
      - from: "parse-edi.payload.carrier.code"      -> to: "carrier_code"
      - from: "parse-edi.payload.pol.un_locode"     -> to: "TOS_DOC_POL"
      - from: "parse-edi.payload.pod.un_locode"     -> to: "TOS_DOC_POD"
      - const: "{{ resolve-partner.partner_code }}" -> to: "TOS_EDI_PARTNER_CODE"   # zapisuje partnera w EAV
    output_var: "awk"

  - id: add-wagons
    type: foreach
    iterate: "{{ parse-edi.payload.wagons }}"
    body:
      - id: add-wagon
        type: action
        connector: pinquark-tos
        account: clip-malaszewicze
        action: train.add_wagon
        mapping:
          - from: "item.wagon_no"        -> to: "wagon_number"
          - from: "item.wagon_type"      -> to: "wagon_type"
          - from: "item.sequence_no"     -> to: "sequence_no"
          - const: "{{ awk.doc_id }}"    -> to: "wms_doc_id"
        output_var: "wagon"

      - id: add-containers
        type: foreach
        iterate: "{{ item.containers }}"
        body:
          - type: action
            connector: pinquark-tos
            account: clip-malaszewicze
            action: train.add_container
            mapping:
              - from: "item.container_no"     -> to: "container_number"
              - from: "item.iso_size_type"    -> to: "container_type"
              - from: "item.weight_kg"        -> to: "weight"
              - from: "item.is_empty"         -> to: "is_empty"
              - from: "item.seal_no"          -> to: "seal_no"
              - const: "{{ wagon.wagon_id }}" -> to: "wagon_id"
              - const: "{{ awk.doc_id }}"     -> to: "wms_doc_id"

  - id: archive-source
    type: action
    connector: ftp-sftp
    account: "{{ trigger.account }}"
    action: file.move
    input:
      source_path: "{{ trigger.path }}"
      destination_path: "/processed/{{ trigger.filename }}"

error_handler:
  - id: send-aperak-error
    type: action
    connector: edifact
    account: "{{ resolve-partner.edifact_account }}"
    action: aperak.build
    input:
      referenced_message_ref: "{{ parse-edi.message_ref }}"
      response_type: "rejected"
      errors: "{{ error.details }}"

  - type: action
    connector: ftp-sftp
    account: "{{ trigger.account }}"
    action: file.upload
    input:
      remote_path: "/outbound/APERAK_REJ_{{ parse-edi.message_ref }}.edi"
      content_base64: "{{ send-aperak-error.content_base64 }}"
```

**Kluczowe: ten jeden workflow obsługuje wszystkich partnerów.** Dodanie 6. partnera EDI to:
1. Dodanie konta SFTP w `accounts/ftp-sftp/<partner-code>-sftp.yaml`,
2. Dodanie konta EDIFACT w `accounts/edifact/<partner-code>-edi.yaml` (sender_id, receiver_id, smdg_profile),
3. Dodanie wpisu do partner registry (sekcja 6) — mapping `ftp_account → partner_code → edifact_account`.

Brak modyfikacji workflow, brak kodu, zero deploya.

#### 3.2. Outbound (pull pattern, generyczny): TOS audit log → CODECO

Plik: `docs/workflows/tos-edi/02_codeco_outbound.yaml`

> Workflow jest **podworkflowem** (`workflow.invoke`) wywoływanym przez `tos-poll-events` (sekcja 14.6.4) dla eventów `event_type` ∈ {`WJAZD_TIR_POTWIERDZONY`, `WYJAZD_TIR_POTWIERDZONY`}. Trigger samodzielny (np. `schedule` co 30s) NIE jest tu używany — workflow odpala się dla każdego eventu z polling pętli.
>
> Workflow jest **partner-agnostyczny**: per event identyfikuje partnera/partnerów z `tos_doc.contractor_id` (przez kartotekę kontrahentów TOS → partner registry OIP) i wysyła CODECO do każdego z nich na ich SFTP/AS2 z ich sender/receiver IDs.

```yaml
name: "outbound-codeco-gate (TOS audit event → CODECO do partnera)"
description: |
  Subworkflow wywoływany przez tos-poll-events dla pojedynczego eventu
  WJAZD/WYJAZD_TIR_POTWIERDZONY. Buduje CODECO wg standardu SMDG i wysyła
  do WSZYSTKICH partnerów zarejestrowanych dla tego dokumentu.

inputs:
  event:                # { id, created_at, module, event_type, doc_id, doc_symbol, details }
    type: object
    required: true

nodes:

  # 1) Wyciągnij snapshot dokumentu z TOS (kontenery, kontrahent, partnerzy EDI)
  - id: enrich-doc
    type: action
    connector: pinquark-tos
    account: clip-malaszewicze
    action: tos_doc_get_status
    input:
      doc_id: "{{ inputs.event.doc_id }}"
    # output zawiera m.in.: contractor_code, edi_partner_codes[]

  # 2) Z partner registry OIP wyciągnij listę kont (FTP+EDIFACT) dla każdego partnera
  - id: resolve-partners
    type: action
    connector: oip-internal
    action: partner_registry.resolve_by_codes
    input:
      partner_codes: "{{ enrich-doc.edi_partner_codes }}"   # [['METRANS'], ['HHLA']] etc.
    # output: [{ partner_code, edifact_account, ftp_account, smdg_profile }, ...]

  # 3) Dla każdego partnera zbuduj CODECO w jego wersji i wyślij na jego SFTP
  - id: send-to-partners
    type: foreach
    iterate: "{{ resolve-partners.partners }}"
    parallel: true                       # wysyłki do różnych partnerów są niezależne
    body:
      - id: build-codeco
        type: action
        connector: edifact
        account: "{{ item.edifact_account }}"   # per-partner: sender/receiver/wersja
        action: codeco.build
        mapping:
          - from: "inputs.event.details.event_type"   -> to: "event_type"
          - from: "inputs.event.created_at"           -> to: "event_timestamp"
          - from: "inputs.event.details.gate_code"    -> to: "locations[0].terminal_id"
          - from: "enrich-doc.containers"             -> to: "containers"
          - from: "inputs.event.id"                   -> to: "interchange_ref"   # idempotency
        output_var: "codeco"

      - id: send-codeco
        type: action
        connector: ftp-sftp
        account: "{{ item.ftp_account }}"           # per-partner: SFTP host/dir
        action: file.upload
        input:
          remote_path: "/outbound/CODECO_{{ inputs.event.doc_symbol }}_{{ inputs.event.id }}.edi"
          content_base64: "{{ codeco.content_base64 }}"
```

**Tryby fanout vs single-partner:** jeśli operacja w terminalu dotyczy kontenerów wielu partnerów (np. pociąg z mieszanymi liniami), `enrich-doc.edi_partner_codes` zwraca listę, a foreach `parallel: true` wysyła równolegle. Jeśli kontenery jednego partnera — lista ma jeden element. **Workflow ten sam.**

#### 3.3. Pełna lista 12 workflow templates do udokumentowania

> **Każdy workflow obsługuje wszystkich partnerów.** Konfiguracja per-partner siedzi w `accounts/` + partner registry (sekcja 6), nie w workflowach. Zmiana z 15 (per-partner) → 12 (generic per-message) eliminuje 3 zduplikowane workflowy HHLA/Kombi.

| # | Plik | Typ | Trigger | Action |
|---|---|---|---|---|
| 00 | `00_tos_poll_events.yaml` | scheduler | **co 30s** — main outbound hub (sekcja 14.6.4) | invoke 02/03/04 wg `event_type` |
| 01 | `01_coprar_inbound.yaml` | inbound | `ftp-sftp.file.new` (`**/COPRAR_*.edi`) | `pinquark-tos.awk.create` + add wagons/containers |
| 02 | `02_codeco_outbound.yaml` | outbound (subworkflow) | `workflow.invoke` z `tos-poll-events` (event_type=WJAZD/WYJAZD_TIR_POTWIERDZONY) | CODECO build + send do partnerów z registry |
| 03 | `03_coarri_outbound.yaml` | outbound (subworkflow) | `workflow.invoke` z `tos-poll-events` (event_type=PRZELAD_ZAKONCZONY) | COARRI build + send |
| 04 | `04_iftsta_outbound.yaml` | outbound (subworkflow) | `workflow.invoke` z `tos-poll-events` (event_type=POCIAG_PRZYJECHAL/ODJECHAL/USZKODZENIE_* / status doc change) | IFTSTA build + send |
| 05 | `05_coparn_inbound.yaml` | inbound | `ftp-sftp.file.new` (`**/COPARN_*.edi`) | `pinquark-tos.awd.create` (release order) |
| 06 | `06_cohaor_inbound.yaml` | inbound | `ftp-sftp.file.new` (`**/COHAOR_*.edi`) | `pinquark-tos.movement.save` (handling order) |
| 07 | `07_iftmin_inbound.yaml` | inbound | `ftp-sftp.file.new` (`**/IFTMIN_*.edi`) | `pinquark-tos.zt_rail.save` (booking) |
| 08 | `08_aperak_auto_response.yaml` | helper | template do `workflow.invoke` z każdego inbound (01,05,06,07) po sukcesie | APERAK accepted |
| 09 | `09_aperak_inbound_handling.yaml` | inbound (response handler) | `ftp-sftp.file.new` (`**/APERAK_*.edi` od partnera w odpowiedzi na nasz outbound) | log do bazy OIP + alert jeśli REJ |
| 10 | `10_contrl_auto_response.yaml` | helper | syntax ACK na każdy poprawny inbound | CONTRL |
| 11 | `11_dead_letter_queue.yaml` | error global | `error_handler` global per workflow | persist error + notify (Slack/email) |
| 12 | `12_reconciliation_daily.yaml` | scheduler | cron daily 02:00 | raport count IN vs OUT per partner per komunikat |

**Liczba workflow: 12 (stałe, niezależnie od liczby partnerów).** Kiedy podłączasz 6. partnera EDI (np. CD Cargo), nie powstaje żaden nowy workflow. Powstaje:
- 1 plik `accounts/ftp-sftp/cdcargo-sftp.yaml`,
- 1 plik `accounts/edifact/cdcargo-edi.yaml`,
- 1 wpis w partner registry (sekcja 6).

---

### Zadanie 4 — README dla integracji

Plik: `docs/workflows/tos-edi/README.md`

Powinien zawierać:
- Wstęp biznesowy (skopiuj sekcję 1 tego dokumentu).
- Diagram architektury (sekcja 2).
- Lista wymaganych konektorów (`edifact`, `ftp-sftp`, `pinquark-tos`, `webhook`).
- Konfiguracja accounts (przykłady `.env` i UI screenshots).
- Lista workflow templates (linki do YAML).
- Sekcja "Onboarding nowego partnera EDI" — krok po kroku.
- Sekcja "Troubleshooting" — typowe błędy parsowania, network errors, mapping issues.

---

### Zadanie 5 — Verification Agent

Rozszerz Verification Agent (`platform/verification-agent/`) aby umiał testować integracje EDI:

- **Tier 1 (infrastructure):** połączenie SFTP do każdego partnera, dostępność `pinquark-tos` health endpoint.
- **Tier 2 (auth):** test logowania do TOS z `token-mer`, test SFTP listing.
- **Tier 3 (functional):** wysłanie testowego pliku COPRAR do partnera testowego, weryfikacja zwrotnego APERAK; round-trip test build → parse dla każdego komunikatu.

To wymaga dodania w `connector.yaml` sekcji `verification_tests:` per akcja.

---

## 4. Konfiguracja accounts — przykład końcowy

### 4.1. Account `metrans-sftp` (konektor ftp-sftp)

```yaml
name: metrans-sftp
host: sftp.metrans.eu
protocol: sftp
port: 22
username: pinquark-clip
private_key: |
  -----BEGIN OPENSSH PRIVATE KEY-----
  ...
  -----END OPENSSH PRIVATE KEY-----
base_path: /pinquark-clip
polling_enabled: true
polling_path: /pinquark-clip/inbound
polling_interval_seconds: 60
```

### 4.2. Account `metrans-edi` (konektor edifact)

```yaml
name: metrans-edi
edifact_version: D95B
sender_id: PLMSCMAL01
receiver_id: METRANS
sequence_state_path: /var/lib/oip/sequences/metrans.json
# base_url i api_key opcjonalne — używamy w trybie parse/build,
# nie forwardujemy nigdzie (TOS jest osobnym konektorem)
```

### 4.3. Account `clip-malaszewicze` (konektor pinquark-tos)

```yaml
name: clip-malaszewicze
base_url: https://pinquark.clip-terminal.pl
bearer_token: eyJhbGciOi...
mer_token: a1b2c3d4-...
warehouse_symbol: MAL01
```

---

## 5. Bezpieczeństwo

- **Wszystkie credentiale** trzymaj w `credential_vault.py` (AES-256-GCM, już istnieje).
- **Komunikacja TOS → OIP** (outbound EDI) odbywa się przez **polling** — OIP jest klientem REST, który uderza do TOS z `Authorization: Bearer <jwt>` + `token-mer: <token>`. Brak webhooków z TOS → brak konieczności wystawiania `webhook_ingestion.py` dla TOS i brak konieczności ustanawiania per-partner HMAC. (`webhook_ingestion.py` zostaje dla scenariuszy partner→OIP, np. powiadomienia od liniowców kontenerowych.)
- **SFTP private keys** przechowuj jako pliki w wolumenie z `chmod 600`, nie w bazie.
- **Audyt każdej akcji** automatyczny przez `audit_trail.py` — zapewnij że PII (np. dane kierowcy) jest maskowane przez `pii_redactor.py`.
- **Rate limit per partner** — w `connector.yaml` dla `pinquark-tos`:
  ```yaml
  rate_limits:
    default: "120/min"
    per_action:
      gate.road_zdb_confirm: "30/min"
      operation.complete: "60/min"
  ```

---

## 6. Co NIE wchodzi w zakres tego zadania

- **Parser AS2** — to osobny konektor, na razie zostajemy przy SFTP/email.
- **Konektor BAPLIE rozszerzony** — BAPLIE jest głównie dla maritime, intermodal kolejowy go nie używa. Zostaw obecną implementację.
- **Modyfikacje w repo TOS** — patrz sekcja 12, to robi inny agent w innym repo. Twoje zadanie kończy się na granicy `pinquark-tos` connectora.
- **UI builder workflow** — UI istnieje, użytkownicy konfigurują workflow w dashboardzie. Twoja praca to YAML templates do importu.

---

## 7. Definicja "done"

Zadanie jest skończone gdy:

- [ ] Konektor `edifact` ma capabilities/actions/schemas/routes/tests dla COPRAR, COPARN, COHAOR, COARRI, IFTSTA, APERAK, CONTRL.
- [ ] Konektor `edifact` ma raw EDI parser i builder z testami round-trip dla wszystkich komunikatów.
- [ ] Konektor `edifact` obsługuje wersje D.95B, D.00B, SMDG 2.0 per account.
- [ ] Nowy konektor `pinquark-tos` istnieje z wszystkimi akcjami z sekcji 2.2 (40 akcji łącznie, w tym `tos_get_events_since` i `tos_get_doc_status_changes_since` dla outbound polling) i przechodzi health check.
- [ ] `docs/workflows/tos-edi/` zawiera 15 workflow templates z sekcji 3.3 (w tym `00_tos_poll_events.yaml` jako główny outbound hub) + README opisujący pull pattern (sekcja 14.6).
- [ ] `setup_tos_integrations.sql` (sekcja 14.5) jest dołączony do konektora `pinquark-tos` w `integrators/wms/pinquark-tos/v1.0.0/sql/` z README opisującym proces uruchomienia po stronie TOS.
- [ ] Wszystkie nowe komponenty mają testy jednostkowe (pytest, ≥80% coverage dla nowego kodu).
- [ ] Verification Agent ma testy dla `pinquark-tos` (3 tiers) i smoke test EDI round-trip.
- [ ] CHANGELOG.md zaktualizowany.
- [ ] Wszystkie zmiany zgodne z `AGENTS.md` w root OIP — Ruff lint zielony, type hints, docstrings.

---

## 8. Standardy implementacyjne (z OIP `AGENTS.md`)

Przypomnienie najważniejszych:

- Python 3.12+, async/await, FastAPI, Pydantic v2.
- Każdy connector to mikroserwis z własnym `Dockerfile`, `docker-compose.yml`, `requirements.txt`.
- `connector.yaml` jest jedynym źródłem prawdy o konektorze — platform discovery czyta to przy starcie.
- Logging: `pinquark_common.logging.setup_logging`.
- Health: `pinquark_common.monitoring.health.HealthChecker`.
- Prometheus metrics na `/metrics`.
- Account management: per-account credentials w `account_manager.py` z `load_from_yaml`.
- Retry: exponential backoff z jitterem (wzorzec w `edifact_client.py`).
- Errors: dziedzicz po `*ClientError` z `status_code`, `message`, `details`.
- Tests: `pytest` + `httpx.AsyncClient(transport=ASGITransport(app=app))`.

---

## 9. Roadmapa szczegółowa (~10 dni roboczych)

> **Uwagi do estymaty:**
> - Plan zakłada pull pattern dla outbound EDI (sekcja 14.6) — względem wersji push/webhook: -2 dni.
> - Plan zakłada **partner-agnostyczne** workflowy (sekcja 3.3, 14.6.4) — względem wersji per-partner: -2 dni (3 zduplikowane workflowy HHLA/Kombi nie istnieją; jedynie konfiguracja w `accounts/` + partner registry).
> - Wszystkie 4 nowe procedury PL/pgSQL po stronie TOS Mateusz dorabia w ~6 h równolegle do prac OIP.

| Dzień | Praca |
|---|---|
| 1 | Klon `pinquark-wms` → `pinquark-tos`, podstawowy `connector.yaml`, `tos_client.py`, health, **dwie akcje read-only `tos_get_events_since`/`tos_get_doc_status_changes_since`** (kluczowe dla outbound) |
| 2 | Pozostałe akcje `pinquark-tos`: awizacje (awk.*, awd.*, train.*), bramy/ruch (gate.*, movement.*, operation.*) |
| 3 | Pozostałe akcje + finalizacja `connector.yaml` (40 akcji łącznie) + **wewnętrzny konektor `oip-internal` z partner_registry.* (sekcja 14.6.6)** + tabela `oip_edi.partner_registry` w bazie OIP |
| 4 | Parser + Builder EDIFACT (`pydifact`, `edifact_parser.py`, `edifact_builder.py`) + round-trip testy + obsługa SMDG profili (1.5/2.0) i wersji (D.95B/D.00B) jako **parametry konta**, NIE per partner kod |
| 5 | COPRAR + COPARN — schemas + routes + builder + parser + fixture files |
| 6 | COHAOR + COARRI + IFTMIN — schemas + routes + builder + parser |
| 7 | IFTSTA (mapping statusów TOS → SMDG codes) + APERAK + CONTRL + auto-response logic |
| 8 | Workflow templates **partner-agnostyczne**: `00_tos_poll_events.yaml` (główny hub) + `01_coprar_inbound.yaml` + `02_codeco_outbound.yaml` + `03_coarri_outbound.yaml` + `04_iftsta_outbound.yaml` + `05_coparn_inbound.yaml` |
| 9 | Workflow templates: `06_cohaor_inbound.yaml` + `07_iftmin_inbound.yaml` + `08_aperak_auto_response.yaml` + `09_aperak_inbound_handling.yaml` + `10_contrl_auto_response.yaml` + `11_dead_letter_queue.yaml` + `12_reconciliation_daily.yaml` + integracja z `setup_tos_integrations.sql` (sekcja 14.5) |
| 10 | README (pull pattern, partner registry, **onboarding nowego partnera w 6 krokach** — sekcja 14.6.6), troubleshooting (sekcja 14.11), Verification Agent extensions (test polling + at-least-once + multi-partner fanout), CHANGELOG, code review, release |

---

## 10. Zasoby referencyjne

| Co | Gdzie |
|---|---|
| Pełny kod TOS (procedury, ekrany, dokumentacja) | `/Users/mateuszkalinowski/Downloads/pinquark_implementation/clip/TOS/` |
| Lista wszystkich procedur TOS | `clip/TOS/tos_procedures.sql` (function names: `tos_*`) |
| Logika biznesowa procedur | `clip/TOS/procedury_logika_biznesowa.md` |
| Dokumentacja API Pinquark | `clip/TOS/docs/dokumentacja_techniczna_api.md` (sekcja "token-mer") |
| Struktura bazy TOS (tabele, EAV) | `clip/TOS/raport_struktura_bazy.md` |
| Wzorzec connector.yaml | `integrators/wms/pinquark-wms/v1.0.0/connector.yaml` |
| Wzorzec parser-less EDIFACT | `integrators/other/edifact/v1.0.0/` (obecny stan) |
| Specyfikacja UN/EDIFACT | https://unece.org/trade/uncefact/introducing-unedifact |
| Specyfikacja SMDG | https://smdg.org/documents/smdg-message-standards/ |
| Biblioteka pydifact | https://github.com/nerdocs/pydifact |
| Lista kodów ISO 6346 (kontenery) | https://en.wikipedia.org/wiki/ISO_6346 |
| Lista UN/LOCODE | https://unece.org/trade/cefact/unlocode-code-list-country-and-territory |

---

## 11. Pytania do twórcy projektu (Mateusza)

Jeśli napotkasz dwuznaczności, zapytaj autora przed implementacją.

> **Założenie bazowe (rozstrzygnięte):** OIP eksponuje **jeden standard SMDG/EDIFACT**, do którego partnerzy się dostosowują. Workflowy są **partner-agnostyczne** (sekcja 3.3 — 12 templatów stałych, niezależnie od liczby partnerów). Per-partner zmienia się tylko `account` (sekcja 14.6.6 — partner registry). Dlatego pytania per partner są ograniczone do kwestii konfiguracyjnych, nie kodowych.

1. **Lista partnerów pilotażowych** — z kim Clip robi pierwszy UAT? (Pierwsza wersja partner registry — sekcja 14.6.6. Domyślnie zakładam: Metrans, HHLA, Kombiverkehr, PKP Cargo Connect.)
2. **Wersja EDIFACT i SMDG profile per partner** — wartości do wpisania w `oip_edi.partner_registry.edifact_version` i `smdg_profile`. Standardowo: D.00B + SMDG 2.0; starsze podmioty trzymają D.95B + SMDG 1.5. **NIE** powoduje to nowych workflow — wpływa wyłącznie na konfigurację konta.
3. **Próbki plików `.edi` od partnera** — przynajmniej 1 sample każdego z: COPRAR, COPARN, COHAOR, IFTMIN. Potrzebne do walidacji parsera (test fixtures w konektorze `edifact`).
4. **Capabilities partnerów** — które z opcjonalnych komunikatów partnerzy obsługują (`supports_yard_move`, `needs_iftsta_progress`, `wants_coarri_per_lift_or_per_train`)? To pole `capabilities` w partner registry — workflowy odczytują je do conditional sendów.
5. **Tokeny i credentiale TOS** — jeden globalny `token-mer` dla całego OIP czy osobny per workflow? **Domyślnie spec zakłada jeden globalny** (sekcja 14.5). Potwierdź z compliance.
6. **SLA dla APERAK** — typowo 5 min, niektórzy partnerzy oczekują <30 s. **Pull pattern wprowadza latency 30–60 s** (sekcja 14.6). Jeśli któryś partner ma SLA <30 s — zmniejsz interwał polling do 5–10 s globalnie (decyzja Clip), bo nie chcemy per-partner pollerów.
7. **Interwał pollingu `tos-poll-events`** — domyślnie 30 s (sekcja 14.6.4). Akceptowalny dla EDI rail. Decyzja Clip-Małaszewicze: ?
8. **Filtr `modules` w `tos_get_events_since`** — czy uruchomić jeden poller dla całego ruchu, czy podzielić per moduł (Bramy/Operacje/Awizacje) dla równoległości i izolacji błędów? Domyślnie sekcja 14.6.4 zakłada jeden — wystarczy do 5000 evt/30 s. **Nie ma to wpływu na liczbę workflow EDI** — to wyłącznie podział pollera infrastrukturalny.
9. **URL pattern integracji własnych Pinquark TOS** — sekcja 14.3 zakłada `/integration/{name}`. Potwierdź faktyczny pattern u admina TOS.
10. **Symbol „Własna" w `con_lib_integration_type`** — `'OWN'`, `'CUSTOM'` czy `'WLASNA'` w bazie Clip? Wpływa na `WHERE symbol = '...'` w skrypcie 14.5.
11. **Magazyn i owner** — `wms_warehouse.symbol = 'CLIP_MALASZEWICZE'` i `wms_company.symbol = 'CLIP'` to założenie. Potwierdź.
12. **Pełny zestaw `event_type` w `tos_audit_log`** — sekcja 14.6.5 zawiera mapowanie 10 najważniejszych typów. Run: `SELECT DISTINCT event_type FROM tos_audit_log ORDER BY 1` na production-like DB i prześlij — uzupełnimy mapping w `00_tos_poll_events.yaml` jeśli pojawią się nieznane typy.
13. **EAV `TOS_EDI_PARTNER_CODES` i `tos_default_edi_partner_codes` na kontrahencie** — sekcja 14.6.6 zakłada że TOS udostępnia pole CSV z kodami partnerów EDI per dokument (z fallbackiem na kontrahenta). Potwierdź gotowość rozszerzenia kartoteki kontrahentów lub powiedz, że dziedziczenie ma iść inną drogą (np. zawsze ze zlecenia transportowego).

---

## 12. Strona TOS (referencja, NIE TWOJE ZADANIE)

Tu opis tego, co ZRÓBI agent po stronie TOS — żebyś rozumiał kontekst integracji. **Pełny opis architektury, konwencji i gotowy generator SQL — patrz sekcja 14.** Ta sekcja to TL;DR dla części TOS.

### 12.1. Po stronie TOS dojdą (TYLKO):

1. **4 nowe procedury PL/pgSQL** (read-only, ~6 h pracy) — wszystkie bez modyfikowania istniejącej logiki biznesowej:
   - `tos_get_events_since(p_data json) RETURNS json` — **krytyczne M0** — polluje `tos_audit_log` od kursora. Gotowy kod w sekcji 14.6.2.
   - `tos_get_doc_status_changes_since(p_data json) RETURNS json` — **krytyczne M0** — polluje `wms_doc_status_history`. Gotowy kod w sekcji 14.6.3.
   - `tos_doc_get_status(p_data json) RETURNS json` — M1 — IFTSTA pull request od partnera.
   - `tos_container_get_status(p_data json) RETURNS json` — M1 — IFTSTA pull request od partnera.
2. **5 INSERT-ów w `tos_reactions.sql`** rejestrujących powyższe procedury jako reakcje (+ 1 fix dla bug-a `tos_gate_road_exit_confirm`).
3. **Integracje typu Serwis w Pinquark TOS** — uruchomienie generatora `setup_tos_integrations.sql` (sekcja 14.5). Tworzy 40 wpisów w `con_integration` + 40 w `con_integration_token` + 1 wspólny token w `con_token`.

**Czego po stronie TOS NIE robimy** (architektonicznie odpadło dzięki pull patternowi):
- ❌ helper `tos_webhook_emit`
- ❌ wpięcia `PERFORM` w żadnej z istniejących procedur biznesowych
- ❌ integracji typu Klient (`con_integration.kind = 'CLIENT'`)
- ❌ wpisów w `con_connection` z URL OIP
- ❌ tabeli `tos_edi_message_log`
- ❌ rozszerzenia `pg_net`/`plperlu` w PostgreSQL TOS

### 12.2. Co TOS UDOSTĘPNIA OIP do pollingu (outbound EDI)

| Endpoint TOS | Co zwraca | Generuje EDI | Polling przez OIP |
|---|---|---|---|
| `tos_get_events_since` | Nowe wpisy z `tos_audit_log` od kursora `last_audit_id` (eventy: AWK zatwierdzona, wjazd/wyjazd potwierdzony, przeładunek zakończony, status zmieniony, uszkodzenie zgłoszone, ...) | **APERAK, CODECO, COARRI, IFTSTA** (wszystkie outbound) | Workflow `tos-poll-events` co 30s |
| `tos_get_doc_status_changes_since` | Nowe wpisy z `wms_doc_status_history` od kursora `last_history_id` | **IFTSTA** (uzupełnienie) | Ten sam workflow, opcjonalnie |
| `tos_doc_get_status` | Aktualny snapshot dokumentu | **IFTSTA response** | On-demand (request od partnera) |
| `tos_container_get_status` | Aktualny snapshot kontenera | **IFTSTA response** | On-demand |

Mapowanie `event_type` → komunikat EDIFACT — sekcja 14.6.5.

### 12.3. Co TOS PRZYJMUJE od OIP (inbound — REST `/integration/tos_*`)

36 istniejących reakcji biznesowych TOS (lista: sekcja 14.4a A1–A11) — wywoływane przez konektor `pinquark-tos` przy obsłudze inbound EDI (COPRAR, COPARN, COHAOR, IFTMIN). Auth: `Authorization: Bearer <jwt>` + `token-mer: <token>`.

---

## 14. Mechanizm „Integracje własne" w Pinquark TOS

Ta sekcja jest **kluczowa** dla zrozumienia, jak konektor `pinquark-tos` (zadanie 2) komunikuje się z TOS. Opisuje różnicę architektoniczną między Pinquark **WMS** (gdzie istnieje gotowa aplikacja `integration-rest` z predefiniowanymi endpointami) a Pinquark **TOS** (gdzie nie ma takiej aplikacji — REST API trzeba zbudować ręcznie z klocków platformy low-code).

### 14.1. Dlaczego TOS nie ma out-of-box REST API

Pinquark to platforma low-code, w której każdy klient buduje swoją aplikację (ekrany + procedury PL/pgSQL + reakcje). Dla **WMS** Pinquark dostarcza dodatkowo aplikację `integration-rest` (Java/Kafka, dokumentowaną w `clip/TOS/docs/dokumentacja_techniczna_api.md` pkt 7) z gotowymi endpointami (`/articles`, `/documents`, `/positions`, `/contractors`) — bo magazyn ma standardowy zestaw operacji.

Dla **TOS** taka aplikacja nie istnieje, ponieważ:
- TOS to znacznie węższa domena (intermodal/terminal),
- każde wdrożenie ma inną logikę bramowania, awizacji, suwnic,
- nie ma sensu definiować „uniwersalnych" endpointów REST.

Zamiast tego Pinquark udostępnia **mechanizm „Integracje własne"** — generyczną bramkę REST, która:
1. nasłuchuje pod jednym hostem (typowo `https://<klient>.pinquark.app/` lub on-prem `http://<host>:<port>/`),
2. przyjmuje POST z URL-em zawierającym **nazwę zarejestrowanej integracji**,
3. waliduje token w nagłówku `token-mer`,
4. uruchamia powiązaną reakcję (`app_reaction`) → która wywołuje procedurę PL/pgSQL,
5. zwraca JSON ze statusem (`OK`/`ERROR`).

Każdy „endpoint" TOS = wpis w tabeli `con_integration` + powiązany `con_token`. **Bez wpisu w bazie danych — endpoint nie istnieje.**

### 14.1.1. Architektura komunikacji: TOS = serwer, OIP = klient (TYLKO PULL)

Komunikacja TOS ↔ OIP jest **jednokierunkowa pod względem inicjacji**: zawsze inicjuje OIP, TOS zawsze odpowiada. Nie ma żadnych webhooków, callback URL-i ani integracji typu „Klient" po stronie TOS.

**Kluczowy fakt:** TOS już teraz ma w sobie **gotowy outbox** — tabelę `tos_audit_log`, do której **wszystkie procedury biznesowe** zapisują zdarzenia przez helper `tos_log_event(p_module, p_event_type, p_doc_id, p_doc_symbol, p_user_id, p_user_login, p_details JSONB)`. Wywołań tego helpera w `clip/TOS/tos_procedures.sql` jest **92** — pokrywają wszystkie istotne biznesowo zmiany (zatwierdzenia awizacji, potwierdzenia bramowe, zakończenia operacji suwnic, przesunięcia kontenerów, raporty uszkodzeń itd.). Plus standardowa Pinquark tabela `wms_doc_status_history` zawiera każdą zmianę statusu dokumentu z timestampem i `adm_user_id`.

```sql
-- Już istniejąca tabela TOS — nasz natywny outbox dla EDI
CREATE TABLE public.tos_audit_log (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    module          TEXT      NOT NULL,   -- 'Awizacje', 'Bramy', 'Operacje', 'ZT', ...
    event_type      TEXT      NOT NULL,   -- 'AWK_ZAPISANA', 'WJAZD_POTWIERDZONY', 'PRZELAD_ZAKONCZONY', ...
    doc_id          INTEGER,              -- FK na wms_doc
    doc_symbol      TEXT,                 -- np. 'AWK-20260415001'
    user_id         INTEGER,
    user_login      TEXT,
    details         JSONB                 -- payload z polami specyficznymi dla zdarzenia + old_data/new_data
);
CREATE INDEX tos_audit_log_created_idx ON public.tos_audit_log (created_at DESC);
CREATE INDEX tos_audit_log_module_idx  ON public.tos_audit_log (module);
CREATE INDEX tos_audit_log_doc_idx     ON public.tos_audit_log (doc_id) WHERE doc_id IS NOT NULL;
```

OIP poluje tę tabelę przez nowy endpoint Serwis `tos_get_events_since(last_audit_id, limit)` co 30 sekund, decyduje które zdarzenia generują EDI i wysyła wiadomości do partnerów. **Zero modyfikacji istniejących procedur TOS.** Pełny opis pull patternu z workflow YAML — sekcja **14.6**.

**Konsekwencje architektoniczne:**

| Aspekt | Stan |
|---|---|
| Integracje typu **Serwis** w `con_integration` | **40** (38 istniejących reakcji biznesowych + 2 nowe pull endpointy) |
| Integracje typu **Klient** w `con_integration` | **0** — nie używamy |
| Helper `tos_webhook_emit` | Niepotrzebny |
| Wpisy w `con_connection` (URL OIP) | Niepotrzebne — TOS nic nie wie o adresie OIP |
| Modyfikacja istniejących 92 wywołań `tos_log_event` | Zero — używamy ich tak jak są |
| Coupling TOS → OIP | Brak |
| Latency end-to-end (event → EDI sent) | 30–60s (interval polling + budowa EDI) — w pełni akceptowalne dla EDI rail (APERAK SLA 5 min, COPRAR czeka godziny) |

### 14.2. Schemat tabel Pinquark dla integracji

> **Uwaga:** schemat poniżej pokazuje **pełny** model Pinquark dla integracji, włącznie z `kind='CLIENT'` i `con_connection`. **W naszym scenariuszu używamy WYŁĄCZNIE kolumn potrzebnych dla `kind='SERVICE'`** (sekcja 14.1.1, sekcja 14.6) — kolumny związane z `kind='CLIENT'` (`app_reaction_id_generated`, `con_connection_id`, cała tabela `con_connection`) zostawione są dla informacji, ale **nie wypełniamy** ich. Skrypt setupowy z 14.5 generuje wyłącznie wpisy `kind='SERVICE'`.

```text
   ┌────────────────────────┐
   │ con_lib_integration_   │  słownik typów: 'OWN' (Własna), 'ALLEGRO', 'BASELINKER'...
   │ type                   │  (TOS używa wyłącznie 'OWN')
   └─────────┬──────────────┘
             │
   ┌─────────▼──────────────┐
   │ con_integration        │  jedna integracja = jeden endpoint (Serwis) lub jeden konsument (Klient)
   │ ─────────────────      │
   │ id                     │  PK
   │ name                   │  identyfikator URL: POST /integration/{name} albo /<name>
   │ con_lib_integration_   │  → 'OWN' (Własna)
   │   type_id              │
   │ con_lib_integration_   │  → 1 = aktywna, 2 = usunięta
   │   status_id            │
   │ kind                   │  'SERVICE' (Serwis: TOS przyjmuje) lub 'CLIENT' (Klient: TOS wywołuje)
   │ wms_warehouse_id       │  magazyn (FK na wms_warehouse)
   │ wms_owner_id           │  właściciel (FK na wms_company)
   │ app_reaction_id        │  → reakcja uruchamiana przy wywołaniu (Serwis) /
   │                        │    przy odbiorze odpowiedzi (Klient)
   │ app_reaction_id_       │  → reakcja autogenerowana „wywołaj tę integrację Klient"
   │   generated            │    (tylko dla kind='CLIENT')
   │ con_connection_id      │  → konfiguracja HTTP (URL, auth) — tylko dla kind='CLIENT'
   │ data jsonb             │  parametry wejścia/wyjścia (mapowanie pól → JSON keys)
   │ limit_per_minute       │  rate-limiting per integracja
   └─────────┬──────────────┘
             │
   ┌─────────▼──────────────┐    ┌────────────────────────┐
   │ con_integration_token  │────│ con_token              │
   │ ─────────────────      │    │ ─────────────────      │
   │ con_integration_id     │    │ id                     │
   │ con_token_id           │    │ token (plaintext)      │
   └────────────────────────┘    │ token_hash (SHA256)    │
                                 │ status (1=aktywny)     │
                                 └────────────────────────┘

   ┌────────────────────────┐
   │ con_connection         │  HTTP config dla kind='CLIENT' (TOS wywołuje OIP)
   │ ─────────────────      │
   │ url                    │  np. https://oip.pinquark.io/webhooks/tos
   │ http_method            │  POST/GET/PUT/PATCH/DELETE
   │ authorization_type     │  NO_AUTH/BASIC/DIGEST/BEARER
   │ token / login/password │  credentialki dla OIP
   │ url_authorization      │  endpoint OAuth (jeśli używany)
   │ api_version            │  
   └────────────────────────┘

   ┌────────────────────────┐
   │ con_integration_       │  log wywołań — używaj jako audit trail
   │ history                │
   │ ─────────────────      │
   │ con_integration_id     │
   │ con_integration_       │  który token użył
   │   token_id             │
   │ time, ip, adm_user_id  │
   └────────────────────────┘
```

### 14.3. URL endpointów Pinquark — co dokładnie wystawiać w `pinquark-tos`

Z pkt 6 dokumentacji `dokumentacja_techniczna_api.md`: **po utworzeniu integracji typu Serwis Pinquark prezentuje przykład wywołania `curl`** (pole 7 i 8 formularza). Fizyczny pattern URL zależy od deployu Pinquark TOS — w środowisku Clip Małaszewicze trzeba potwierdzić u admina (Mateusz: pytanie pkt **11.6** poniżej). Najczęściej spotykane warianty:

```
POST https://<host>:<port>/integration/<integration_name>
POST https://<host>:<port>/<integration_name>
POST https://<host>:<port>/api/integration/<integration_name>
```

**Przyjmij domyślnie pierwszy wariant** (`/integration/{name}`), parametryzuj przez `account.config.path_prefix` w konfiguracji konektora `pinquark-tos`:

```yaml
# integrators/wms/pinquark-tos/v1.0.0/connector.yaml
account_template:
  - key: base_url
    type: string
    required: true
    description: "Bazowy URL Pinquark TOS, np. https://clip-malaszewicze.pinquark.app"
  - key: path_prefix
    type: string
    required: false
    default: "/integration"
    description: "Prefix ścieżki integracji własnych (zwykle /integration)"
  - key: bearer_token
    type: secret
    required: true
    description: "JWT bearer dla autoryzacji REST"
  - key: mer_token
    type: secret
    required: true
    description: "Token z tabeli con_token (nagłówek token-mer)"
  - key: warehouse_code
    type: string
    required: true
    description: "Kod magazynu Pinquark (np. CLIP_MALASZEWICZE)"
```

Każda akcja konektora `pinquark-tos` mapuje się 1:1 na nazwę integracji w bazie TOS:

```yaml
actions:
  - id: notification.rail.save
    display_name: "Zapisz awizację kolejową (AWK Rail)"
    method: POST
    path: "{path_prefix}/tos_notification_rail_save"
    auth:
      headers:
        Authorization: "Bearer {bearer_token}"
        token-mer: "{mer_token}"
    input_schema: ...
    output_schema: ...
```

### 14.4. Co MUSISZ udokumentować w `pinquark-tos/README.md`

Konektor jest bezużyteczny, jeśli admin TOS nie utworzy odpowiednich wpisów w `con_integration`. Dlatego README konektora **MUSI zawierać sekcję „Wymagana konfiguracja po stronie Pinquark TOS"** ze wskazaniem:

1. **Co użytkownik musi zrobić w TOS przed włączeniem konektora:**
   - administracyjnie utworzyć ~40 integracji typu Serwis (po jednej na każdą reakcję),
   - utworzyć **jeden** token typu BEARER w `con_token`,
   - powiązać token ze WSZYSTKIMI integracjami w `con_integration_token`.
2. **Skrypt SQL do jednorazowego wykonania** — gotowy szablon (sekcja 14.5).
3. **Instrukcję pobrania tokena** — token plaintext jest widoczny tylko raz, w UI Pinquark, w momencie tworzenia.
4. **Test połączenia** — przykład `curl` weryfikujący poprawność konfiguracji.

### 14.4a. Pełna lista integracji TOS ↔ OIP do utworzenia

Ta sekcja zawiera **wyczerpujący wykaz** 40 integracji typu Serwis, które trzeba zarejestrować w `con_integration` po stronie TOS. **Zero integracji typu Klient** — outbound EDI realizowany jest przez polling `tos_audit_log` (sekcja 14.6).

Lista jest podzielona logicznie wg domeny biznesowej. Każda integracja ma:
- **Nazwę** (= `con_integration.name` = ostatni segment URL),
- **Reakcję TOS** (= `app_reaction.proc_name` = procedurę PL/pgSQL, którą uruchamia),
- **Powiązanie z EDI** (komunikat EDIFACT, który wyzwala / generuje wywołanie),
- **Workflow OIP**, w którym jest używana,
- **Krytyczność** dla pilotażu z Metrans/HHLA (M0 = MVP, M1 = po MVP, M2 = backlog).

> Konwencja: **`con_integration.name` = `app_reaction.proc_name`**. Trzymamy 1:1 — pozwala to dodawać nowe endpointy bez zmian w aplikacji Pinquark, a w `connector.yaml` po stronie OIP `action.path` mapuje się prosto na `{path_prefix}/{proc_name}`.

#### A) Integracje typu **Serwis** (OIP → TOS, **40 endpointów**)

> Wszystkie z `kind = 'SERVICE'`, jeden wspólny `con_token`, auth `Authorization: Bearer <jwt>` + `token-mer: <token>`.

##### A1. Awizacje kolejowe (AWK Rail) — wyzwalane przez COPRAR/COPARN

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 1 | `tos_notification_rail_save` | `tos_notification_rail_save` (1017) | COPRAR (preadvice) | `inbound-coprar-to-awk` | **M0** |
| 2 | `tos_notification_rail_approve` | `tos_notification_rail_approve` (1018) | brak — autoaprobata po pełnym imporcie | `inbound-coprar-to-awk` (krok końcowy) | **M0** |
| 3 | `tos_notification_rail_cancel` | `tos_notification_rail_cancel` (1019) | COPRAR funct_code=`1` (cancel) | `inbound-coprar-cancel` | M1 |
| 4 | `tos_notification_rail_copy` | `tos_notification_rail_copy` (1020) | — (wewnętrzne, dla COPARN replace) | `inbound-coparn-replace` | M1 |
| 5 | `tos_notification_rail_create_outbound` | `tos_notification_rail_create_outbound` (1021) | COPRAR dla pociągu wyjazdowego | `inbound-coprar-outbound` | M1 |

##### A2. Awizacje drogowe (AWK Road / AVD) — wyzwalane przez IFTMIN/COPARN

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 6 | `tos_notification_road_save` | `tos_notification_road_save` (1022) | IFTMIN (booking message) | `inbound-iftmin-to-avd` | **M0** |
| 7 | `tos_notification_road_approve` | `tos_notification_road_approve` (1023) | brak — autoaprobata | `inbound-iftmin-to-avd` (krok końcowy) | **M0** |
| 8 | `tos_notification_road_cancel` | `tos_notification_road_cancel` (1024) | IFTMIN funct_code=`1` (cancel) | `inbound-iftmin-cancel` | M1 |
| 9 | `tos_notification_road_copy` | `tos_notification_road_copy` (1025) | — (wewnętrzne) | manual / API | M2 |

##### A3. Wagony i kontenery na pociągu — pętle w workflow COPRAR

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 10 | `tos_train_wagon_add` | `tos_train_wagon_add` (1026) | COPRAR — sekcja EQD wagon | `inbound-coprar-to-awk` (foreach wagons) | **M0** |
| 11 | `tos_train_container_add` | `tos_train_container_add` (1028) | COPRAR/COPARN — sekcja EQD container | `inbound-coprar-to-awk` (foreach containers) | **M0** |
| 12 | `tos_logistic_unit_save` | `tos_logistic_unit_save` (1011) | COPRAR/IFTMIN — slot dla nowego kontenera w bazie JL | wszystkie inbound | **M0** |

##### A4. Zlecenia transportowe (ZT/KZT) — wyzwalane przez wewnętrzne workflow + COHAOR

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 13 | `tos_zt_rail_save` | `tos_zt_rail_save` (1033) | COHAOR (handling order) | `inbound-cohaor-to-kzt` | M1 |
| 14 | `tos_zt_change_status` | `tos_zt_change_status` (1034) | — (wewnętrzny status push z OIP) | `oip-status-sync` | M1 |
| 15 | `tos_zt_set_entry_time` | `tos_zt_set_entry_time` (1035) | — (zewnętrzny system bram, jeśli nie używamy `gate_road_entry_confirm`) | opcjonalny | M2 |
| 16 | `tos_zt_set_exit_time` | `tos_zt_set_exit_time` (1036) | — analogicznie | opcjonalny | M2 |

##### A5. Brama drogowa — wyzwalana przez COHAOR (zatwierdzenia awizacji) i wewnętrzne korekty OIP

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 17 | `tos_gate_road_entry_confirm` | `tos_gate_road_entry_confirm` (1044) | COHAOR — auth wjazdu | `inbound-cohaor-gate-auth` | M1 |
| 18 | `tos_gate_road_entry_reject` | `tos_gate_road_entry_reject` (1045) | COHAOR funct=`reject` | `inbound-cohaor-gate-auth` (gałąź NEG) | M1 |
| 19 | `tos_gate_road_exit_confirm` | `tos_gate_road_exit_confirm` (1046) **— ⚠️ DO DOROBIENIA** (reakcja istnieje, procedury brak) | COHAOR — auth wyjazdu (rzadko, zwykle TOS sam decyduje) | manual / opcjonalny | M2 |
| 20 | `tos_gate_ocr_override` | `tos_gate_ocr_override` (1047) | — (manualne korekty z dashboardu OIP) | dashboard OIP | M2 |
| 21 | `tos_gate_assign_track` | `tos_gate_assign_track` (1048) | COHAOR (przypisanie toru po wjeździe TIR-a) | `inbound-cohaor-track-assign` | M1 |

##### A6. Brama kolejowa — wyzwalana z workflow OIP po przyjęciu pociągu

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 22 | `tos_gate_rail_entry_confirm` | `tos_gate_rail_entry_confirm` (1041) | brak (wewnętrzne, ale potwierdza przyjęcie po imporcie COPRAR) | `inbound-coprar-to-awk` (post-import) | M1 |
| 23 | `tos_gate_rail_entry_reject` | `tos_gate_rail_entry_reject` (1042) | — (manualnie) | dashboard OIP | M2 |
| 24 | `tos_gate_rail_exit_confirm` | `tos_gate_rail_exit_confirm` (1043) | — (zwykle TOS sam, ale OIP musi mieć możliwość forsowania) | manual | M2 |

##### A7. Operacje suwnic (CODECO/COARRI source) — bardzo rzadkie inbound, ale możliwe

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 25 | `tos_operation_start` | `tos_operation_start` (1052) | brak (zwykle kierowca suwnicy) | dashboard OIP fallback | M2 |
| 26 | `tos_operation_complete` | `tos_operation_complete` (1053) | brak (zwykle kierowca suwnicy) | dashboard OIP fallback | M2 |

> Operacje są **głównie outbound** — TOS sam je wykonuje i loguje do `tos_audit_log` (event `PRZELAD_ZAKONCZONY`), skąd OIP poluje (sekcja 14.6). Endpointy 25/26 zostawiamy dla scenariuszy „OIP wymusza zamknięcie operacji" (np. po timeoucie partnera EDI).

##### A8. Przesunięcia kontenerów — workflow z COHAOR (handling order = przeniesienie z toru na plac)

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 27 | `tos_movement_save` | `tos_movement_save` (1049) | COHAOR (zlecenie przesunięcia) | `inbound-cohaor-movement` | M1 |
| 28 | `tos_movement_execute` | `tos_movement_execute` (1050) | — (po przyjęciu zlecenia) | `inbound-cohaor-movement` | M1 |
| 29 | `tos_movement_complete` | `tos_movement_complete` (1051) | — (post-execution callback z OIP) | `inbound-cohaor-movement` | M1 |

##### A9. Uszkodzenia i zdjęcia — wyzwalane gdy partner przekazuje raport zewnętrzny

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 30 | `tos_damage_report_save` | `tos_damage_report_save` (1037) | DESADV / IFTMCS (rzadko EDIFACT) lub niestandardowy XML/JSON partnera | `inbound-damage-report` | M2 |
| 31 | `tos_photo_save` | `tos_photo_save` (1039) | załącznik MIME w wiadomości partnera | `inbound-damage-report` | M2 |

##### A10. Dokumenty — załączniki PDF/XML

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 32 | `tos_doc_file_add` | `tos_doc_file_add` (1030) | załącznik UNB+UNH (rzadko) lub email | `inbound-attachment` | M2 |
| 33 | `tos_doc_set_status` | `tos_doc_set_status` (1032) | — (manualne forsowanie statusu z OIP po ACK) | `oip-status-sync` | M1 |

##### A11. Walidacja (synchroniczna) — pre-checki dla flow OIP

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 34 | `tos_validate_vehicle_number` | `tos_validate_vehicle_number` (1059) | przed `tos_notification_road_save` | `inbound-iftmin-to-avd` (pre-check) | M1 |
| 35 | `tos_validate_container_code` | `tos_validate_container_code` (1060) | walidacja ISO 6346 dla COPRAR/IFTMIN | każde inbound (pre-check) | M1 |
| 36 | `tos_validate_slot_availability` | `tos_validate_slot_availability` (1061) | sprawdzenie wolnego slotu przed AWK | `inbound-coprar/iftmin` | M1 |

##### A12. Status pull dla zapytań zewnętrznych (IFTSTA request) — read-only snapshot per dokument/kontener

| # | `con_integration.name` | Reakcja TOS | EDI źródło | Workflow OIP | M |
|---|---|---|---|---|---|
| 37 | `tos_doc_get_status` ⚠️ **NEW** | `tos_doc_get_status` *(do dorobienia)* | IFTSTA request od partnera | `inbound-iftsta-pull` | M1 |
| 38 | `tos_container_get_status` ⚠️ **NEW** | `tos_container_get_status` *(do dorobienia)* | IFTSTA request od partnera | `inbound-iftsta-pull` | M1 |

> Endpointy 37–38 wymagają **dorobienia procedur PL/pgSQL po stronie TOS**. Procedury mają zwracać aktualny status dokumentu/kontenera w formacie zgodnym z IFTSTA payload.

##### A13. Outbound polling (OIP polluje TOS dla generowania CODECO/COARRI/APERAK/IFTSTA) — fundament pull patternu

| # | `con_integration.name` | Reakcja TOS | Co zwraca | Workflow OIP | M |
|---|---|---|---|---|---|
| 39 | `tos_get_events_since` ⚠️ **NEW** | `tos_get_events_since` *(do dorobienia)* | nowe wpisy z `tos_audit_log` (od kursora `last_audit_id`) z polami: `id`, `created_at`, `module`, `event_type`, `doc_id`, `doc_symbol`, `details JSONB` | `tos-poll-events` (scheduled co 30s) — główny mechanizm outbound | **M0** |
| 40 | `tos_get_doc_status_changes_since` ⚠️ **NEW** | `tos_get_doc_status_changes_since` *(do dorobienia)* | nowe wpisy z `wms_doc_status_history` (od kursora `last_history_id`) z polami: `id`, `wms_doc_id`, `wms_lib_status_doc_id`, `time`, `status_symbol`, `status_name`, `adm_user_id` | `tos-poll-events` (jako uzupełnienie / sanity-check) | **M0** |

> Endpointy 39–40 są **fundamentem outbound EDI**. Bez nich OIP nie wie kiedy generować CODECO/COARRI/APERAK/IFTSTA. Pełna implementacja procedur + przykładowy workflow polling — sekcja **14.6**.

---

#### Podsumowanie ilościowe

| Kategoria | Liczba integracji | M0 (MVP pilot Metrans) | M1 (po MVP) | M2 (backlog) |
|---|---:|---:|---:|---:|
| Serwis biznesowe (TOS przyjmuje, modyfikuje stan) | **38** | 6 | 19 | 13 |
| Serwis read-only (TOS odpowiada na pytania OIP) | **2** *(A13)* | 2 | 0 | 0 |
| Serwis snapshot (IFTSTA pull od partnera) | **2** *(A12)* | 0 | 2 | 0 |
| Klient (TOS wysyła) | **0** | 0 | 0 | 0 |
| **RAZEM** | **40** | **8** | **21** | **13** |

**Wszystkie integracje są typu Serwis** — TOS jest wyłącznie serwerem REST. OIP zawsze inicjuje komunikację, w tym outbound EDI realizowany przez polling endpointów A13 (`tos_get_events_since`).

**Pilot MVP (M0)** — wystarczy 8 integracji + 4 workflow OIP, żeby uruchomić pełny cykl preadvice → przyjazd pociągu → discharge → gate-out tira z Metransem.

#### Mapowanie M0 na 4 workflow OIP (priorytet wdrożeniowy)

| Workflow OIP | Typ | Endpointy TOS użyte | Generuje EDI |
|---|---|---|---|
| `inbound-coprar-to-awk` (Metrans COPRAR → AWK Rail) | inbound | A1.1, A1.2, A3.10, A3.11, A3.12 | — (przyjmuje COPRAR) |
| `inbound-iftmin-to-avd` (HHLA IFTMIN → AVD) | inbound | A2.6, A2.7, A3.12 | — (przyjmuje IFTMIN) |
| `tos-poll-events` (scheduled co 30s, główny event hub outbound) | outbound | **A13.39, A13.40** + opcjonalnie A12.37 dla pełnego snapshotu | APERAK, IFTSTA, CODECO, COARRI (routing wg `event_type` w workflow) |
| `inbound-iftsta-pull` (partner pyta o status) | request/reply | A12.37, A12.38 | IFTSTA response |

#### Co z tej listy musi dorobić Mateusz (po stronie TOS)

**Tylko 4 nowe procedury** — zero modyfikacji już działających:

| # | Brakująca procedura PL/pgSQL | Po co | Plik docelowy | M |
|---|---|---|---|---|
| 1 | `tos_get_events_since(p_data json) RETURNS json` | **Krytyczne** — fundament outbound EDI (A13.39) | `tos_procedures.sql` (NEW) | **M0** |
| 2 | `tos_get_doc_status_changes_since(p_data json) RETURNS json` | Uzupełnienie polling — zmiany statusów (A13.40) | `tos_procedures.sql` (NEW) | **M0** |
| 3 | `tos_doc_get_status(p_data json) RETURNS json` | IFTSTA pull request od partnera (A12.37) | `tos_procedures.sql` (NEW) | M1 |
| 4 | `tos_container_get_status(p_data json) RETURNS json` | IFTSTA pull request od partnera (A12.38) | `tos_procedures.sql` (NEW) | M1 |
| 5 | `tos_gate_road_exit_confirm(p_data json) RETURNS json` | **Bug fix** — reakcja `1046` jest, procedury brak (A5.19) | `tos_procedures.sql` (NEW) | M2 |
| 6 | INSERT-y reakcji do `tos_reactions.sql` dla #1–#5 | Rejestracja procedur jako reakcji | `tos_reactions.sql` | jw |
| 7 | (opcjonalnie) `tos_train_container_add_bulk(p_data json)` | Optymalizacja batch dla COPRAR z 3000+ kontenerów | `tos_procedures.sql` (NEW) | M1+ |

**Czego NIE trzeba robić** (świadome decyzje wynikające z pull patternu):
- ❌ helpera `tos_webhook_emit` — niepotrzebny, OIP poluje
- ❌ modyfikacji 92 wywołań `tos_log_event` — używamy ich tak jak są
- ❌ wpięcia `PERFORM` w 9 procedurach biznesowych (`tos_change_doc_status`, `tos_gate_*_confirm`, `tos_operation_complete` itd.)
- ❌ tabeli `tos_edi_message_log` — `tos_audit_log` w pełni wystarcza jako audit trail
- ❌ `con_connection` z URL OIP — TOS nic nie wie o adresie OIP
- ❌ rozszerzenia `pg_net` ani `plperlu` w PostgreSQL TOS

---

### 14.5. Gotowy generator SQL — załącznik do sekcji 12

**Ten skrypt MUSISZ umieścić w README konektora `pinquark-tos`** (i ewentualnie jako osobny plik `integrators/wms/pinquark-tos/v1.0.0/sql/setup_tos_integrations.sql`). Mateusz uruchomi go po stronie TOS — Ty go nie wykonujesz, ale dostarczasz jako artefakt razem z konektorem.

```sql
-- ========================================================================
--  SETUP_TOS_INTEGRATIONS.sql
--  Tworzy integracje „własne" Pinquark dla połączenia z OIP EDI Gateway
--  Uruchom po wdrożeniu reakcji TOS (tos_reactions.sql) JEDEN RAZ na środowisko
-- ========================================================================

DO $$
DECLARE
    v_type_own_id           INT;
    v_status_active_id      INT;
    v_warehouse_id          INT;
    v_owner_id              INT;
    v_token_plain           TEXT;
    v_token_id              INT;
    v_integration_id        INT;
    v_reaction_id           INT;
    v_reaction_proc         TEXT;

    -- Lista WSZYSTKICH reakcji TOS, które OIP będzie wywoływać.
    -- Synchronizuj z `actions:` w connector.yaml konektora pinquark-tos.
    -- Format: nazwa_reakcji (= proc_name w app_reaction = identyfikator URL integracji)
    -- Pełna lista 40 reakcji TOS (36 istniejących biznesowych A1-A11
    --                              + 2 IFTSTA pull A12 [DO DOROBIENIA]
    --                              + 2 outbound polling A13 [DO DOROBIENIA — KRYTYCZNE M0])
    -- Konwencja: con_integration.name = app_reaction.proc_name
    v_reactions TEXT[] := ARRAY[
        -- A1. AWK Rail (5)
        'tos_notification_rail_save',
        'tos_notification_rail_approve',
        'tos_notification_rail_cancel',
        'tos_notification_rail_copy',
        'tos_notification_rail_create_outbound',
        -- A2. AWK Road / AVD (4)
        'tos_notification_road_save',
        'tos_notification_road_approve',
        'tos_notification_road_cancel',
        'tos_notification_road_copy',
        -- A3. Wagony i kontenery (3)
        'tos_train_wagon_add',
        'tos_train_container_add',
        'tos_logistic_unit_save',
        -- A4. ZT/KZT (4)
        'tos_zt_rail_save',
        'tos_zt_change_status',
        'tos_zt_set_entry_time',
        'tos_zt_set_exit_time',
        -- A5. Brama drogowa (5)
        'tos_gate_road_entry_confirm',
        'tos_gate_road_entry_reject',
        'tos_gate_road_exit_confirm',
        'tos_gate_ocr_override',
        'tos_gate_assign_track',
        -- A6. Brama kolejowa (3)
        'tos_gate_rail_entry_confirm',
        'tos_gate_rail_entry_reject',
        'tos_gate_rail_exit_confirm',
        -- A7. Operacje suwnic (2)
        'tos_operation_start',
        'tos_operation_complete',
        -- A8. Przesunięcia (3)
        'tos_movement_save',
        'tos_movement_execute',
        'tos_movement_complete',
        -- A9. Uszkodzenia i zdjęcia (2)
        'tos_damage_report_save',
        'tos_photo_save',
        -- A10. Dokumenty (2)
        'tos_doc_file_add',
        'tos_doc_set_status',
        -- A11. Walidacja synchroniczna (3)
        'tos_validate_vehicle_number',
        'tos_validate_container_code',
        'tos_validate_slot_availability',
        -- A12. Status pull dla IFTSTA (2 — DO DOROBIENIA po stronie TOS)
        'tos_doc_get_status',                   -- TODO: dorobić procedurę PL/pgSQL
        'tos_container_get_status',             -- TODO: dorobić procedurę PL/pgSQL
        -- A13. OUTBOUND POLLING — fundament outbound EDI (2 — DO DOROBIENIA, KRYTYCZNE M0)
        'tos_get_events_since',                 -- TODO: dorobić procedurę PL/pgSQL — przykład w sekcji 14.6
        'tos_get_doc_status_changes_since'      -- TODO: dorobić procedurę PL/pgSQL — przykład w sekcji 14.6
    ];
BEGIN
    -- 1) Pobierz słownikowe ID
    SELECT id INTO v_type_own_id
        FROM con_lib_integration_type
        WHERE symbol = 'OWN'
        LIMIT 1;

    SELECT id INTO v_status_active_id
        FROM con_lib_integration_status
        WHERE name ILIKE 'active%' OR name ILIKE 'aktywn%'
        LIMIT 1;

    -- 2) Pobierz magazyn i ownera (DOSTOSUJ do swojego środowiska)
    SELECT id INTO v_warehouse_id
        FROM wms_warehouse
        WHERE symbol = 'CLIP_MALASZEWICZE'  -- ← edytuj
        LIMIT 1;

    SELECT id INTO v_owner_id
        FROM wms_company
        WHERE symbol = 'CLIP'  -- ← edytuj
        LIMIT 1;

    IF v_type_own_id IS NULL OR v_status_active_id IS NULL OR v_warehouse_id IS NULL THEN
        RAISE EXCEPTION 'Brak wymaganych słowników: type_own=%, status_active=%, warehouse=%',
            v_type_own_id, v_status_active_id, v_warehouse_id;
    END IF;

    -- 3) Wygeneruj jeden wspólny token Bearer dla całego OIP
    --    (W produkcji rozważ osobny token per środowisko OIP, np. dev/prod)
    v_token_plain := encode(gen_random_bytes(32), 'hex');

    INSERT INTO con_token (token, token_hash, status, time_add)
    VALUES (
        v_token_plain,
        encode(digest(v_token_plain, 'sha256'), 'hex'),
        1,
        now()
    )
    RETURNING id INTO v_token_id;

    -- ZACHOWAJ TEN TOKEN — wpisz go do account.mer_token konektora pinquark-tos w OIP
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  TOKEN PINQUARK TOS DLA OIP EDI GATEWAY (con_token.id=%):     ', v_token_id;
    RAISE NOTICE '  %                                                            ', v_token_plain;
    RAISE NOTICE '  ZAPISZ TERAZ — nie pojawi się ponownie!                      ';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';

    -- 4) Dla każdej reakcji TOS utwórz integrację Serwis + powiąż z tokenem
    FOREACH v_reaction_proc IN ARRAY v_reactions
    LOOP
        -- znajdź reakcję
        SELECT id INTO v_reaction_id
            FROM app_reaction
            WHERE proc_name = v_reaction_proc
              AND active = true
            LIMIT 1;

        IF v_reaction_id IS NULL THEN
            RAISE WARNING 'Reakcja % nie istnieje w app_reaction — pomijam', v_reaction_proc;
            CONTINUE;
        END IF;

        -- czy integracja już istnieje (idempotentność)
        SELECT id INTO v_integration_id
            FROM con_integration
            WHERE name = v_reaction_proc
              AND status <> 2
            LIMIT 1;

        IF v_integration_id IS NOT NULL THEN
            RAISE NOTICE 'Integracja % już istnieje (id=%) — aktualizuję', v_reaction_proc, v_integration_id;
            UPDATE con_integration
               SET app_reaction_id = v_reaction_id,
                   con_lib_integration_status_id = v_status_active_id,
                   wms_warehouse_id = v_warehouse_id,
                   wms_owner_id = v_owner_id,
                   kind = 'SERVICE',
                   limit_per_minute = 600  -- 10 RPS — dostosuj do potrzeb
             WHERE id = v_integration_id;
        ELSE
            INSERT INTO con_integration (
                con_lib_integration_type_id,
                name,
                con_lib_integration_status_id,
                time_add,
                wms_owner_id,
                wms_warehouse_id,
                app_reaction_id,
                kind,
                status,
                limit_per_minute,
                data
            ) VALUES (
                v_type_own_id,
                v_reaction_proc,
                v_status_active_id,
                now(),
                v_owner_id,
                v_warehouse_id,
                v_reaction_id,
                'SERVICE',
                1,
                600,
                jsonb_build_object(
                    'description',  'Auto-generated for OIP EDI Gateway',
                    'http_method',  'POST',
                    'content_type', 'application/json',
                    'created_by',   'setup_tos_integrations.sql'
                )
            )
            RETURNING id INTO v_integration_id;
            RAISE NOTICE 'Utworzono integrację Serwis: % (id=%, reaction_id=%)',
                v_reaction_proc, v_integration_id, v_reaction_id;
        END IF;

        -- powiązanie token ↔ integracja (idempotentne)
        IF NOT EXISTS (
            SELECT 1 FROM con_integration_token
            WHERE con_integration_id = v_integration_id
              AND con_token_id = v_token_id
        ) THEN
            INSERT INTO con_integration_token (con_integration_id, con_token_id)
            VALUES (v_integration_id, v_token_id);
        END IF;
    END LOOP;

    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE 'Setup zakończony. Liczba reakcji w mapie: %', array_length(v_reactions, 1);
    RAISE NOTICE 'Token plaintext: % (con_token.id=%)', v_token_plain, v_token_id;
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;
```

### 14.6. Kierunek odwrotny (outbound EDI) — **Pull pattern: OIP poluje `tos_audit_log`**

> **Ta sekcja zastępuje wcześniejszą koncepcję integracji typu Klient i webhooków `tos_webhook_emit`.** Po analizie kodu TOS (92 wywołań `tos_log_event` w istniejących procedurach + tabela `tos_audit_log` z indeksami) okazało się, że TOS ma **gotowy outbox** — wystarczy go wystawić jako endpoint REST i niech OIP go poluje. To radykalnie upraszcza implementację po stronie TOS (zero modyfikacji procedur biznesowych) i spełnia wymagania latency dla EDI rail (30–60s end-to-end, podczas gdy SLA APERAK = 5 min, COPRAR/COARRI = godziny).

#### 14.6.1. Architektura pull patternu

```
┌─────────────────────────┐                     ┌─────────────────────────┐
│      TOS (Pinquark)     │                     │   OIP (EDI Gateway)     │
│                         │                     │                         │
│  92 procedur biznesowych│                     │  workflow tos-poll-events
│  ├ tos_gate_*_confirm   │                     │  ├ scheduler co 30s     │
│  ├ tos_operation_*      │  PERFORM           │  │                       │
│  ├ tos_movement_*       │  tos_log_event(...) │  │  POST /tos_get_events_since
│  ├ tos_notification_*   │  ┌──────────────┐   │  │  Body: {"last_audit_id": 12345, "limit": 1000}
│  └ tos_*_save           │  │ INSERT INTO  │   │  │  Header: token-mer: <bearer>
│                         │  │ tos_audit_log│   │  │                       │
│         (BEZ ZMIAN)     │  └──────┬───────┘   │  ▼                       │
│                         │         │           │  HTTP 200                 │
│                         │         ▼           │  {"status":"OK",          │
│                         │  ┌──────────────┐   │   "events":[...],        │
│                         │  │tos_audit_log │◄──┤   "max_id": 12378,       │
│                         │  │  (indexed)   │   │   "count": 33}           │
│                         │  └──────────────┘   │                          │
│                         │                     │  pętla po events:        │
│                         │                     │  ├ awizacja zatw. → APERAK│
│                         │                     │  ├ przeładunek → COARRI  │
│                         │                     │  ├ wjazd/wyjazd → CODECO │
│                         │                     │  ├ status zmiana → IFTSTA│
│                         │                     │  └ uszkodzenie → IFTSTA  │
│                         │                     │                          │
│                         │                     │  emit do partnerów EDI   │
│                         │                     │  (SFTP/AS2/email)        │
│                         │                     │                          │
│                         │                     │  zapisz max_id → kursor  │
│                         │                     │  w state OIP             │
└─────────────────────────┘                     └─────────────────────────┘
```

**Dlaczego pull, a nie push (webhook):**

| Aspekt | Push (Klient + webhook) | **Pull (rekomendowany)** |
|---|---|---|
| Modyfikacje istniejących procedur TOS | 14 wpięć w 9 procedurach (tos_change_doc_status, tos_gate_*, tos_operation_complete itd.) — ryzyko regresji | **0** — używamy istniejących wywołań `tos_log_event` |
| Nowe obiekty SQL po stronie TOS | helper `tos_webhook_emit`, 14 integracji `kind='CLIENT'`, 14 `con_connection`, helper `tos_call_integration` | 4 procedury read-only (events, status_history, doc_status, container_status) |
| Sprzężenie TOS → OIP | TOS musi znać URL OIP, token OIP, retry, kolejka | TOS nic nie wie o OIP |
| Co przy padzie OIP | TOS musi buforować (bo retry nie zawsze działa), ryzyko zgubionych eventów | OIP po restarcie czyta od ostatniego kursora — **gwarancja at-least-once** za darmo |
| Co przy padzie TOS | OIP musi wykryć timeouty webhooków | OIP normalnie poluje, dostaje błąd, retry; po wstaniu TOS — wszystko ciągnie się od kursora |
| Latency | ~1 s | 30–60 s (akceptowalne dla EDI rail) |
| Audit trail outbound | nowa tabela `tos_edi_message_log` | **`tos_audit_log` + log workflow OIP** w jednym miejscu |
| Złożoność OIP workflow | 14 osobnych endpointów `/webhooks/tos/<event>`, każdy z własnym mapowaniem | 1 workflow `tos-poll-events` z routingiem po `event_type` |

#### 14.6.2. Procedura `tos_get_events_since` — gotowa do wdrożenia

To **jedyny** krytyczny nowy obiekt SQL po stronie TOS dla outbound EDI. Mateusz dorzuca go do `tos_procedures.sql`, rejestruje w `tos_reactions.sql`, skrypt z 14.5 podpina go jako integrację Serwis. Po tym OIP może już generować APERAK/CODECO/COARRI/IFTSTA.

```sql
-- ========================================================================
--  tos_get_events_since
--  Read-only endpoint dla OIP — wyciąga nowe wpisy z tos_audit_log
--  od kursora (last_audit_id) z limitem (default 1000, max 5000).
--
--  Wywołanie z OIP:
--    POST /<base>/tos_get_events_since
--    Header: token-mer: <bearer>
--    Body:   {"last_audit_id": 12345, "limit": 1000}
--
--  Odpowiedź:
--    {
--      "status": "OK",
--      "events": [
--        {
--          "id": 12346,
--          "created_at": "2026-04-19T08:01:23.456",
--          "module": "Bramy",
--          "event_type": "WJAZD_TIR_POTWIERDZONY",
--          "doc_id": 78901,
--          "doc_symbol": "ZT-20260419-0042",
--          "user_id": 17,
--          "user_login": "kowalski.j",
--          "details": { ... payload zdarzenia ... }
--        },
--        ...
--      ],
--      "max_id": 12378,
--      "count": 33
--    }
-- ========================================================================
CREATE OR REPLACE FUNCTION public.tos_get_events_since(
    p_data json
) RETURNS json
LANGUAGE plpgsql AS $$
DECLARE
    v_last_id  INT  := COALESCE((p_data->>'last_audit_id')::int, 0);
    v_limit    INT  := LEAST(COALESCE((p_data->>'limit')::int, 1000), 5000);
    v_modules  TEXT := COALESCE(p_data->>'modules', '');  -- opcjonalny filtr CSV
    v_events   jsonb;
    v_max_id   INT;
    v_count    INT;
BEGIN
    WITH src AS (
        SELECT a.*
        FROM public.tos_audit_log a
        WHERE a.id > v_last_id
          AND (v_modules = '' OR a.module = ANY (string_to_array(v_modules, ',')))
        ORDER BY a.id ASC
        LIMIT v_limit
    )
    SELECT
        COALESCE(jsonb_agg(jsonb_build_object(
            'id',          src.id,
            'created_at',  to_char(src.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'module',      src.module,
            'event_type',  src.event_type,
            'doc_id',      src.doc_id,
            'doc_symbol',  src.doc_symbol,
            'user_id',     src.user_id,
            'user_login',  src.user_login,
            'details',     COALESCE(src.details, '{}'::jsonb)
        ) ORDER BY src.id), '[]'::jsonb),
        COALESCE(MAX(src.id), v_last_id),
        COUNT(*)
    INTO v_events, v_max_id, v_count
    FROM src;

    RETURN json_build_object(
        'status',  'OK',
        'events',  v_events,
        'max_id',  v_max_id,
        'count',   v_count
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'status',     'ERROR',
        'error_code', SQLSTATE,
        'message',    SQLERRM
    );
END $$;
COMMENT ON FUNCTION public.tos_get_events_since(json) IS
'Read-only outbound endpoint dla OIP EDI Gateway. Polluje nowe wpisy z tos_audit_log od kursora last_audit_id. Limit 1000 (max 5000). Patrz TOS_INTERMODAL_EDI_SPEC.md sekcja 14.6.';
```

Procedura jest **deterministyczna i bezpieczna**:
- read-only (`SELECT` only) — nie modyfikuje stanu TOS,
- używa istniejącego indeksu `tos_audit_log_created_idx` + PK `id` (zapytanie po `id > X ORDER BY id LIMIT N` jest indeksowe),
- limit `LIMIT 5000` chroni przed przeciążeniem,
- opcjonalny filtr `modules` pozwala uruchomić wiele równoległych pollerów (np. osobno dla bram i osobno dla operacji),
- zwraca `max_id` — OIP zapisuje to jako swój kursor i przy następnym pollu wysyła jako `last_audit_id`.

#### 14.6.3. Procedura `tos_get_doc_status_changes_since` — uzupełnienie

Drugi endpoint pollingu dla wąskiego strumienia tylko zmian statusów dokumentów (z `wms_doc_status_history`). Używany dla generowania IFTSTA — często wystarczy sama zmiana statusu bez dodatkowych szczegółów z `tos_audit_log`.

```sql
CREATE OR REPLACE FUNCTION public.tos_get_doc_status_changes_since(
    p_data json
) RETURNS json
LANGUAGE plpgsql AS $$
DECLARE
    v_last_id  INT := COALESCE((p_data->>'last_history_id')::int, 0);
    v_limit    INT := LEAST(COALESCE((p_data->>'limit')::int, 1000), 5000);
    v_changes  jsonb;
    v_max_id   INT;
BEGIN
    WITH src AS (
        SELECT
            h.id,
            h.wms_doc_id,
            h.wms_lib_status_doc_id,
            h.time,
            ls.symbol AS status_symbol,
            ls.name   AS status_name,
            h.adm_user_id,
            d.symbol  AS doc_symbol,
            ld.symbol AS doc_type_symbol  -- np. AWK, AVD, ZT, PRZ
        FROM public.wms_doc_status_history h
        JOIN public.wms_doc d              ON d.id  = h.wms_doc_id
        JOIN public.wms_lib_status_doc ls  ON ls.id = h.wms_lib_status_doc_id
        JOIN public.wms_lib_doc ld         ON ld.id = d.wms_lib_doc_id
        WHERE h.id > v_last_id
        ORDER BY h.id ASC
        LIMIT v_limit
    )
    SELECT
        COALESCE(jsonb_agg(jsonb_build_object(
            'id',                    src.id,
            'wms_doc_id',            src.wms_doc_id,
            'doc_symbol',            src.doc_symbol,
            'doc_type_symbol',       src.doc_type_symbol,
            'wms_lib_status_doc_id', src.wms_lib_status_doc_id,
            'status_symbol',         src.status_symbol,
            'status_name',           src.status_name,
            'time',                  to_char(src.time AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
            'adm_user_id',           src.adm_user_id
        ) ORDER BY src.id), '[]'::jsonb),
        COALESCE(MAX(src.id), v_last_id)
    INTO v_changes, v_max_id
    FROM src;

    RETURN json_build_object(
        'status',  'OK',
        'changes', v_changes,
        'max_id',  v_max_id,
        'count',   jsonb_array_length(v_changes)
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'status',     'ERROR',
        'error_code', SQLSTATE,
        'message',    SQLERRM
    );
END $$;
```

#### 14.6.4. Workflow OIP `tos-poll-events` — gotowy YAML

> **Workflow partner-agnostyczny.** Subworkflowy (`outbound-codeco-gate-in`, `outbound-aperak-positive`, `outbound-iftsta-*`, ...) są **wspólne dla wszystkich partnerów**. Routing per partner odbywa się **w środku subworkflow** — na podstawie `tos_doc.contractor_id` zaczerpniętego z `tos_doc_get_status` lookupowany jest partner w **partner registry OIP** (sekcja 14.6.6), z którego wynika konkretne `account` SFTP/AS2 + `account` EDIFACT (sender_id, receiver_id, smdg_profile, wersja D.95B/D.00B). Brak osobnych subworkflowów per partner — dodanie 6. partnera EDI nie wymaga modyfikacji tego pliku.

```yaml
# integrators/edi/edifact/v1.0.0/workflows/tos-poll-events.yaml
name: tos-poll-events
description: |
  Główny workflow outbound EDI. Co 30 sekund poluje tos_audit_log,
  routuje eventy do generatorów EDIFACT (APERAK, CODECO, COARRI, IFTSTA).
  Routing per partner następuje DOPIERO w subworkflowach (sekcja 14.6.6 —
  partner registry), nie tutaj.

trigger:
  type: schedule
  cron: "*/30 * * * * *"   # co 30s
  initial_state:
    last_audit_id: 0       # przy pierwszym uruchomieniu — od początku

steps:

  - id: load_cursor
    type: state.load
    output:
      last_audit_id: "{{ state.last_audit_id | default(0) }}"

  - id: poll_tos
    type: connector.action
    connector: pinquark-tos
    action: tos_get_events_since
    input:
      last_audit_id: "{{ steps.load_cursor.output.last_audit_id }}"
      limit: 1000
    timeout_s: 30
    retry:
      max_attempts: 3
      backoff_s: [2, 5, 15]

  - id: short_circuit_if_empty
    type: condition
    if: "{{ steps.poll_tos.output.count == 0 }}"
    then:
      - id: log_idle
        type: log
        level: debug
        message: "No new events (cursor={{ steps.load_cursor.output.last_audit_id }})"
      - id: end_idle
        type: end

  - id: route_events
    type: foreach
    items: "{{ steps.poll_tos.output.events }}"
    parallel: false        # zachowaj kolejność per partner; w razie potrzeby grupuj po partnerze
    body:

      - id: classify
        type: switch
        on: "{{ item.event_type }}"
        cases:

          # APERAK — potwierdzenie przyjęcia preadvice
          # UWAGA: każdy subworkflow jest PARTNER-AGNOSTYCZNY — sam wybiera
          # partnera/partnerów na podstawie inputs.event.doc_id (lookup
          # tos_doc.contractor_id → partner_registry).
          AWK_RAIL_ZATWIERDZONA:
            - { type: workflow.invoke, workflow: 08_aperak_auto_response, input: { event: "{{ item }}", response_type: "accepted" } }
          AWK_RAIL_ANULOWANA:
            - { type: workflow.invoke, workflow: 08_aperak_auto_response, input: { event: "{{ item }}", response_type: "rejected" } }
          AVD_ZATWIERDZONA:
            - { type: workflow.invoke, workflow: 08_aperak_auto_response, input: { event: "{{ item }}", response_type: "accepted" } }

          # CODECO — bramowanie (jeden subworkflow dla in/out, rozróżnienie w środku)
          WJAZD_TIR_POTWIERDZONY:
            - { type: workflow.invoke, workflow: 02_codeco_outbound, input: { event: "{{ item }}", direction: "gate-in" } }
          WYJAZD_TIR_POTWIERDZONY:
            - { type: workflow.invoke, workflow: 02_codeco_outbound, input: { event: "{{ item }}", direction: "gate-out" } }
          WJAZD_TIR_ODRZUCONY:
            - { type: workflow.invoke, workflow: 08_aperak_auto_response, input: { event: "{{ item }}", response_type: "rejected" } }

          # COARRI — operacje suwnic
          PRZELAD_ZAKONCZONY:
            - { type: workflow.invoke, workflow: 03_coarri_outbound, input: { event: "{{ item }}" } }

          # IFTSTA — status pociągu / dokumentu (jeden subworkflow z subtype)
          POCIAG_PRZYJECHAL:
            - { type: workflow.invoke, workflow: 04_iftsta_outbound, input: { event: "{{ item }}", status_code: "ARRIVED" } }
          POCIAG_ODJECHAL:
            - { type: workflow.invoke, workflow: 04_iftsta_outbound, input: { event: "{{ item }}", status_code: "DEPARTED" } }
          USZKODZENIE_ZGLOSZONE:
            - { type: workflow.invoke, workflow: 04_iftsta_outbound, input: { event: "{{ item }}", status_code: "DAMAGED" } }
          STATUS_DOKUMENTU_ZMIENIONY:
            - { type: workflow.invoke, workflow: 04_iftsta_outbound, input: { event: "{{ item }}", status_code: "{{ item.details.new_status_code }}" } }

          # default — log do dashboardu, brak akcji EDI
          default:
            - { type: log, level: trace, message: "Skipping event {{ item.event_type }} (no EDI mapping)" }

  - id: save_cursor
    type: state.save
    input:
      last_audit_id: "{{ steps.poll_tos.output.max_id }}"

  - id: metrics
    type: metrics.emit
    metrics:
      - { name: tos_events_polled_total, value: "{{ steps.poll_tos.output.count }}", type: counter }
      - { name: tos_cursor_position,      value: "{{ steps.poll_tos.output.max_id }}", type: gauge }
```

**Cechy workflow:**
- **Idempotentność** — eventy są routowane do podworkflowów, które same generują wiadomości EDI z deterministycznymi MSG_REF (np. `<doc_symbol>-<audit_id>`); duplikat audit_id zostanie zignorowany przez deduplicator EDI po stronie partnera.
- **Kursor w state** — przy restarcie OIP workflow podejmuje od ostatniego zapisanego `last_audit_id`. **At-least-once delivery** za darmo.
- **Sekwencyjność** — `parallel: false` w foreach zachowuje kolejność wiadomości (CODECO gate-in MUSI być przed CODECO gate-out dla tego samego kontenera).
- **Throttling** — przy włączonym `limit: 1000` i interwale 30s przepustowość = ~33 evt/s, co spokojnie pokrywa pikowe godziny w terminalu (Małaszewicze ~50 ZT/dzień + 8 pociągów × 50 wagonów × 2 kontenery = ~850 evt/dzień).
- **Routing po `event_type`** — wszystkie 92 wywołania `tos_log_event` mają zdefiniowany typ; nieznane typy są ignorowane (log + metryka), a workflow nie pada.
- **Partner-agnostyczność** — workflow nie wie nic o konkretnych partnerach (Metrans, HHLA itd.). Mapowanie `doc_id → contractor_id → partner(s)` odbywa się **w subworkflowach** przez `partner_registry.resolve_by_codes` (sekcja 14.6.6). Dodanie nowego partnera EDI **nie modyfikuje tego pliku** — jedyna zmiana to wpis w partner registry + 1 plik account FTP + 1 plik account EDIFACT.

#### 14.6.5. Pełna lista mapowania `event_type` → komunikat EDIFACT

To **musi być** w README konektora `edifact` jako sekcja "Outbound event mapping". Wartości `event_type` pochodzą z istniejących wywołań `tos_log_event` w `tos_procedures.sql` (możesz je wylistować przez `rg "tos_log_event\(" clip/TOS/tos_procedures.sql -o`).

| `event_type` w `tos_audit_log` | Komunikat EDI generowany | Kierunek | Workflow OIP (generic) | M |
|---|---|---|---|---|
| `AWK_RAIL_ZATWIERDZONA`, `AVD_ZATWIERDZONA` | **APERAK** accepted | OIP → partner | `08_aperak_auto_response` | **M0** |
| `AWK_RAIL_ANULOWANA`, `AVD_ANULOWANA`, `WJAZD_TIR_ODRZUCONY` | **APERAK** rejected (+ opc. **IFTSTA** rejected) | OIP → partner | `08_aperak_auto_response` | M1 |
| `WJAZD_TIR_POTWIERDZONY` | **CODECO** gate-in (+ opc. **IFTSTA** progress) | OIP → partner | `02_codeco_outbound` (`direction=gate-in`) | **M0** |
| `WYJAZD_TIR_POTWIERDZONY` | **CODECO** gate-out (+ opc. **IFTSTA** completed) | OIP → partner | `02_codeco_outbound` (`direction=gate-out`) | **M0** |
| `POCIAG_PRZYJECHAL` | **IFTSTA** ARRIVED (+ opc. **COARRI** batch) | OIP → partner | `04_iftsta_outbound` (`status_code=ARRIVED`) | **M0** |
| `POCIAG_ODJECHAL` | **IFTSTA** DEPARTED | OIP → partner | `04_iftsta_outbound` (`status_code=DEPARTED`) | M1 |
| `PRZELAD_ZAKONCZONY` | **COARRI** load/discharge confirm | OIP → partner | `03_coarri_outbound` | **M0** |
| `PRZESUNIECIE_WYKONANE` | **CODECO** yard-move (opcjonalne — partnerzy z opt-in flagą) | OIP → partner | `02_codeco_outbound` (`direction=yard-move`) | M2 |
| `USZKODZENIE_ZGLOSZONE` | **IFTSTA** DAMAGED | OIP → partner | `04_iftsta_outbound` (`status_code=DAMAGED`) | M2 |
| `STATUS_DOKUMENTU_ZMIENIONY` | **IFTSTA** status update (kod z `details.new_status_code`) | OIP → partner | `04_iftsta_outbound` (`status_code=<dynamic>`) | M1 |

**Routing per partner** odbywa się **wewnątrz subworkflow**, NIE w `tos-poll-events.yaml`. Mechanizm:
1. Subworkflow dostaje `event` z `doc_id` i `doc_symbol`.
2. Wywołuje `pinquark-tos.tos_doc_get_status(doc_id)` — zwraca m.in. `contractor_code` i pole EAV `TOS_EDI_PARTNER_CODES` (jeden lub więcej partnerów do których wysyłamy CODECO/IFTSTA dla tego dokumentu).
3. Wywołuje `oip-internal.partner_registry.resolve_by_codes(partner_codes)` — zwraca listę `[{ partner_code, edifact_account, ftp_account, smdg_profile }]`.
4. `foreach` po liście — dla każdego partnera: `edifact.codeco.build` z jego account (sender_id, receiver_id, wersja) → `ftp-sftp.file.upload` z jego account.

**Konsekwencja:** podpięcie 6. partnera EDI nie wymaga zmian ani w `tos-poll-events.yaml`, ani w żadnym z 12 workflow templates. Wystarczy:
- 1 wpis w partner registry (sekcja 14.6.6),
- 1 plik `accounts/edifact/<partner>-edi.yaml`,
- 1 plik `accounts/ftp-sftp/<partner>-sftp.yaml`,
- (po stronie TOS) zarejestrowanie partnera w `tos_contractor` jeśli jeszcze go nie ma.

#### 14.6.6. Partner registry OIP — kartoteka partnerów EDI

> **Po co:** workflowy są partner-agnostyczne, ale gdzieś musi być mapping `partner_code (z TOS) → konta techniczne (FTP, EDIFACT) i SMDG profile`. Trzymamy to **w bazie OIP**, nie w kodzie i nie w workflowach.

**Tabela `oip_partner_registry`** (w bazie OIP, np. nowy schemat `oip_edi.partner_registry`):

```sql
CREATE TABLE oip_edi.partner_registry (
    id              BIGSERIAL PRIMARY KEY,
    partner_code    TEXT NOT NULL UNIQUE,        -- 'METRANS', 'HHLA', 'KOMBI', 'DBCARGO', 'PKPCC', ...
    partner_name    TEXT NOT NULL,
    edifact_account TEXT NOT NULL,               -- nazwa konta z accounts/edifact/<...>.yaml
    ftp_account     TEXT NOT NULL,               -- nazwa konta z accounts/ftp-sftp/<...>.yaml
    smdg_profile    TEXT NOT NULL DEFAULT 'SMDG_2_0',  -- 'SMDG_1_5', 'SMDG_2_0' (różnice w segmentach RFF/EQD)
    edifact_version TEXT NOT NULL DEFAULT 'D_00B',     -- 'D_95B', 'D_00B'
    capabilities    JSONB NOT NULL DEFAULT '{}',  -- np. { "supports_yard_move": true, "needs_iftsta_progress": false }
    enabled         BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_partner_registry_enabled ON oip_edi.partner_registry(enabled) WHERE enabled = true;
```

**Przykładowe wpisy** (4 wiersze = 4 partnerów, zero kodu):

```sql
INSERT INTO oip_edi.partner_registry
    (partner_code, partner_name, edifact_account, ftp_account, smdg_profile, edifact_version, capabilities)
VALUES
    ('METRANS',  'Metrans a.s.',          'metrans-edi',  'metrans-sftp',  'SMDG_2_0', 'D_00B', '{"supports_yard_move": false}'),
    ('HHLA',     'HHLA Intermodal',       'hhla-edi',     'hhla-sftp',     'SMDG_2_0', 'D_00B', '{"supports_yard_move": true,  "needs_iftsta_progress": true}'),
    ('KOMBI',    'Kombiverkehr KG',       'kombi-edi',    'kombi-sftp',    'SMDG_1_5', 'D_95B', '{"supports_yard_move": false}'),
    ('PKPCC',    'PKP Cargo Connect',     'pkpcc-edi',    'pkpcc-sftp',    'SMDG_2_0', 'D_00B', '{}');
```

**Wewnętrzny konektor `oip-internal`** (część platformy OIP, nie nowy konektor) udostępnia akcje:

| Akcja | Input | Output | Użycie |
|---|---|---|---|
| `partner_registry.resolve_by_codes` | `{ partner_codes: ['METRANS','HHLA'] }` | `{ partners: [{ partner_code, edifact_account, ftp_account, smdg_profile, edifact_version, capabilities }, ...] }` | W subworkflowach outbound — fanout do wielu partnerów |
| `partner_registry.resolve_by_ftp_account` | `{ ftp_account: 'metrans-sftp' }` | `{ partner_code, edifact_account, smdg_profile, edifact_version }` | W workflowach inbound — z konta SFTP które wyzwoliło trigger wyciągamy partnera |
| `partner_registry.list_enabled` | `{}` | `{ partners: [...] }` | W `12_reconciliation_daily.yaml` — iteracja per partner |

**Strona TOS:** każdy dokument (`tos_doc`) ma:
- `tos_doc.contractor_id` → `tos_contractor` (właściciel ładunku — strona handlowa),
- EAV `TOS_EDI_PARTNER_CODES` (CSV `'METRANS,HHLA'` lub pojedynczy `'METRANS'`) — jeden lub wielu odbiorców EDI dla tego dokumentu.

Domyślnie `TOS_EDI_PARTNER_CODES` jest dziedziczone z `tos_contractor.tos_default_edi_partner_codes` (atrybut EAV), ale można go nadpisać per dokument (np. dla pociągu mieszanego). Ten atrybut jest dodany do listy zadań Mateusza w sekcji 14.8 jako jednorazowa rozszerzona migracja schematu kartotekowego.

**Onboarding nowego partnera EDI — checklist:**
1. ☐ Dodaj wpis do `oip_edi.partner_registry` (1 SQL INSERT).
2. ☐ Utwórz `accounts/edifact/<code>-edi.yaml` (sender_id, receiver_id, smdg_profile).
3. ☐ Utwórz `accounts/ftp-sftp/<code>-sftp.yaml` (host, port, user, key, paths).
4. ☐ (TOS) Dodaj `tos_contractor` jeśli nie istnieje, ustaw `tos_default_edi_partner_codes`.
5. ☐ Smoke test: ręcznie wrzuć COPRAR_TEST.edi na nowy SFTP — zweryfikuj że workflow `01_coprar_inbound` zadziałał i AWK powstał.
6. ☐ Smoke test outbound: utwórz testowy ZT dla tego partnera, potwierdź wjazd TIR — sprawdź że CODECO trafiło na ich SFTP.

**Suma kroków: 6 wpisów konfiguracyjnych. Zero linii kodu, zero deploya, zero modyfikacji workflow.**

### 14.7. Test smoke po setupie

Po wykonaniu `setup_tos_integrations.sql` zweryfikuj minimum trzy ścieżki: inbound Serwis biznesowy, outbound polling oraz IFTSTA pull.

```bash
# 1. Test integracji Serwis biznesowej (OIP → TOS) — utworzenie awizacji kolejowej
curl -X POST https://clip-malaszewicze.pinquark.app/integration/tos_notification_rail_save \
     -H "Authorization: Bearer <jwt>" \
     -H "token-mer: <token_z_setup_skryptu>" \
     -H "Content-Type: application/json" \
     -d '{
       "tos_train_no": "TEST-001",
       "tos_doc_planned_arrival": "2026-04-20T10:00:00Z",
       "carrier_code": "TEST",
       "TOS_DOC_POL": "DEHAM",
       "TOS_DOC_POD": "PLMSZ"
     }'

# Spodziewana odpowiedź:
# {"status":"OK","message":"AWK created","doc_id":12345}

# 2. Test outbound polling (KRYTYCZNE M0) — pobranie nowych zdarzeń od kursora
curl -X POST https://clip-malaszewicze.pinquark.app/integration/tos_get_events_since \
     -H "Authorization: Bearer <jwt>" \
     -H "token-mer: <token_z_setup_skryptu>" \
     -H "Content-Type: application/json" \
     -d '{"last_audit_id": 0, "limit": 10}'

# Spodziewana odpowiedź:
# {
#   "status": "OK",
#   "events": [
#     {"id": 1, "created_at": "2026-04-19T...", "module": "Awizacje",
#      "event_type": "AWK_RAIL_ZAPISANA", "doc_id": 12345, "doc_symbol": "AWK-...",
#      "user_id": 17, "user_login": "service.oip", "details": {...}},
#     ...
#   ],
#   "max_id": 10,
#   "count": 10
# }
#
# Drugi poll z last_audit_id=10 powinien zwrócić count=0 (jeśli nikt nic nie robił)

# 3. Test IFTSTA pull (M1) — status konkretnego dokumentu
curl -X POST https://clip-malaszewicze.pinquark.app/integration/tos_doc_get_status \
     -H "Authorization: Bearer <jwt>" \
     -H "token-mer: <token_z_setup_skryptu>" \
     -H "Content-Type: application/json" \
     -d '{"doc_id": 12345}'

# 4. Sprawdź audyt wywołań integracji
psql -d pinquark_tos -c "SELECT i.name, h.time, h.ip
                          FROM con_integration_history h
                          JOIN con_integration i ON i.id = h.con_integration_id
                          WHERE i.name LIKE 'tos_%'
                          ORDER BY h.id DESC LIMIT 10;"
```

### 14.8. Co Mateusz musi przygotować po stronie TOS (nie Twoje zadanie)

> **Wszystkie zadania TOS po stronie outbound EDI sprowadzają się do dorobienia 5 nowych procedur read-only + 2 tabel metadanych.** Zero modyfikacji istniejących 92 wywołań `tos_log_event`, zero modyfikacji procedur `tos_change_doc_status`/`tos_gate_*`/`tos_operation_*`, zero helpera `tos_webhook_emit`, zero integracji typu Klient. Łączny szacowany czas po stronie TOS: ~15 h (z czego 6 h na M0; +3 h na M1 gdzie doszły task'i 14.8.14–14.8.15 dla auto-discovery OIP).

#### M0 (krytyczne dla pilotu Metrans, ~6 h)

| # | Zadanie | Plik docelowy |
|---|---|---|
| 14.8.1 | Implementacja `tos_get_events_since(p_data json) RETURNS json` (gotowy kod w sekcji 14.6.2) | `clip/TOS/tos_procedures.sql` |
| 14.8.2 | Implementacja `tos_get_doc_status_changes_since(p_data json) RETURNS json` (gotowy kod w sekcji 14.6.3) | `clip/TOS/tos_procedures.sql` |
| 14.8.3 | INSERT-y reakcji do `tos_reactions.sql` dla obu nowych procedur (kolejne wolne `id`, `proc_name = nazwa procedury`, `active = true`) | `clip/TOS/tos_reactions.sql` |
| 14.8.4 | Uruchomić `setup_tos_integrations.sql` (sekcja 14.5) na bazie TOS — JEDEN RAZ. Skrypt jest idempotentny — można puszczać po każdym dorobieniu nowej reakcji | nowy plik `clip/TOS/sql/setup_tos_integrations.sql` |
| 14.8.5 | Przekazać Tobie token zwrócony przez `RAISE NOTICE` ze skryptu 14.5 — wpisujesz w account `clip-malaszewicze` w OIP | (sekret, przez bezpieczny kanał) |
| 14.8.6 | Sanity check: `SELECT module, event_type, COUNT(*) FROM tos_audit_log GROUP BY 1,2 ORDER BY 3 DESC LIMIT 30` — porównać ze wszystkimi `event_type` z mapowania 14.6.5. Każdy używany typ MUSI być na liście; jeśli czegoś brak — to bug w `tos_log_event` w jakiejś procedurze biznesowej | (analiza danych) |

#### M1 (po MVP, ~3 h)

| # | Zadanie | Plik docelowy |
|---|---|---|
| 14.8.7 | Implementacja `tos_doc_get_status(p_data json) RETURNS json` — IFTSTA pull request (A12.37). **Output musi zawierać `contractor_code` oraz pole `edi_partner_codes` (CSV)** — z EAV `TOS_EDI_PARTNER_CODES` na dokumencie z fallbackiem na `tos_default_edi_partner_codes` z kontrahenta. To pozwala OIP zrobić routing per partner (sekcja 14.6.6) | `clip/TOS/tos_procedures.sql` |
| 14.8.8 | Implementacja `tos_container_get_status(p_data json) RETURNS json` — IFTSTA pull request (A12.38) | `clip/TOS/tos_procedures.sql` |
| 14.8.9 | INSERT-y reakcji w `tos_reactions.sql`, ponowny run skryptu setupowego | `clip/TOS/tos_reactions.sql` |
| 14.8.10 | **Atrybut EAV `TOS_EDI_PARTNER_CODES` na `wms_doc`** (typ TEXT, format CSV `'METRANS,HHLA'`) — używany przez OIP do fanout EDI per dokument. Domyślnie pusty (fallback na kontrahenta). Jednorazowy `INSERT` do `wms_attribute` + `wms_attribute_link` dla wszystkich `wms_lib_doc.symbol IN ('AWK','AVD','ZT','PRZ','OPER')`. Atrybut musi być widoczny w UI dokumentu (zakładka EDI lub w „Dane awizacji") | `clip/TOS/tos_tables.sql` + `SCREENS_DESCRIPTION.toml` |
| 14.8.11 | **Atrybut EAV `tos_default_edi_partner_codes` na `tos_contractor`** (typ TEXT, CSV) — domyślny zestaw partnerów EDI dla kontrahenta. Używany jako fallback przez `tos_doc_get_status` jeśli `TOS_EDI_PARTNER_CODES` na dokumencie jest pusty | `clip/TOS/tos_tables.sql` + ekran kartoteki kontrahenta w `SCREENS_DESCRIPTION.toml` |
| 14.8.14 | **Procedura `tos_get_openapi_spec(p_data json) RETURNS json`** — buduje OpenAPI 3.1 spec dla wszystkich aktywnych integracji TOS z metadanych `tos_api_schema`. Pełny gotowy kod w sekcji 15.4.2.2. Wymaga rejestracji jako reakcja w `tos_reactions.sql` (id 1099) + dorzucenia do `v_reactions` w `setup_tos_integrations.sql`. **Wymagane przez OIP konektor `rest-api` w trybie auto-discovery (Tryb B, sekcja 15.4.1)** — bez tej procedury OIP nie odkryje dynamicznych endpointów Pinquark | `clip/TOS/tos_procedures.sql` + `clip/TOS/tos_reactions.sql` |
| 14.8.15 | **Tabela `tos_api_schema` + generator `scripts/generate_api_schemas.py`** — tabela trzyma request/response schemas per procedura (sekcja 15.4.2.1). Generator parsuje `tos_procedures.sql` regexem (~85% pól automatycznie wykrywanych) + merge z `tos_api_schemas_overrides.json` dla pozostałych 15%. Wpięcie w pipeline deploy: po `generate_list_definitions.py`, przed `generate_screens_from_description.py`. Wynik (`tos_api_schemas.json`) konwertowany na INSERT-y w `tos_tables.sql` z `ON CONFLICT (procedure_name) DO UPDATE` (idempotentne) | `clip/TOS/tos_tables.sql` + `clip/TOS/scripts/generate_api_schemas.py` + `clip/TOS/tos_api_schemas_overrides.json` |

#### M2 (backlog, ~3 h)

| # | Zadanie | Plik docelowy |
|---|---|---|
| 14.8.12 | **Bug fix:** dorobić `tos_gate_road_exit_confirm(p_data json) RETURNS json` — reakcja z `id=1046` jest, procedury brak (rozbieżność znaleziona podczas audytu) | `clip/TOS/tos_procedures.sql` |
| 14.8.13 | (opcjonalnie) `tos_train_container_add_bulk(p_data json) RETURNS json` — batch dla COPRAR z 3000+ kontenerów (zamiast pętli OIP po pojedynczych `tos_train_container_add`) | `clip/TOS/tos_procedures.sql` |

#### Czego Mateusz **NIE musi robić** (świadome decyzje wynikające z pull patternu)

- ❌ Helpera `tos_webhook_emit` — niepotrzebny.
- ❌ Modyfikacji żadnej z 92 istniejących linii `PERFORM tos_log_event(...)` — używamy ich tak jak są.
- ❌ Wpięcia `PERFORM` w procedurach `tos_change_doc_status`, `tos_gate_road_entry_confirm`, `tos_gate_road_exit_confirm`, `tos_gate_rail_entry_confirm`, `tos_gate_rail_exit_confirm`, `tos_operation_complete`, `tos_movement_complete`, `tos_notification_*_approve`, `tos_damage_report_save`.
- ❌ Tworzenia tabeli `tos_edi_message_log` — `tos_audit_log` w pełni wystarcza jako audit trail (OIP loguje swoje akcje EDI w swoim repo).
- ❌ Nowych wpisów w `con_connection` z URL OIP — TOS nic nie wie o adresie OIP.
- ❌ Rozszerzenia `pg_net`, `plperlu` ani innego mechanizmu HTTP w PostgreSQL TOS.
- ❌ **Tabeli partnerów EDI po stronie TOS** — partner registry jest **w bazie OIP** (`oip_edi.partner_registry`, sekcja 14.6.6). TOS udostępnia tylko **kody partnerów** (CSV w EAV `TOS_EDI_PARTNER_CODES` na dokumencie + `tos_default_edi_partner_codes` na kontrahencie). Tłumaczenie kod → konfiguracja techniczna (SFTP, sender/receiver IDs, wersja EDIFACT) odbywa się w OIP, **nie w TOS**.
- ❌ Pisania nowych workflowów w OIP per partner — workflowy są partner-agnostyczne (sekcja 3.3, 14.6.4). Onboarding partnera = 6 wpisów konfiguracyjnych, zero linii kodu.
- ❌ Pisania `connector.yaml` z 40 akcjami ręcznie po stronie OIP — auto-discovery (sekcja 15.4) odczyta listę endpointów z `tos_get_openapi_spec` (Tryb B). Po stronie TOS wystarczy task 14.8.14–14.8.15 (procedura + tabela schemas + generator). Po stronie OIP konektor `rest-api` jest 100% generyczny.

### 14.9. Pułapki

1. **`con_lib_integration_type.symbol`** — wartość `'OWN'` jest hipotetyczna. Sprawdź `SELECT id, name, symbol FROM con_lib_integration_type;` w docelowej bazie i poprawnie ustaw `WHERE symbol = '...'`. W niektórych instalacjach jest `'CUSTOM'` lub `'WLASNA'`.
2. **`con_lib_integration_status.name`** — analogicznie sprawdź czy jest `'active'`, `'aktywne'`, czy może `'enabled'`.
3. **Token w `con_token.token`** jest **plaintext** + `token_hash` SHA256. Aplikacja Pinquark sprawdza hash, ale plaintext jest też w bazie — chroń backupy.
4. **Limit `limit_per_minute`** — domyślnie ustawiony na 600 (10 RPS). Dla flow EDI batch (np. COPRAR z 60 wagonami × 50 kontenerów = 3000 wywołań) zwiększ do 6000+ albo użyj batch endpointów (`tos_train_add_container_bulk` — do dorobienia po stronie TOS).
5. **Idempotentność** — skrypt setupu jest idempotentny (UPDATE-y zamiast INSERT-ów dla istniejących integracji). Możesz go puszczać wielokrotnie po dodaniu nowej reakcji do listy `v_reactions`.
6. **Wersjonowanie** — przy dodawaniu nowych reakcji TOS wersjonuj nazwy integracji (`tos_notification_rail_save_v2`), żeby nie zepsuć istniejących wywołań OIP. Stare integracje dezaktywuj przez `UPDATE con_integration SET status = 2 WHERE name = '...'` (zgodnie z konwencją statusów TOS — soft-delete).

### 14.10. Mapowanie na akcje w `pinquark-tos/connector.yaml`

Każda integracja Serwis utworzona przez skrypt 14.5 musi mieć odpowiadającą akcję w `connector.yaml`. Przykład:

```yaml
# integrators/wms/pinquark-tos/v1.0.0/connector.yaml (fragment)
actions:
  - id: notification.rail.save
    display_name: "Awizacja kolejowa - zapisz"
    description: "Tworzy awizację kolejową (AWK) z wagonami i kontenerami"
    method: POST
    path: "{path_prefix}/tos_notification_rail_save"   # ← MUSI = con_integration.name
    auth:
      headers:
        Authorization: "Bearer {bearer_token}"
        token-mer: "{mer_token}"
    input_schema_ref: "schemas/notification_rail.json"
    output_schema_ref: "schemas/reaction_response.json"
    timeout_seconds: 30
    retry:
      max_attempts: 3
      backoff_initial_seconds: 2
      backoff_multiplier: 2
      retryable_status_codes: [429, 502, 503, 504]
```

Konwencja: **`action.path` po `{path_prefix}` = `con_integration.name`**. Trzymaj 1:1 — żeby dodanie nowej akcji w OIP wymagało tylko dodania jednego rekordu w `con_integration` po stronie TOS, bez zmian w aplikacji.

### 14.11. Diagnostyka — jak debugować błędy

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| `401 Unauthorized` | Niepoprawny token w `token-mer` lub token zdezaktywowany | `SELECT id, status FROM con_token WHERE token = '...'` — `status` musi być `1` |
| `404 Not Found` | Brak integracji o takiej nazwie LUB `status = 2` | `SELECT * FROM con_integration WHERE name = '...'` |
| `403 Forbidden` | Token nie powiązany z tą konkretną integracją | `SELECT * FROM con_integration_token WHERE con_integration_id = X AND con_token_id = Y` |
| `500 Internal Server Error` z `procedure raised exception` | Błąd w PL/pgSQL reakcji | `SELECT * FROM con_integration_history WHERE con_integration_id = X ORDER BY time DESC LIMIT 5` + Pinquark logs |
| `429 Too Many Requests` | Przekroczony `limit_per_minute` | Zwiększ limit albo wprowadź batch w OIP |
| Polling zwraca `count: 0` cały czas | Procedury TOS nie wstawiają do `tos_audit_log` LUB filtr `modules` jest niepoprawny | `SELECT MAX(id), MAX(created_at) FROM tos_audit_log` — sprawdź czy timestamp rośnie w trakcie operacji w Pinquark UI |
| Polling gubi eventy | Workflow OIP nie zapisał `last_audit_id` po crashu | Sprawdzić state OIP (`oip state get tos-poll-events.last_audit_id`) i ręcznie wycofać kursor; eventy są persistent w `tos_audit_log` więc reprocess jest bezpieczny |
| `event_type` w `tos_audit_log` nie ma mapowania w workflow | Nowa procedura biznesowa TOS dodała `tos_log_event` z nieznaną nazwą | Dodać case w `route_events` w `tos-poll-events.yaml` lub świadomie zostawić na `default: log` |
| Duplikaty wiadomości EDI u partnera | Crash OIP po wysłaniu EDI ale przed `state.save` kursora | Dedupe po stronie partnera po `MSG_REF` (= `<doc_symbol>-<audit_id>`) — partner EDI to standardowo robi |

---

## 13. Kontakt i ownership

- **Repo TOS:** `/Users/mateuszkalinowski/Downloads/pinquark_implementation/clip/TOS/`
- **Repo OIP:** `/Users/mateuszkalinowski/Open-Integration-Platform/`
- **Autor projektu:** Mateusz Kalinowski
- **Klient docelowy:** Clip-Terminal Małaszewice (potem Mała, Zabrze)
- **Operatorzy do integracji (priorytet):** Metrans → HHLA → Kombiverkehr → DB Cargo → PKP Cargo Connect

---

---

## 15. Zmiana architektoniczna: Generyczny REST API connector zamiast dedykowanego `pinquark-tos`

> **Decyzja:** Zamiast tworzyć dedykowany konektor `integrators/wms/pinquark-tos/v1.0.0/`, tworzymy **generyczny konektor `integrators/other/rest-api/v1.0.0/`** — uniwersalny proxy REST, który pozwala podłączyć dowolny system REST (nie tylko Pinquark TOS) przez konfigurację konta.

### 15.1. Uzasadnienie

Analiza kodu klienta TOS z sekcji 2.5 pokazuje, że cała logika `pinquark-tos` sprowadza się do **jednej generycznej operacji**:

```python
POST {base_url}/{path_prefix}/{endpoint_name}
Headers: Authorization: Bearer {token}, token-mer: {custom_token}
Body: { ...arbitrary JSON... }
Response: { "status": "OK"|"ERROR", "message": "...", "data": {...} }
```

Nie ma tu żadnej logiki specyficznej dla Pinquark — jedynie konfigurowalny URL, headery auth i konwencja response. Tworzenie dedykowanego konektora dla tak generycznej operacji łamie zasadę DRY i zamyka OIP na podłączanie innych systemów.

**Porównanie podejść:**

| Aspekt | Dedykowany `pinquark-tos` | Generyczny `rest-api` |
|---|---|---|
| Podłączenie Pinquark TOS Małaszewicze | Działa | Działa — konto z profilem `pinquark-tos` |
| Podłączenie innego TOS (np. Navis N4, TOPS Expert) | Nowy konektor od zera | Nowe konto z innym profilem/auth |
| Podłączenie ERP (SAP REST, Dynamics 365) | Nowy konektor od zera | Nowe konto |
| Podłączenie dowolnego REST API partnera | Nie obsługuje | Nowe konto |
| Typowanie payloadów (Pydantic per akcja) | Silne (40 schemas) | Luźne (pass-through JSON) — walidacja po stronie docelowego systemu |
| Czytelność workflow YAML | `connector: pinquark-tos` / `action: awk.create` | `connector: rest-api` / `action: rest.call` + `endpoint: tos_notification_rail_save` |
| Dashboard OIP — lista akcji | 40 named actions | Auto-discovered z OpenAPI spec + opcjonalny action registry per konto |
| Czas implementacji | ~3 dni (klon + 40 schemas + routing) | ~2 dni (generyczny + profile system + auto-discovery) |
| Reużywalność | Zerowa | Nieograniczona — każdy nowy system REST = nowe konto w dashboard |
| Zgodność z filozofią OIP "any-to-any" | Częściowa (1 system) | Pełna |
| UX konfiguracji | Hardcoded — agent pisze YAML per system | **Self-service** — user podaje URL + auth → konektor sam odkrywa endpointy |

### 15.2. Architektura konektora `rest-api`

```
integrators/other/rest-api/v1.0.0/
├── .env.example
├── Dockerfile
├── connector.yaml
├── docker-compose.yml
├── requirements.txt
├── config/
│   ├── accounts.yaml.example
│   └── profiles/                    # wbudowane profile response mapping
│       ├── pinquark.yaml            # profile: pinquark (status/message/data)
│       ├── generic.yaml             # profile: generic (HTTP status only)
│       └── sap.yaml                 # profile: sap (d.results pattern)
├── src/
│   ├── __init__.py
│   ├── config.py                    # Settings (pydantic-settings)
│   ├── main.py                      # FastAPI app factory
│   ├── api/
│   │   ├── dependencies.py          # AppState
│   │   └── routes.py                # generyczne endpointy
│   ├── schemas/
│   │   ├── common.py                # RestCallRequest, RestCallResponse, etc.
│   │   └── account.py               # AccountConfig, AuthConfig, ResponseMapping
│   ├── services/
│   │   ├── account_manager.py       # zarządzanie kontami
│   │   ├── rest_client.py           # generyczny klient REST z retry + auth
│   │   ├── auth_provider.py         # strategia auth (Bearer, Basic, OAuth2, API key, custom headers)
│   │   ├── response_parser.py       # parsowanie response wg profilu/mappingu
│   │   └── openapi_discovery.py     # auto-discovery endpointów z OpenAPI/Swagger spec
│   └── validators/
│       └── request_validator.py     # walidacja URL, headers, timeout
└── tests/
    ├── conftest.py
    ├── test_rest_client.py
    ├── test_auth_provider.py
    ├── test_response_parser.py
    └── test_api.py
```

### 15.3. Konfiguracja konta — flow w dashboard OIP

> **Kluczowa zmiana:** Użytkownik **nie edytuje YAML-a ręcznie**. Konfiguracja konta odbywa się w dashboardzie OIP, tak samo jak dla każdego innego konektora (InPost, DHL, Allegro itd.) — przez formularz z polami `config_schema`.

#### Krok 1: Użytkownik wypełnia formularz połączenia

W dashboardzie OIP, po wybraniu konektora "REST API Gateway", użytkownik widzi formularz:

```
┌─────────────────────────────────────────────────────────┐
│  Nowe połączenie: REST API Gateway                       │
│                                                          │
│  Nazwa konta:    [clip-malaszewicze                    ] │
│  Base URL:       [https://clip-malaszewicze.pinquark.app] │
│  Path prefix:    [/integration                         ] │
│                                                          │
│  ── Autentykacja ──                                      │
│  Typ auth:       [Bearer + Custom Headers        ▼]     │
│  Bearer Token:   [••••••••••••••••••••••           ]     │
│  Custom Headers: [token-mer: ••••••••••            ]     │
│                                                          │
│  ── Opcjonalne ──                                        │
│  Response profile: [pinquark                     ▼]     │
│                    (auto / pinquark / generic / sap)     │
│                                                          │
│     [Testuj połączenie]    [Zapisz i odkryj endpointy]  │
└─────────────────────────────────────────────────────────┘
```

To jest **standardowy mechanizm OIP** — `config_schema` w `connector.yaml` definiuje te pola (sekcja 15.4).

#### Krok 2: Auto-discovery endpointów (po kliknięciu "Zapisz i odkryj endpointy")

Konektor automatycznie próbuje pobrać specyfikację OpenAPI z docelowego systemu. Wspiera **dwa tryby**:

**Tryb A — system natywnie wystawia OpenAPI** (Spring Boot, .NET, Express z swagger-jsdoc, FastAPI z core'owymi routami):

```
Próbuję odkryć endpointy z:
  1. GET  {base_url}/openapi.json          ← FastAPI (natywne routy core)
  2. GET  {base_url}/swagger.json          ← Swagger 2.0
  3. GET  {base_url}/api-docs              ← Spring Boot
  4. GET  {base_url}/v3/api-docs           ← Spring Boot v3
  5. GET  {base_url}/.well-known/openapi   ← RFC 9264
  6. GET  {base_url}{path_prefix}/openapi.json
```

**Tryb B — system wymaga dedykowanego endpointu spec** (Pinquark TOS/WMS/TMS — mechanizm „Integracji własnych" rejestruje dynamiczne endpointy w bazie `con_integration`, których core'owy `/openapi.json` FastAPI nie zna i nie opisuje):

```
Próbuję odkryć endpointy (jeśli config_schema.openapi_spec_path jest ustawiony):
  7. <openapi_spec_method> {base_url}{openapi_spec_path}
     np. POST /integration/tos_get_openapi_spec
     z nagłówkami auth (token-mer, Bearer)
     z body z config_schema.openapi_spec_body (np. "{}")
```

> **Realia Pinquark (ważne):** rdzeń Pinquark (FastAPI) wystawia `/openapi.json`, ale opisuje tam **tylko core routy** (auth, health, admin) — **NIE** opisuje dynamicznych endpointów `/integration/*`, bo są one rejestrowane runtime z bazy `con_integration` po stronie aplikacji, a FastAPI generuje swój spec ze statycznych dekoratorów `@app.post(...)`. Dla pełnego discovery 40 integracji TOS trzeba wskazać **dedykowany endpoint serwujący OpenAPI** dla wszystkich aktywnych integracji własnych — patrz sekcja 15.4.2 (server-side `tos_get_openapi_spec`). Bez niego konektor `rest-api` w Trybie A znajdzie tylko core endpointy Pinquark (~5 sztuk), a 40 integracji biznesowych trzeba by wpisać ręcznie.

```
✅ Tryb B (Pinquark): Znaleziono OpenAPI 3.1.0 pod
   POST https://clip-malaszewicze.pinquark.app/integration/tos_get_openapi_spec
   Znaleziono 40 endpointów (38 biznesowych + 2 polling). Importuję...
```

Dashboard wyświetla odkryte endpointy do potwierdzenia:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Odkryte endpointy (40)                                  [Zaznacz wszystkie] │
│                                                                      │
│  ☑ POST /integration/tos_notification_rail_save                      │
│    → Tworzy awizację kolejową (AWK) z wagonami i kontenerami         │
│    Input: { tos_train_no: string, tos_doc_planned_arrival: datetime, │
│             carrier_code: string, TOS_DOC_POL: string, ... }         │
│                                                                      │
│  ☑ POST /integration/tos_notification_rail_approve                   │
│    → Zatwierdza AWK i tworzy KZT                                    │
│    Input: { doc_id: integer }                                        │
│                                                                      │
│  ☑ POST /integration/tos_gate_road_entry_confirm                     │
│    → Potwierdza wjazd TIR na terminal                               │
│    Input: { doc_id: integer, vehicle_number: string, ... }           │
│                                                                      │
│  ☑ POST /integration/tos_get_events_since                            │
│    → Polling tos_audit_log od kursora                                │
│    Input: { last_audit_id: integer, limit: integer }                 │
│                                                                      │
│  ... (36 więcej)                                                     │
│                                                                      │
│  ── Aliasy (opcjonalne, dla czytelności w workflow) ──               │
│  ☑ Generuj automatyczne aliasy                                       │
│    tos_notification_rail_save → awk.create                           │
│    tos_notification_rail_approve → awk.approve                       │
│    tos_gate_road_entry_confirm → gate.road_entry_confirm             │
│    tos_get_events_since → events.poll                                │
│                                                                      │
│           [Importuj zaznaczone]     [Anuluj]                         │
└─────────────────────────────────────────────────────────────────────┘
```

**Co się dzieje pod spodem:**

1. `openapi_discovery.py` pobiera spec z `{base_url}/openapi.json`
2. Parsuje każdy `path` + `method` + `requestBody` + `responses`
3. Buduje `action_registry` z wyciągniętymi:
   - `endpoint` (ścieżka URL)
   - `method` (POST/GET/PUT/DELETE)
   - `description` (z OpenAPI `summary` / `description`)
   - `input_schema` (z `requestBody.content.application/json.schema`)
   - `output_schema` (z `responses.200.content.application/json.schema`)
4. Opcjonalnie generuje aliasy (`tos_notification_rail_save` → `awk.create`) przez heurystykę nazw
5. Zapisuje wynik jako część konfiguracji konta w bazie OIP

#### Krok 3: Gotowe — konto działa

Po imporcie konto ma pełny action registry. W workflow builder w dashboard użytkownik widzi dropdown z czytelnymi nazwami:

```
┌─────────────────────────────────────────────┐
│  Krok workflow: Wywołaj REST API             │
│                                              │
│  Konto:    [clip-malaszewicze          ▼]   │
│  Akcja:    [awk.create                 ▼]   │
│            ├── awk.create                    │
│            ├── awk.approve                   │
│            ├── awk.cancel                    │
│            ├── gate.road_entry_confirm       │
│            ├── gate.road_exit_confirm        │
│            ├── events.poll                   │
│            └── (34 więcej...)                │
│                                              │
│  Body:     { ... edytor JSON ... }           │
│                                              │
│  ⓘ Schema input (z OpenAPI):                │
│    tos_train_no: string (required)           │
│    tos_doc_planned_arrival: datetime          │
│    carrier_code: string                       │
└─────────────────────────────────────────────┘
```

#### Scenariusze discovery

| Scenariusz | Co się dzieje |
|---|---|
| **FastAPI (Pinquark TOS)** | `/openapi.json` dostępny domyślnie → pełne auto-discovery z schematami input/output |
| **Spring Boot** | `/api-docs` lub `/v3/api-docs` → pełne auto-discovery |
| **API bez OpenAPI spec** | Discovery nie znajduje spec → użytkownik ręcznie dodaje endpointy w formularzu (nazwa, ścieżka, metoda HTTP) |
| **Partial spec** | Discovery znajduje spec ale bez schematów → importuje endpointy, body traktuje jako pass-through JSON |
| **Prywatna sieć (on-premise)** | Discovery działa normalnie — konektor `rest-api` jest wewnątrz sieci, ma dostęp do prywatnych URL |
| **Re-discovery** | Użytkownik klika "Odśwież endpointy" po aktualizacji docelowego API → merge nowych endpointów z istniejącymi (nie kasuje ręcznie dodanych) |

#### Fallback: ręczne dodawanie endpointów

Jeśli docelowe API nie ma OpenAPI spec, użytkownik może ręcznie dodać endpointy w dashboardzie:

```
┌─────────────────────────────────────────────────────────┐
│  Ręczne dodawanie endpointów                             │
│                                                          │
│  [+ Dodaj endpoint]                                      │
│                                                          │
│  1. Alias:     [awk.create                             ] │
│     Endpoint:  [tos_notification_rail_save             ] │
│     Metoda:    [POST ▼]                                  │
│     Opis:      [Tworzy awizację kolejową               ] │
│                                                          │
│  2. Alias:     [events.poll                            ] │
│     Endpoint:  [tos_get_events_since                   ] │
│     Metoda:    [POST ▼]                                  │
│     Opis:      [Polling zdarzeń od kursora             ] │
│                                                          │
│  ... lub wklej OpenAPI JSON/YAML:                        │
│  [Wklej specyfikację]                                    │
└─────────────────────────────────────────────────────────┘
```

### 15.3.1. Jak to wygląda w bazie OIP (wewnętrznie)

Konfiguracja konta jest przechowywana w bazie OIP (nie w plikach YAML na dysku). Struktura wewnętrzna:

```json
{
  "account_name": "clip-malaszewicze",
  "connector": "rest-api",
  "config": {
    "base_url": "https://clip-malaszewicze.pinquark.app",
    "path_prefix": "/integration",
    "default_method": "POST",
    "profile": "pinquark",
    "auth": {
      "type": "bearer_with_custom_headers",
      "bearer_token": "vault://clip-malaszewicze/bearer_token",
      "custom_headers": {
        "token-mer": "vault://clip-malaszewicze/mer_token"
      }
    },
    "response_mapping": {
      "status_field": "status",
      "status_ok_value": "OK",
      "message_field": "message",
      "data_field": "data"
    },
    "timeouts": { "connect_s": 30, "read_s": 60 },
    "retry": { "max_attempts": 3, "backoff_initial_s": 2, "retryable_status_codes": [429, 502, 503, 504] },
    "rate_limit": "600/min"
  },
  "action_registry": {
    "awk.create": {
      "endpoint": "tos_notification_rail_save",
      "method": "POST",
      "description": "Tworzy awizację kolejową (AWK)",
      "input_schema": { "type": "object", "properties": { "tos_train_no": {"type": "string"}, "...": {} } },
      "output_schema": { "type": "object", "properties": { "status": {"type": "string"}, "doc_id": {"type": "integer"} } },
      "source": "openapi_discovery"
    },
    "events.poll": {
      "endpoint": "tos_get_events_since",
      "method": "POST",
      "description": "Polling tos_audit_log od kursora",
      "source": "openapi_discovery"
    }
  },
  "discovery": {
    "openapi_url": "https://clip-malaszewicze.pinquark.app/openapi.json",
    "last_discovered_at": "2026-04-15T10:30:00Z",
    "endpoints_count": 40,
    "openapi_version": "3.1.0"
  }
}
```

Credentiale (`bearer_token`, `mer_token`) trzymane w Credential Vault (AES-256-GCM), w bazie jest tylko referencja `vault://`.

### 15.3.2. Przykłady konfiguracji innych systemów (w dashboardzie — te same pola)

**Navis N4 (inny TOS):**

| Pole | Wartość |
|---|---|
| Nazwa konta | `gdynia-bct` |
| Base URL | `https://api.bct-gdynia.pl/n4/v2` |
| Typ auth | OAuth2 Client Credentials |
| Token URL | `https://api.bct-gdynia.pl/oauth/token` |
| Client ID | `(z vault)` |
| Client Secret | `(z vault)` |
| Profile | `generic` |
| Discovery | Auto z `/api-docs` → odkryto 28 endpointów |

**SAP S/4HANA:**

| Pole | Wartość |
|---|---|
| Nazwa konta | `sap-production` |
| Base URL | `https://sap.company.com/sap/opu/odata/sap` |
| Typ auth | Basic |
| Username | `(z vault)` |
| Password | `(z vault)` |
| Custom headers | `x-csrf-token: fetch` |
| Profile | `sap` |
| Discovery | Brak OpenAPI → ręcznie dodano 5 endpointów |

### 15.4. Manifest konektora `rest-api` (`connector.yaml`)

`connector.yaml` definiuje **formularz konfiguracji** (jak w każdym konektorze OIP) + **4 generyczne akcje**:

```yaml
name: rest-api
category: other
version: 1.0.0
display_name: "REST API Gateway"
description: >
  Uniwersalny konektor REST API — łączy OIP z dowolnym systemem 
  udostępniającym REST/JSON API. Po podaniu URL i danych auth 
  automatycznie odkrywa endpointy z OpenAPI spec.
interface: rest-api
country: global

capabilities:
  - rest_call
  - rest_poll
  - rest_batch
  - health_check
  - openapi_discovery
  - action_registry

# ── Formularz w dashboard OIP ──
# Te pola widzi użytkownik przy dodawaniu nowego połączenia.
# Identyczny mechanizm jak config_schema w InPost, DHL, Allegro itd.
config_schema:
  required:
    - base_url
  optional:
    - path_prefix
    - default_method
    - response_profile
    - connect_timeout_s
    - read_timeout_s
    - rate_limit
    - openapi_spec_path
    - custom_headers
  field_types:
    base_url:
      type: string
      label: "URL bazowy API"
      placeholder: "https://example.com/api"
      row: connection
    path_prefix:
      type: string
      label: "Prefix ścieżki (opcjonalny)"
      placeholder: "/integration"
      row: connection
    default_method:
      type: enum
      label: "Domyślna metoda HTTP"
      options: [POST, GET, PUT, PATCH, DELETE]
      default: POST
      row: connection
    response_profile:
      type: enum
      label: "Profil odpowiedzi"
      options: [auto, pinquark, generic, sap, custom]
      default: auto
      row: response
      help: >
        'auto' — konektor sam wykryje format odpowiedzi na podstawie 
        pierwszego test request. Wybierz konkretny profil jeśli auto 
        nie zadziała poprawnie.
    connect_timeout_s:
      type: integer
      label: "Timeout połączenia (s)"
      default: 30
      row: advanced
    read_timeout_s:
      type: integer
      label: "Timeout odczytu (s)"
      default: 60
      row: advanced
    rate_limit:
      type: string
      label: "Limit wywołań"
      placeholder: "600/min"
      row: advanced
    openapi_spec_path:
      type: string
      label: "Ścieżka do spec OpenAPI (opcjonalna)"
      placeholder: "/openapi.json"
      row: advanced
      help: >
        Zostaw puste — konektor sam spróbuje znaleźć spec pod typowymi 
        ścieżkami (/openapi.json, /swagger.json, /api-docs). Wypełnij 
        tylko jeśli spec jest pod niestandardową ścieżką.
    custom_headers:
      type: key_value_list
      label: "Dodatkowe headery HTTP"
      row: advanced

# ── Walidacja credentiali ──
# Po kliknięciu "Testuj połączenie" w dashboard.
credential_validation:
  required_fields: [base_url]
  # Konektor testuje połączenie i próbuje auto-discovery:
  # 1. Health check: GET {base_url}{path_prefix}/ → 200/401/403 = system żyje
  # 2. OpenAPI discovery: GET {base_url}/openapi.json → jeśli 200, parsuj spec
  # 3. Test auth: wywołaj GET z auth headers → 200 = credentiale OK
  validate_endpoint: /accounts/{account_name}/validate

# ── Provisioning credentiali ──
credential_provisioning:
  mode: account
  account_endpoint: /accounts
  payload_field: account_name
  credential_mapping:
    name: account_name
    base_url: base_url
    path_prefix: path_prefix
    auth_type: auth_type
    bearer_token: bearer_token
    username: username
    password: password
    client_id: client_id
    client_secret: client_secret
    api_key: api_key
    custom_headers: custom_headers

# ── Auth types ──
# Dynamiczny formularz w dashboard — pola zmieniają się w zależności od wybranego typu.
auth_types:
  bearer:
    fields: [bearer_token]
  bearer_with_custom_headers:
    fields: [bearer_token, custom_headers]
  basic:
    fields: [username, password]
  api_key_header:
    fields: [api_key, api_key_header_name]
  api_key_query:
    fields: [api_key, api_key_param_name]
  oauth2_client_credentials:
    fields: [token_url, client_id, client_secret, scope]
  none:
    fields: []

# ── Akcje generyczne ──
actions:
  - id: rest.call
    display_name: "REST Call"
    description: >
      Wywołaj endpoint REST. Użyj `named_action` (z odkrytych 
      endpointów) lub `endpoint` (surowa ścieżka).
    method: POST
    path: /rest/call

  - id: rest.poll
    display_name: "REST Poll"
    description: >
      Polling endpoint z kursorem. Automatycznie zarządza stanem 
      kursora (last_id / last_timestamp) między wywołaniami.
    method: POST
    path: /rest/poll

  - id: rest.batch
    display_name: "REST Batch Call"
    description: >
      Wykonaj wiele wywołań REST w jednym batchu.
    method: POST
    path: /rest/batch

  - id: rest.health
    display_name: "Health Check"
    description: "Sprawdź dostępność docelowego systemu REST."
    method: GET
    path: /rest/health

  - id: rest.discover
    display_name: "Odkryj endpointy"
    description: >
      Pobierz specyfikację OpenAPI z docelowego systemu 
      i zaktualizuj action registry konta.
    method: POST
    path: /rest/discover

action_routes:
  rest.call: /rest/call
  rest.poll: /rest/poll
  rest.batch: /rest/batch
  rest.health: /rest/health
  rest.discover: /rest/discover

# Per-action input fields (widoczne w workflow builder)
action_fields:
  rest.call:
    - field: account_name
      label: "Konto"
      type: string
      required: true
    - field: named_action
      label: "Akcja (z odkrytych endpointów)"
      type: string
      dynamic_options:
        source: account.action_registry
        label_field: description
        value_field: alias
    - field: endpoint
      label: "Endpoint (surowa ścieżka, alternatywa dla named_action)"
      type: string
    - field: method
      label: "Metoda HTTP (domyślna z konta)"
      type: enum
      options: [POST, GET, PUT, PATCH, DELETE]
    - field: body
      label: "Body (JSON)"
      type: json
      dynamic_schema:
        source: account.action_registry.{named_action}.input_schema
    - field: headers
      label: "Dodatkowe headery"
      type: key_value_list
    - field: query_params
      label: "Query params"
      type: key_value_list
    - field: timeout_s
      label: "Timeout (s)"
      type: integer
  rest.poll:
    - field: account_name
      label: "Konto"
      type: string
      required: true
    - field: named_action
      label: "Endpoint do pollingu"
      type: string
      dynamic_options:
        source: account.action_registry
    - field: cursor_field
      label: "Pole kursora w request"
      type: string
      placeholder: "last_audit_id"
    - field: cursor_response_field
      label: "Pole kursora w response"
      type: string
      placeholder: "max_id"
    - field: items_field
      label: "Pole z listą elementów w response"
      type: string
      placeholder: "events"
    - field: limit
      label: "Limit elementów"
      type: integer
      default: 1000

output_fields:
  rest.call:
    - field: status
      label: "Status (success/error)"
      type: string
    - field: http_status
      label: "HTTP status code"
      type: integer
    - field: response_status
      label: "Status z response (np. OK)"
      type: string
    - field: message
      label: "Wiadomość"
      type: string
    - field: data
      label: "Dane (JSON)"
      type: json
      dynamic_schema:
        source: account.action_registry.{named_action}.output_schema
    - field: elapsed_ms
      label: "Czas odpowiedzi (ms)"
      type: integer

health_endpoint: /health
docs_url: /docs
```

### 15.4.1. Auto-discovery — `openapi_discovery.py`

Serwis odpowiedzialny za automatyczne odkrywanie endpointów:

```python
class OpenAPIDiscovery:
    """Odkrywa endpointy z OpenAPI/Swagger spec docelowego systemu.

    Obsługuje dwa tryby:
      A) GET pod znaną ścieżką (FastAPI core, Spring Boot, .NET, Express)
      B) Dedykowany endpoint (POST/GET) wskazany w config_schema —
         wymagany dla systemów z dynamicznymi routami (Pinquark TOS/WMS).
    """

    # Tryb A — sondowanie standardowych ścieżek metodą GET
    PROBE_PATHS = [
        "/openapi.json",
        "/swagger.json",
        "/api-docs",
        "/v3/api-docs",
        "/.well-known/openapi",
        "{path_prefix}/openapi.json",
    ]

    async def discover(
        self,
        base_url: str,
        path_prefix: str,
        auth_headers: dict,
        # Tryb B — explicite wskazany endpoint z config_schema (priorytet)
        explicit_spec_path: str | None = None,
        explicit_spec_method: str = "GET",
        explicit_spec_body: dict | None = None,
    ) -> DiscoveryResult:
        """Najpierw spróbuj Trybu B (jeśli skonfigurowany), potem Trybu A."""
        # Tryb B — dedykowany endpoint (Pinquark TOS/WMS, każdy system z custom integration)
        if explicit_spec_path:
            url = f"{base_url}{explicit_spec_path}"
            spec = await self._try_fetch_spec(
                url,
                auth_headers,
                method=explicit_spec_method,
                body=explicit_spec_body or {},
            )
            if spec:
                return self._parse_spec(spec, path_prefix, mode="explicit")
            # NIE fallback do Trybu A — jeśli admin wskazał konkretny endpoint
            # i ten nie zwraca spec, to jest błąd konfiguracji, nie powód
            # żeby cicho importować tylko 5 core routów Pinquark.
            return DiscoveryResult(
                found=False,
                error=f"Tryb B: spec endpoint {explicit_spec_method} {url} nie zwrócił prawidłowego OpenAPI 3.x",
                endpoints=[],
            )

        # Tryb A — sondowanie standardowych ścieżek
        for path in self.PROBE_PATHS:
            resolved = path.replace("{path_prefix}", path_prefix)
            url = f"{base_url}{resolved}"
            spec = await self._try_fetch_spec(url, auth_headers, method="GET")
            if spec:
                return self._parse_spec(spec, path_prefix, mode="probe")
        return DiscoveryResult(found=False, endpoints=[])

    def _parse_spec(self, spec: dict, path_prefix: str) -> DiscoveryResult:
        """Parsuj OpenAPI spec → lista endpointów z schematami."""
        endpoints = []
        for path, methods in spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method in ("get", "post", "put", "patch", "delete"):
                    endpoint = path.removeprefix(path_prefix).strip("/")
                    endpoints.append(DiscoveredEndpoint(
                        endpoint=endpoint,
                        method=method.upper(),
                        description=operation.get("summary", ""),
                        input_schema=self._extract_input_schema(operation),
                        output_schema=self._extract_output_schema(operation),
                        alias=self._generate_alias(endpoint),
                    ))
        return DiscoveryResult(
            found=True,
            openapi_version=spec.get("openapi", spec.get("swagger", "unknown")),
            endpoints=endpoints,
        )

    def _generate_alias(self, endpoint: str) -> str:
        """Heurystyka: tos_notification_rail_save → awk.create."""
        alias_map = {
            "tos_notification_rail_save": "awk.create",
            "tos_notification_rail_approve": "awk.approve",
            "tos_gate_road_entry_confirm": "gate.road_entry_confirm",
            "tos_get_events_since": "events.poll",
            # ... dalsze mapowania — lub generuj z nazwy endpointu
        }
        return alias_map.get(endpoint, endpoint.replace("/", "."))
```

**Kluczowe cechy:**
- Probe wielu ścieżek (Tryb A) — obsługuje natywne OpenAPI w Spring Boot, .NET, Express, FastAPI core
- Dedykowany endpoint (Tryb B) — obsługuje custom integration patterns (Pinquark TOS/WMS, dowolny system z dynamicznymi routami)
- Parsuje zarówno OpenAPI 3.x jak i Swagger 2.0
- Wyciąga schematy input/output → wyświetlane w workflow builder
- Generuje aliasy automatycznie (heurystyka + opcjonalny mapping per profil)
- Wynik zapisywany w bazie OIP → re-discovery nie kasuje ręcznych modyfikacji
- Tryb B nie ma fallbacku do Trybu A — jeśli admin wskazał konkretny endpoint, błędna konfiguracja jest zgłaszana, nie ukrywana

**Przykład konfiguracji konta dla Pinquark TOS (Tryb B):**

```yaml
# accounts/rest-api/clip-malaszewicze.yaml (fragment dotyczący discovery)
discovery:
  enabled: true
  mode: explicit                                              # wymusza Tryb B
  spec_path: "/integration/tos_get_openapi_spec"              # endpoint po stronie TOS
  spec_method: POST                                           # bo Pinquark integracje to zawsze POST
  spec_body: {}                                               # pusty payload — procedura zwraca pełny spec
  spec_auth_headers:
    token-mer: "{{ secrets.tos_token }}"                      # ten sam token co dla wywołań biznesowych
  refresh_ttl_seconds: 3600                                   # cache spec na godzinę
  on_change: notify                                           # webhook do dashboardu jeśli pojawiły się nowe endpointy
```

**Przykład dla Spring Boot (Tryb A — wystarczy domyślne sondowanie):**

```yaml
discovery:
  enabled: true
  mode: probe                                                 # Tryb A (default)
  refresh_ttl_seconds: 3600
```

### 15.4.2. Strona serwerowa Pinquark — endpoint `tos_get_openapi_spec`

> **Po co:** auto-discovery z sekcji 15.4.1 w Trybie B wymaga, żeby docelowy system zwrócił prawidłowy OpenAPI 3.1 JSON pod wskazanym URL-em. Pinquark tego NIE robi natywnie dla integracji własnych. Trzeba dorobić **jeden endpoint** po stronie TOS (procedura PL/pgSQL + integracja Serwis), który dynamicznie buduje spec z metadanych w bazie. To zadanie po stronie Mateusza (~3 h), patrz sekcja 14.8.14–14.8.15.

**Architektura:**

```
┌─────────────────────────┐         ┌────────────────────────────────────┐
│  OIP konektor rest-api  │         │  Pinquark TOS (PostgreSQL + REST)  │
│                         │  POST   │                                    │
│  openapi_discovery.py   ├────────>│  /integration/tos_get_openapi_spec │
│  Tryb B: explicit       │         │     ↓                              │
│  spec_path = ...        │         │  procedura PL/pgSQL                │
│  spec_method = POST     │  JSON   │  tos_get_openapi_spec(p_data json) │
│                         │<────────┤     ↓                              │
│  parse spec → 40 akcji  │ OpenAPI │  SELECT ... FROM con_integration   │
│                         │  3.1.0  │            JOIN tos_api_schema     │
└─────────────────────────┘         │            JOIN app_reaction       │
                                    │     ↓                              │
                                    │  jsonb_build_object(...)           │
                                    └────────────────────────────────────┘
```

#### 15.4.2.1. Tabela `tos_api_schema` (po stronie bazy TOS)

Trzyma metadane request/response per procedura. Plik `clip/TOS/tos_tables.sql`:

```sql
CREATE TABLE IF NOT EXISTS public.tos_api_schema (
    procedure_name   TEXT PRIMARY KEY,                -- np. 'tos_notification_rail_save'
    summary          TEXT NOT NULL,                   -- jednoliniowy opis (do OpenAPI summary)
    description      TEXT,                            -- pełny opis biznesowy (markdown OK)
    tags             TEXT[] NOT NULL DEFAULT '{}',    -- np. ['Awizacje','Rail'] — grupowanie w UI
    request_schema   JSONB NOT NULL,                  -- JSON Schema body
    response_schema  JSONB NOT NULL,                  -- JSON Schema 200 response
    examples         JSONB,                           -- { "request": {...}, "response": {...} }
    deprecated       BOOLEAN NOT NULL DEFAULT false,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tos_api_schema_tags ON public.tos_api_schema USING gin(tags);
```

Wpis dla każdej z 40 procedur — generowany skryptem (sekcja 15.4.2.3), wprowadzany przez `INSERT ... ON CONFLICT (procedure_name) DO UPDATE` w `tos_tables.sql` na końcu pipeline'u deploy.

#### 15.4.2.2. Procedura `tos_get_openapi_spec(p_data json) RETURNS json`

Plik `clip/TOS/tos_procedures.sql`:

```sql
CREATE OR REPLACE FUNCTION public.tos_get_openapi_spec(
    p_data json
) RETURNS json
LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_base_path TEXT := '/integration';
    v_paths     JSONB := '{}'::jsonb;
    v_tags      JSONB := '[]'::jsonb;
    v_rec       RECORD;
    v_op        JSONB;
BEGIN
    -- Iteruj po aktywnych integracjach TOS, dla których mamy schema
    FOR v_rec IN
        SELECT
            ci.name           AS integration_name,        -- = nazwa procedury
            ci.description    AS integration_description,
            sch.summary,
            sch.description   AS sch_description,
            sch.tags,
            sch.request_schema,
            sch.response_schema,
            sch.examples,
            sch.deprecated
        FROM public.con_integration ci
        JOIN public.app_reaction ar ON ar.id = ci.app_reaction_id
        JOIN public.tos_api_schema sch ON sch.procedure_name = ar.proc_name
        WHERE ci.status = 1                                -- tylko aktywne
          AND ci.con_lib_integration_kind_id = (
              SELECT id FROM public.con_lib_integration_kind WHERE symbol = 'SERVICE'
          )
          AND ci.name LIKE 'tos_%'                         -- tylko TOS, nie WMS core
        ORDER BY ci.name
    LOOP
        v_op := jsonb_build_object(
            'operationId', v_rec.integration_name,
            'summary',     v_rec.summary,
            'description', COALESCE(v_rec.sch_description, v_rec.integration_description, ''),
            'tags',        to_jsonb(v_rec.tags),
            'deprecated',  v_rec.deprecated,
            'security',    jsonb_build_array(
                              jsonb_build_object('TokenMer', '[]'::jsonb)
                          ),
            'requestBody', jsonb_build_object(
                'required', true,
                'content',  jsonb_build_object(
                    'application/json', jsonb_build_object(
                        'schema',   v_rec.request_schema,
                        'examples', COALESCE(
                            jsonb_build_object('default',
                                jsonb_build_object('value', v_rec.examples->'request')),
                            '{}'::jsonb)
                    )
                )
            ),
            'responses', jsonb_build_object(
                '200', jsonb_build_object(
                    'description', 'Success',
                    'content', jsonb_build_object(
                        'application/json', jsonb_build_object(
                            'schema', v_rec.response_schema
                        )
                    )
                ),
                '401', jsonb_build_object('description', 'Unauthorized — brak/nieprawidłowy token-mer'),
                '404', jsonb_build_object('description', 'Integration not found / inactive'),
                '500', jsonb_build_object('description', 'Procedure raised exception')
            )
        );

        v_paths := v_paths || jsonb_build_object(
            v_base_path || '/' || v_rec.integration_name,
            jsonb_build_object('post', v_op)
        );
    END LOOP;

    -- Tagi (grupowanie endpointów w UI)
    SELECT jsonb_agg(DISTINCT jsonb_build_object('name', tag))
      INTO v_tags
      FROM public.tos_api_schema, unnest(tags) AS tag;

    RETURN json_build_object(
        'openapi', '3.1.0',
        'info', jsonb_build_object(
            'title',       'Pinquark TOS — Custom Integrations API',
            'version',     '1.0.0',
            'description', 'Auto-generated OpenAPI spec for active con_integration entries. ' ||
                           'Used by OIP rest-api connector for endpoint discovery (Tryb B).'
        ),
        'servers', jsonb_build_array(
            jsonb_build_object('url', current_setting('app.public_base_url', true))
        ),
        'components', jsonb_build_object(
            'securitySchemes', jsonb_build_object(
                'TokenMer', jsonb_build_object(
                    'type', 'apiKey',
                    'in',   'header',
                    'name', 'token-mer'
                )
            )
        ),
        'tags',  COALESCE(v_tags, '[]'::jsonb),
        'paths', v_paths
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'status',     'ERROR',
        'error_code', SQLSTATE,
        'message',    SQLERRM
    );
END $$;

COMMENT ON FUNCTION public.tos_get_openapi_spec(json) IS
  'Zwraca OpenAPI 3.1.0 spec dla wszystkich aktywnych integracji własnych TOS. ' ||
  'Używane przez konektor OIP rest-api do auto-discovery (Tryb B). ' ||
  'Wymaga wpisu w app_reaction + con_integration + tos_api_schema.';
```

Dodatkowo: **rejestracja jako integracja Serwis** — wpis do `tos_reactions.sql` + nowy wiersz w `setup_tos_integrations.sql` (sekcja 14.5):

```sql
-- tos_reactions.sql (kolejne wolne id, np. 1099)
INSERT INTO public.app_reaction (id, name, proc_name, active)
VALUES (1099, 'Pobierz OpenAPI spec', 'tos_get_openapi_spec', true)
ON CONFLICT (id) DO UPDATE SET proc_name = EXCLUDED.proc_name, active = true;
```

```sql
-- setup_tos_integrations.sql — dorzuć do listy v_reactions
v_reactions TEXT[] := ARRAY[
    -- ... 40 dotychczasowych ...
    'tos_get_openapi_spec'                  -- ← NOWE: spec endpoint dla auto-discovery OIP
];
```

#### 15.4.2.3. Generator `scripts/generate_api_schemas.py`

Mateusz nie pisze schematów request/response ręcznie 40 razy. Generujemy je z istniejących artefaktów:

| Źródło | Co wyciąga |
|---|---|
| `clip/TOS/reaction_registry.json` | mapping `proc_name → moduł, opis, label` (już istnieje) |
| `clip/TOS/procedury_logika_biznesowa.md` | description (sekcja per procedura → markdown przed kolejnym `###`) |
| `clip/TOS/tos_procedures.sql` | request_schema z regexa `p_data->>'(\w+)'` + typy z kontekstu (`::int`, `::numeric`, `::date`, `::timestamptz`); response_schema z `RETURN json_build_object(...)` |

Algorytm (pseudokod):

```python
# clip/TOS/scripts/generate_api_schemas.py
import re, json
from pathlib import Path

ROOT = Path(__file__).parent.parent
PROCEDURES_SQL = ROOT / "tos_procedures.sql"
REACTION_REGISTRY = ROOT / "reaction_registry.json"
LOGIC_DOC = ROOT / "procedury_logika_biznesowa.md"
OUT_JSON = ROOT / "tos_api_schemas.json"

# 1. Wczytaj reaction_registry (proc_name → moduł, label)
registry = json.loads(REACTION_REGISTRY.read_text())

# 2. Sparsuj tos_procedures.sql na bloki CREATE OR REPLACE FUNCTION
proc_blocks = re.findall(
    r"CREATE OR REPLACE FUNCTION public\.(\w+)\(\s*p_data json\s*\).*?\$\$;",
    PROCEDURES_SQL.read_text(), re.DOTALL
)

schemas = {}
for proc_name, body in proc_blocks:
    # 3a. Request schema — wyciągnij wszystkie p_data->>'pole' i wnioskuj typ
    fields = {}
    for m in re.finditer(r"p_data->>'(\w+)'(?:\s*\)\s*::(\w+))?", body):
        name, sql_type = m.group(1), m.group(2)
        json_type = SQL_TO_JSON_TYPE.get(sql_type, "string")
        fields[name] = {"type": json_type}
        # Heurystyka required: jeśli COALESCE/NULLIF wokół → optional, inaczej required
        if f"COALESCE(p_data->>'{name}'" in body or f"NULLIF(p_data->>'{name}'" in body:
            fields[name]["nullable"] = True

    # 3b. Response schema — sparsuj RETURN json_build_object(...)
    response_match = re.search(
        r"RETURN\s+json_build_object\s*\((.*?)\)\s*;\s*EXCEPTION",
        body, re.DOTALL
    )
    response_fields = parse_json_build_object(response_match.group(1)) if response_match else {}

    # 4. Zbuduj wpis
    reg = registry.get(proc_name, {})
    schemas[proc_name] = {
        "summary": reg.get("label", proc_name.replace("_", " ").title()),
        "description": extract_business_description(LOGIC_DOC, proc_name),
        "tags": [reg.get("module", "Other")],
        "request_schema": {"type": "object", "properties": fields, "required": [
            k for k, v in fields.items() if not v.get("nullable")
        ]},
        "response_schema": {"type": "object", "properties": response_fields},
        "examples": load_existing_examples(proc_name),  # opcjonalne, z manualnego override
    }

OUT_JSON.write_text(json.dumps(schemas, indent=2, ensure_ascii=False))
print(f"Wygenerowano {len(schemas)} schematów do {OUT_JSON}")
```

**Pokrycie:** ~85% pól wykrywanych automatycznie. Pozostałe 15% (walidacje warunkowe, zagnieżdżone JSON, enum-y) wymaga ręcznego override w pliku `clip/TOS/tos_api_schemas_overrides.json` — generator merge'uje overrides z auto-detected.

**Wpięcie w pipeline deploy:** w `generate_screens_from_description.py` (lub jako osobny krok przed deploy SQL) uruchamiamy `generate_api_schemas.py`, wynik (`tos_api_schemas.json`) konwertujemy na blok INSERT-ów w `tos_tables.sql`:

```python
# fragment generate_api_schemas.py — generowanie INSERT-ów
inserts = "\n".join(
    f"""INSERT INTO public.tos_api_schema (procedure_name, summary, description, tags, request_schema, response_schema, examples)
VALUES ('{proc}', $$tag${data['summary']}$$tag$, $$tag${data['description']}$$tag$,
        ARRAY[{','.join(repr(t) for t in data['tags'])}]::TEXT[],
        $$tag${json.dumps(data['request_schema'])}$$tag$::jsonb,
        $$tag${json.dumps(data['response_schema'])}$$tag$::jsonb,
        $$tag${json.dumps(data.get('examples', {}))}$$tag$::jsonb)
ON CONFLICT (procedure_name) DO UPDATE SET
    summary = EXCLUDED.summary,
    description = EXCLUDED.description,
    tags = EXCLUDED.tags,
    request_schema = EXCLUDED.request_schema,
    response_schema = EXCLUDED.response_schema,
    examples = EXCLUDED.examples,
    updated_at = now();"""
    for proc, data in schemas.items()
)
```

#### 15.4.2.4. Przykład response z `tos_get_openapi_spec` (skrócony)

Po wywołaniu `POST /integration/tos_get_openapi_spec` z body `{}` i nagłówkiem `token-mer: <jwt>` Pinquark zwraca:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Pinquark TOS — Custom Integrations API",
    "version": "1.0.0",
    "description": "Auto-generated OpenAPI spec for active con_integration entries."
  },
  "servers": [
    {"url": "https://clip-malaszewicze.pinquark.app"}
  ],
  "components": {
    "securitySchemes": {
      "TokenMer": {"type": "apiKey", "in": "header", "name": "token-mer"}
    }
  },
  "tags": [
    {"name": "Awizacje"}, {"name": "Bramy"}, {"name": "Operacje"},
    {"name": "Polling"}, {"name": "Status"}
  ],
  "paths": {
    "/integration/tos_notification_rail_save": {
      "post": {
        "operationId": "tos_notification_rail_save",
        "summary": "Awizacja kolejowa - zapisz",
        "description": "Tworzy awizację kolejową (AWK) z wagonami i kontenerami...",
        "tags": ["Awizacje"],
        "deprecated": false,
        "security": [{"TokenMer": []}],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["tos_train_no", "tos_doc_planned_arrival", "carrier_code"],
                "properties": {
                  "tos_train_no":             {"type": "string"},
                  "tos_doc_planned_arrival":  {"type": "string", "format": "date-time"},
                  "carrier_code":             {"type": "string"},
                  "TOS_DOC_POL":              {"type": "string"},
                  "TOS_DOC_POD":              {"type": "string"},
                  "TOS_EDI_PARTNER_CODES":    {"type": "string", "nullable": true,
                                                "description": "CSV kodów partnerów EDI"}
                }
              },
              "examples": {
                "default": {
                  "value": {
                    "tos_train_no": "MET-204",
                    "tos_doc_planned_arrival": "2026-04-20T14:30:00Z",
                    "carrier_code": "METRANS"
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status":  {"type": "string", "enum": ["OK", "ERROR"]},
                    "doc_id":  {"type": "integer"},
                    "message": {"type": "string"}
                  }
                }
              }
            }
          },
          "401": {"description": "Unauthorized — brak/nieprawidłowy token-mer"},
          "404": {"description": "Integration not found / inactive"},
          "500": {"description": "Procedure raised exception"}
        }
      }
    },
    "/integration/tos_get_events_since": {
      "post": {
        "operationId": "tos_get_events_since",
        "summary": "Pobierz nowe zdarzenia od kursora",
        "description": "Polling tos_audit_log od ostatniego last_audit_id. Główne źródło outbound EDI.",
        "tags": ["Polling"],
        "security": [{"TokenMer": []}],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["last_audit_id"],
                "properties": {
                  "last_audit_id": {"type": "integer", "minimum": 0},
                  "limit":         {"type": "integer", "minimum": 1, "maximum": 5000, "default": 1000},
                  "modules":       {"type": "string", "nullable": true,
                                     "description": "Opcjonalny filtr CSV po module"}
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {"type": "string"},
                    "events": {"type": "array", "items": {"type": "object"}},
                    "max_id": {"type": "integer"},
                    "count":  {"type": "integer"}
                  }
                }
              }
            }
          }
        }
      }
    }
    // ... 38 kolejnych endpointów
  }
}
```

OIP konektor `rest-api` parsuje to bezpośrednio przez `OpenAPIDiscovery._parse_spec(...)` (sekcja 15.4.1) i rejestruje 40 akcji w action registry konta — z pełnym typowaniem, opisami, tagami i przykładami. Dashboard pokazuje je użytkownikowi do potwierdzenia importu (mockup z kroku 2 sekcji 15.3).

#### 15.4.2.5. Bezpieczeństwo

- **Endpoint wymaga `token-mer`** (ten sam co dla pozostałych integracji TOS, jeden globalny — sekcja 14.5). Bez tokenu zwraca 401, jak każda inna integracja Serwis. Nie ma trybu anonimowego — spec ujawnia strukturę całego API biznesowego TOS, nie chcemy żeby leciał publicznie.
- **OIP discovery przekazuje token z accountu** automatycznie (zdefiniowany w `discovery.spec_auth_headers.token-mer`).
- **Spec NIE zawiera danych biznesowych** — tylko nazwy pól, typy, opisy. Sample examples w `tos_api_schema.examples` powinny być sanitized (mock data, nie dane z produkcji).
- **Rate limit** — endpoint jest tani (kilkadziesiąt SELECT-ów), ale i tak ma standardowy `limit_per_minute` z `con_integration` (default 600). Discovery cache'uje wynik na `refresh_ttl_seconds` (default 1h) — produkcyjnie hit raz na godzinę.

#### 15.4.2.6. Multi-system reuse

Ten sam wzorzec działa dla **każdego systemu Pinquark**, nie tylko TOS:

- WMS — procedura `wms_get_openapi_spec` + tabela `wms_api_schema` + analogiczny `con_integration.name LIKE 'wms_%'` filter
- TMS — procedura `tms_get_openapi_spec` + tabela `tms_api_schema`
- Dowolny system z custom integrations — analogicznie

Konektor `rest-api` w OIP nie wie nic o Pinquark — widzi tylko endpoint zwracający OpenAPI 3.1, czyli **nadal jest 100% generyczny**. Per-system specyfika siedzi po stronie systemu, nie konektora.

### 15.5. Schemat request/response

#### `rest.call` — request

```json
{
  "account": "clip-malaszewicze",
  "endpoint": "tos_notification_rail_save",
  "method": "POST",
  "body": {
    "tos_train_no": "MET-204",
    "tos_doc_planned_arrival": "2026-04-20T14:30:00Z",
    "carrier_code": "METRANS"
  },
  "headers": {},
  "query_params": {},
  "timeout_s": 30
}
```

Alternatywnie z `named_action` (rozwiązywany z action registry konta):

```json
{
  "account": "clip-malaszewicze",
  "named_action": "awk.create",
  "body": {
    "tos_train_no": "MET-204",
    "tos_doc_planned_arrival": "2026-04-20T14:30:00Z"
  }
}
```

#### `rest.call` — response

```json
{
  "status": "success",
  "http_status": 200,
  "response_status": "OK",
  "message": "AWK created",
  "data": { "doc_id": 12345 },
  "raw_response": { ... },
  "elapsed_ms": 142,
  "account": "clip-malaszewicze",
  "endpoint": "tos_notification_rail_save"
}
```

#### `rest.poll` — request

```json
{
  "account": "clip-malaszewicze",
  "endpoint": "tos_get_events_since",
  "cursor_field": "last_audit_id",
  "cursor_response_field": "max_id",
  "items_field": "events",
  "limit": 1000,
  "method": "POST"
}
```

#### `rest.batch` — request

```json
{
  "account": "clip-malaszewicze",
  "calls": [
    { "named_action": "train.add_wagon", "body": { "wagon_number": "31514789012-3", "sequence_no": 1 } },
    { "named_action": "train.add_wagon", "body": { "wagon_number": "31514789013-1", "sequence_no": 2 } },
    { "named_action": "train.add_wagon", "body": { "wagon_number": "31514789014-9", "sequence_no": 3 } }
  ],
  "parallel": false,
  "stop_on_error": true
}
```

### 15.6. Strategie autentykacji (`auth_provider.py`)

Konektor obsługuje wiele strategii auth, konfigurowalnych per konto:

| `auth.type` | Headery wysyłane | Użycie |
|---|---|---|
| `bearer` | `Authorization: Bearer {token}` | Standardowe API z tokenem stałym |
| `bearer_with_custom_headers` | `Authorization: Bearer {token}` + dowolne custom headery (np. `token-mer`) | **Pinquark TOS** |
| `basic` | `Authorization: Basic {base64(user:pass)}` | Legacy API, SAP |
| `api_key_header` | `{header_name}: {api_key}` (np. `X-API-Key: abc123`) | Proste API z kluczem |
| `api_key_query` | `?{param_name}={api_key}` | API z kluczem w query |
| `oauth2_client_credentials` | `Authorization: Bearer {auto_refreshed_token}` (auto-refresh z `token_url`) | OAuth2 M2M (Navis N4, Dynamics 365) |
| `oauth2_authorization_code` | `Authorization: Bearer {auto_refreshed_token}` (refresh z `refresh_token`) | OAuth2 z user consent (Allegro, Shopify) |
| `none` | Brak | Publiczne API, wewnętrzne mikroserwisy |

### 15.7. Profile response mapping (`response_parser.py`)

Wbudowane profile + możliwość custom mapping per konto:

```yaml
# config/profiles/pinquark.yaml
name: pinquark
description: "Pinquark platform response format"
status_field: status
status_ok_values: ["OK"]
status_error_values: ["ERROR"]
message_field: message
data_field: data
error_code_field: error_code
```

```yaml
# config/profiles/generic.yaml
name: generic
description: "Standard HTTP — sukces = 2xx, error = 4xx/5xx"
use_http_status: true
data_field: null              # cały body to data
```

```yaml
# config/profiles/sap.yaml
name: sap
description: "SAP OData response format"
status_field: d.Status
data_field: d
error_field: error.message.value
```

### 15.8. Klient REST (`rest_client.py`)

```python
class RestClient:
    """Generyczny async HTTP client z auth, retry, response parsing."""

    def __init__(
        self,
        account: AccountConfig,
        auth_provider: AuthProvider,
        response_parser: ResponseParser,
    ):
        self.account = account
        self.auth_provider = auth_provider
        self.response_parser = response_parser
        self._client: httpx.AsyncClient | None = None

    async def call(
        self,
        endpoint: str,
        method: str = "POST",
        body: dict | None = None,
        headers: dict | None = None,
        query_params: dict | None = None,
        timeout_s: int | None = None,
    ) -> RestCallResponse:
        """Wykonaj request REST z auth, retry i response parsing."""
        url = f"{self.account.base_url}{self.account.path_prefix}/{endpoint}"
        auth_headers = await self.auth_provider.get_headers()
        merged_headers = {**auth_headers, **(headers or {})}

        response = await self._request_with_retry(
            method=method,
            url=url,
            json=body,
            headers=merged_headers,
            params=query_params,
            timeout=timeout_s or self.account.timeouts.read_s,
        )

        return self.response_parser.parse(response, self.account)

    async def call_named(self, named_action: str, body: dict | None = None) -> RestCallResponse:
        """Rozwiąż named_action z action_registry i wywołaj."""
        action_def = self.account.action_registry.get(named_action)
        if not action_def:
            raise RestClientError(f"Unknown action '{named_action}' in account '{self.account.name}'")
        return await self.call(
            endpoint=action_def.endpoint,
            method=action_def.method or self.account.default_method,
            body=body,
        )
```

### 15.9. Wpływ na workflow YAML

Workflowy z sekcji 3.x zmieniają się minimalnie — zamiast `connector: pinquark-tos` używają `connector: rest-api` z account:

**Przed (dedykowany):**
```yaml
- id: create-awk
  type: action
  connector: pinquark-tos
  account: clip-malaszewicze
  action: awk.create
  input:
    tos_train_no: "{{ parse-edi.payload.train_no }}"
```

**Po (generyczny z named_action):**
```yaml
- id: create-awk
  type: action
  connector: rest-api
  account: clip-malaszewicze
  action: rest.call
  input:
    named_action: awk.create
    body:
      tos_train_no: "{{ parse-edi.payload.train_no }}"
```

**Po (generyczny z surowym endpoint):**
```yaml
- id: create-awk
  type: action
  connector: rest-api
  account: clip-malaszewicze
  action: rest.call
  input:
    endpoint: tos_notification_rail_save
    body:
      tos_train_no: "{{ parse-edi.payload.train_no }}"
```

Polling outbound (sekcja 14.6.4) z `rest.poll`:
```yaml
- id: poll_tos
  type: connector.action
  connector: rest-api
  account: clip-malaszewicze
  action: rest.poll
  input:
    named_action: events.poll
    cursor_field: last_audit_id
    cursor_response_field: max_id
    items_field: events
    limit: 1000
```

### 15.10. Co to zmienia w pozostałych zadaniach

| Zadanie | Zmiana |
|---|---|
| **Zadanie 1** (konektor `edifact`) | **Bez zmian** — parser/builder EDIFACT + nowe komunikaty niezależne od tego jak łączymy się z TOS |
| **Zadanie 2** (konektor `pinquark-tos`) | **Zastąpione** przez konektor `rest-api` + konto `clip-malaszewicze` w `accounts.yaml` |
| **Zadanie 3** (workflow templates) | Minimalna zmiana: `connector: rest-api` + `action: rest.call` zamiast `connector: pinquark-tos` + `action: awk.create`. Semantycznie identyczne dzięki `named_action` |
| **Zadanie 4** (README) | Rozszerzony o sekcję "Konfiguracja konta REST API dla Pinquark TOS" |
| **Zadanie 5** (Verification Agent) | Bez zmian — testuje generyczny `rest.call` z kontem TOS |
| **Sekcja 14.5** (`setup_tos_integrations.sql`) | **Bez zmian** — skrypt po stronie TOS jest taki sam |
| **Sekcja 14.6** (pull pattern) | Bez zmian koncepcyjnych, workflow używa `rest.poll` zamiast `pinquark-tos.tos_get_events_since` |

### 15.11. Roadmapa (zaktualizowana ~10 dni roboczych)

| Dzień | Praca |
|---|---|
| 1 | Konektor `rest-api` — `connector.yaml` (z `config_schema`, `auth_types`, `action_fields`, `output_fields`, **`discovery.mode: probe|explicit`**), `rest_client.py`, `auth_provider.py` (Bearer, Basic, OAuth2, custom headers), `response_parser.py` z profilami (pinquark, generic, sap), `account_manager.py`, health check |
| 2 | Konektor `rest-api` — `routes.py` (`rest.call`, `rest.poll`, `rest.batch`, `rest.discover`), `openapi_discovery.py` z **dwoma trybami**: A) probe `/openapi.json|/swagger.json|/api-docs` GET, B) explicit `POST /integration/<name>` z config konta (kluczowe dla Pinquark — sekcja 15.4.1, 15.4.2). Parser endpoints, generowanie aliasów, `main.py`, Dockerfile, docker-compose |
| 3 | Konektor `rest-api` — testy unit (>80%), `credential_validation` endpoint, integracja z `oip-internal` partner registry, smoke test z Pinquark TOS FastAPI spec |
| 4 | Parser + Builder EDIFACT (`pydifact`, `edifact_parser.py`, `edifact_builder.py`) + round-trip testy + obsługa SMDG profili (1.5/2.0) i wersji (D.95B/D.00B) jako parametry konta |
| 5 | COPRAR + COPARN — schemas + routes + builder + parser + fixture files |
| 6 | COHAOR + COARRI + IFTMIN rozszerzony — schemas + routes + builder + parser |
| 7 | IFTSTA (mapping statusów TOS → SMDG codes) + APERAK + CONTRL + auto-response logic |
| 8 | Workflow templates partner-agnostyczne (zaktualizowane na `connector: rest-api`): `00_tos_poll_events.yaml` + `01_coprar_inbound.yaml` + `02_codeco_outbound.yaml` + `03_coarri_outbound.yaml` + `04_iftsta_outbound.yaml` + `05_coparn_inbound.yaml` |
| 9 | Workflow templates: `06–12` + `setup_tos_integrations.sql` jako artefakt konektora `rest-api` (w `docs/examples/pinquark-tos/`) |
| 10 | README (konfiguracja kont REST API, pull pattern, onboarding partnera), Verification Agent, CHANGELOG, code review |

### 15.12. Konsekwencje dla OIP jako platformy

Konektor `rest-api` z auto-discovery staje się **jednym z fundamentalnych konektorów OIP** — obok `ftp-sftp`, `email-client` i `edifact`. Każdy nowy system, który ma REST API, można podłączyć **bez pisania kodu i bez agenta** — wystarczy:

1. W dashboardzie OIP: wpisać URL + credentials.
2. Kliknąć "Odkryj endpointy" → konektor sam pobiera OpenAPI spec.
3. Wybrać endpointy do zaimportowania → gotowe.
4. Użyć w workflow builder z dropdown-em odkrytych akcji.

**Dla systemów bez OpenAPI spec** (legacy, on-premise ERP) — ręczne dodanie endpointów w formularzu (nazwa, ścieżka, metoda). Bez edycji YAML-i, bez wdrożeń, bez programisty.

To oznacza że OIP zyskuje zdolność podłączenia dowolnego z dziesiątek systemów terminali (Navis N4, TOPS Expert, Jade Master Terminal, Tideworks), ERP (SAP, Dynamics, Comarch), TMS (Transporeon, CargoWise) i innych — **bez implementacji nowego konektora per system**, jedynie przez konfigurację w dashboardzie.

**Porównanie UX:**

| Dzisiaj (dedykowany konektor) | Po zmianach (generyczny `rest-api`) |
|---|---|
| Programista pisze konektor (~3 dni) | Użytkownik klika w dashboard (~5 min) |
| Deploy nowej wersji OIP | Zero deploya |
| 1 konektor = 1 system | 1 konektor = ∞ systemów |
| Aktualizacja API = nowa wersja konektora | Aktualizacja API = klik "Odśwież endpointy" |

---

**Powodzenia. Zaczynaj od konektora `rest-api` (dzień 1–3) i Zadania 1.1 (parser raw EDI, dzień 4) równolegle — to najbardziej fundamentalne komponenty, reszta od nich zależy.**
