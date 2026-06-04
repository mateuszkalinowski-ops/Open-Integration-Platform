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
