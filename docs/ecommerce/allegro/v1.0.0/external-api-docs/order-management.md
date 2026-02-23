Zarządzanie zgłoszeniami ofert do kampanii - Allegro Developer Portal - baza wiedzy o Allegro REST API

Obsługa zgłoszeń ofert do kampanii i oznaczeń Allegro

Jak zgłosić ofertę do kampanii, programów specjalnych i oznaczeń Allegro

Allegro Ceny - jak zarządzać zgodami na uczestnictwo w programie

AlleObniżka - jak zarządzać udziałem w programie

Lista zasobów

# Zarządzanie zgłoszeniami ofert do kampanii

Opis procesów dotyczących zarządzania zgłoszeniami ofert do kampanii, programów specjalnych i oznaczeń Allegro.

## Jak przypisać ofertę do kampanii

Jeżeli masz konto firmowe, możesz zgłaszać swoje oferty do różnych akcji promocyjnych, dzięki temu wyświetlimy w nich specjalne oznaczenia.

Aby wziąć udział w kampanii, musisz [spełniać warunki](https://help.allegro.com/pl/sell/a/poznaj-strefe-okazji-i-wybrane-akcje-promocyjne-na-allegro-b2OwBoY7WU0) i zaakceptować regulamin dostępny w zasobie [GET /sale/badge-campaigns](https://developer.allegro.pl/documentation/#tag/Badge-campaigns/operation/badgeCampaigns_get_all).

### Obsługa zgłoszeń ofert do kampanii i oznaczeń Allegro

Możesz dodać ofertę do kampanii sezonowych i cyklicznych takich jak:

- [Allegro Days](https://help.allegro.com/pl/sell/a/czym-jest-akcja-allegro-days-i-jak-wziac-w-niej-udzial-lL5oexbyyfM).
- Black Weeks,
- Smart! Week,

Więcej na temat kampanii dowiesz się w artykule o [Strefie okazji](https://help.allegro.com/pl/campaigns/pl).

Pamiętaj, że wszystkie żądania musisz wykonywać jako zautoryzowany sprzedawca, który chce dodać oznaczenia do swoich ofert.

### Jak zgłosić ofertę do kampanii, programów specjalnych i oznaczeń Allegro

#### Lista dostępnych kampanii

Za pomocą [GET /sale/badge-campaigns](https://developer.allegro.pl/documentation/#operation/badgeCampaigns_get_all) pobierzesz listę dostępnych kampanii, które możesz przypisać do ofert.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/badge-campaigns&marketplace.id=allegro-pl' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
   {
   "badgeCampaigns": [
   {
     "id": "BLACK_WEEKS_2025_PL",    // identyfikator kampanii
     "name": "Black Weeks 2025",     // nazwa kampanii
     "marketplace": {
         "id": "allegro-pl"    // identyfikator serwisu (np. allegro-pl, allegro-cz, allegro-sk)
     },
     "type": "DISCOUNT",     // typ kampanii, obecnie są dostępne trzy typy: STANDARD - dodamy do oferty oznaczenie na liście ofert; DISCOUNT - zmienimy cenę w ofercie, a na liście ofert obok ceny promocyjnej wyświetlimy najniższą cenę oferty z ostatnich 30 dni jako cenę przekreśloną; SOURCING - zmienimy cenę w ofercie, nie dodamy oznaczenia widocznego na platformie, ale otrzymasz bonusy wynikające z regulaminu konkretnej kampanii, np. niższe prowizje od sprzedaży produktu.
     "eligibility": {    // czy kampania jest dostępna dla zautoryzowanego użytkownika
       "eligible": true,
       "refusalReasons": []    // dlaczego użytkownik nie kwalifikuje się do udziału w danej kampanii
     },
     "application": {    // okres przyjmowania zgłoszeń ofert do kampanii kanałem API. Może różnić się od okresu widoczności w zakładce Kampanie i programy / Może różnić się od okresu przyjmowania zgłoszeń z poziomu zakładki Kampanie i programy.
       "type": "ALWAYS",    // czas trwania, dostępne jest 5 wartości:  ALWAYS (zawsze), SINCE (od danego dnia), UNTIL (do danego dnia), WITHIN (przedział czasowy), NEVER (nigdy)
       "from": null,
       "to": null
     },
     "publication": {    // okres trwania oznaczenia
       "type": "ALWAYS",    // czas trwania dostępne jest 5 wartości: ALWAYS (zawsze), SINCE (od danego dnia), UNTIL (do danego dnia), WITHIN (przedział czasowy), NEVER (nigdy)
       "from": null,
       "to": null
     },
     "visibility": {    // okres, w którym kampania jest widoczna w narzędziach do zarządzania kampaniami na API (nie jest równy widoczności oznaczenia kampanii na portalu). Może różnić się od okresu widoczności w Moim Allegro. Zakres tych dat pozwala stwierdzić, jak długo informacje o kampanii będą dostępne na platformie
       "type": "ALWAYS",    // czas trwania dostępne jest 5 wartości:  ALWAYS (zawsze), SINCE (od danego dnia), UNTIL (do danego dnia), WITHIN (przedział czasowy), NEVER (nigdy)
       "from": null,
       "to": null
     },
     "regulationsLink": "https://allegro.pl/regulaminy/regulamin-strefy-okazji-R8l59vW7GfL",    // link do regulaminu kampanii
     "stockReservationIsRequired": false    // informacja, czy kampania wymaga zadeklarowania dedykowanej ilości
   },
   …
   ]
 }
```

#### Zgłoś ofertę do kampanii

Za pomocą [POST /sale/badges](https://developer.allegro.pl/documentation/#operation/postBadges) zgłosisz ofertę do wybranej kampanii.

Zgłoszenia, które nie spełniają wymagań danej kampanii zostaną przez nas odrzucone.

Cena zwracana w polu "prices.market" jest obliczana przez Serwis Allegro. Obliczamy najniższą cenę oferty z 30 dni przed obniżką, którą wyświetlamy jako przekreśloną.

Przykładowy request:

```
  curl -X POST \
  'https://api.allegro.pl/sale/badges' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
   "campaign": {
       "id":"BLACK_WEEKS_2025_PL"    // wymagane, identyfikator kampanii, jaką chcesz dodać do oferty - zgodnie z badgeCampaigns.id otrzymanym przez GET /sale/badge-campaigns
   },
   "offer": {
       "id":"6206378062"    // wymagane, identyfikator oferty, do jakiej chcesz dodać kampanię
   },
   "prices": {    // wymagane dla kampanii typu DISCOUNT i SOURCING, cena promocyjna oferty jaka ma być widoczna na ofercie
       "bargain": {    
           "amount":"180.00",
           "currency":"PLN"
       }
   },
   "purchaseConstraints": {    // opcjonalne - ograniczenia zakupowe na czas udziału w kampanii
       "limit": {
           "perUser": {
               "maxItems": 1    // ograniczenie liczby sztuk dostępnych dla pojedynczego użytkownika; tylko dla kampanii typu DISCOUNT i SOURCING
           }
       }
   },
   "declaredStock": {    // opcjonalne - musi być podane w zależności od flagi „stockReservationIsRequired" - w przypadku wartości true „declaredStock" jest wymagany, w przypadku false musi być null
       "quantity": 10
   }
 }'
```

Przykładowy response:

```
 {
  "id":"8a457b8f-627d-43cf-8806-f06f8d13c306",    // identyfikator zgłoszenia oferty do kampanii
  "createdAt":"2025-06-26T10:22:35.225Z",    // data utworzenia zgłoszenia
  "updatedAt":"2025-06-26T10:22:35.225Z",    // data ostatniej zmiany w zgłoszeniu
  "campaign": {
    "id":"BLACK_WEEKS_2025_PL"    // identyfikator kampanii
  },
  "offer": {
    "id":"6206378062"    //  identyfikator oferty, którą chcesz dodać do kampanii
  },
  "prices": {    // informacje o cenie, jaka ma być widoczna na ofercie
    "bargain": {    // cena promocyjna oferty
      "amount":"180.00",
      "currency":"PLN"
    },
    "market": {    // wyliczona przez nas najniższa cena sprzedaży w ofercie z ostatnich 30 dni. Wyświetlimy ją jako przekreśloną na liście ofert
      "amount":"200.00",
      "currency":"PLN"
    }
  },
  "purchaseConstraints": {    // opcjonalne - ograniczenia zakupowe na czas udziału w kampanii
    "limit": {
      "perUser": {
        "maxItems":"1"    // ograniczenie liczby sztuk dostępnych dla pojedynczego użytkownika
      }
    }
  },
  "campaignStock": {    // opcjonalne - stock zadeklarowany w requeście
     "quantity": 10
  },
  "process": {
    "status":"REQUESTED",    // status zgłoszenia, dostępne są 3 wartości: REQUESTED (wniosek czeka na przetworzenie), PROCESSED (wniosek został przetworzony - od tego momentu możesz sprawdzić status przypisana oznaczenia do oferty zasobem GET sale/badges), DECLINED (wniosek został odrzucony)
    "rejectionReasons": []    // powód odrzucenia zgłoszenia
  }
 }
```

#### Pobierz dane zgłoszenie

Za pomocą [GET /sale/badge-applications/{applicationId}](https://developer.allegro.pl/documentation/#operation/badgeApplications_get_one) pobierzesz konkretne zgłoszenie oferty do kampanii i sprawdzisz jego status.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/badge-applications/8a457b8f-627d-43cf-8806-f06f8d13c306' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
 {
   "id": "8a457b8f-627d-43cf-8806-f06f8d13c306",    // identyfikator zgłoszenia oferty do kampanii
   "createdAt": "2025-06-26T10:22:35.225Z",    // data utworzenia zgłoszenia
   "updatedAt": "2025-06-26T10:22:35.225Z",    // data ostatniej zmiany w zgłoszeniu
   "campaign": {
     "id": "BLACK_WEEKS_2025_PL"    // identyfikator kampanii
   },
   "offer": {
     "id": "6206378062"    //  identyfikator oferty, którą chcesz dodać do kampanii
   },
   "prices": {    // informacje o cenie, jaka ma być widoczna na ofercie
     "bargain": {    // cena promocyjna oferty
       "amount": "180.00",
       "currency": "PLN"
     },
     "market": {    // wyliczona przez nas najniższa cena sprzedaży w ofercie z ostatnich 30 dni. Wyświetlimy ją jako przekreśloną na liście ofert.
       "amount": "200.00",
       "currency": "USD"
     },
   "campaignStock": {    // opcjonalne - stock zadeklarowany w [POST] /sale/badges
     "quantity": 10
   },
   "process": {
     "status": "DECLINED",    // status zgłoszenia, dostępne są 3 wartości: REQUESTED (wniosek czeka na przetworzenie), PROCESSED (wniosek został przetworzony - od tego momentu możesz sprawdzić status przypisana oznaczenia do oferty zasobem GET sale/badges), DECLINED (wniosek został odrzucony)
     "rejectionReasons": [    // informacja na temat powodów odrzucenia zgłoszenia
       {
         "code": "BB5",    // powód odrzucenia zgłoszenia
         "messages": [
           {
             "text": "Currency is not equal to ‘PLN’"
             "link": null
           }
         ] 
       }
     ]
   }
 }
```

#### Pobierz swoje zgłoszenia

Za pomocą [GET /sale/badge-applications](https://developer.allegro.pl/documentation/#operation/badgeApplications_get_all) pobierzesz wszystkie zgłoszenia ofert do kampanii.

Przy wywołaniu musisz podać jeden z parametrów:

- offer.id - identyfikator oferty.
- campaign.id - identyfikator kampanii,

Aby dostosować listę wyszukiwania do swoich potrzeb, możesz skorzystać z parametrów:

limit by określić liczbę zgłoszeń na liście (przyjmuje wartości od 1 do 1000, domyślnie 50),

offset by wskazać miejsce, od którego chcesz pobrać kolejną porcję danych (przyjmuje wartości od 0 do nieskończoności, domyślnie 0).

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/badge-applications?campaign.id=BLACK_WEEKS_2025_PL' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
 {
  "badgeApplications": [    // lista zgłoszeń ofert do danego typu kampanii 
  {
   "id": "8a457b8f-627d-43cf-8806-f06f8d13c306",
   "createdAt": "2025-06-26T10:22:35.225Z",
   "updatedAt": "2025-06-26T10:22:35.225Z",
   "campaign": {
       "id": "BLACK_WEEKS_2025_PL"
       },
   "offer": {
       "id": "6206378062"
       },
   "prices": {
       "bargain": {
         "amount": "180.00",
         "currency": "PLN"
       },
       "market": {
         "amount": "200.00",
         "currency": "PLN"
       }
     },
   "campaignStock": {    // opcjonalne - stock zadeklarowany w [POST] /sale/badges
       "quantity": 10
     },     
   "process": {
       "status": "DECLINED",
       "rejectionReasons": [
          {
           "code": "BA1",
           "messages": [
             {
              "text": "Badge already exists"
             },
             {
              "text": "check terms & conditions",
              "link": "http://allegro.pl/xyz"
             }
           ]
          }
        ]
      }
    }
  ]
}
```

#### Kampanie przypisane do ofert

Za pomocą [GET /sale/badges](https://developer.allegro.pl/documentation/#operation/getBadges) sprawdzisz przypisane oznaczenia do swoich ofert.

Aby dostosować listę wyszukiwania do swoich potrzeb, możesz skorzystać z parametrów:

marketplace.id by wskazać, z którego rynku kampanie dla swoich ofert chcesz uzyskać, jest to parametr obowiązkowy,

limit by określić liczbę zgłoszeń na liście (przyjmuje wartości od 1 do 1000, domyślnie 50),

offset by wskazać miejsce, od którego chcesz pobrać kolejną porcję danych (przyjmuje wartości od 0 do nieskończoności, domyślnie 0).

Tym zasobem możesz sprawdzić przypisane oznaczenia do danej oferty, wystarczy, że wywołasz GET /sale/badges?marketplace.id=allegro-pl&offer.id={offerId}.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/badges?marketplace.id=allegro-pl' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
   "badges": [
     {
       "offer": {
         "id": "6206378062"
       },
       "campaign": {
         "id": "BLACK_WEEKS_2025_PL",
         "name": "Black Weeks 2025"
       },
       "publication": {
         "type": "ALWAYS"
       },
       "prices": {    // informacja cenowa dotycząca oferowanego przedmiotu, zwracana tylko dla kampanii wymagających podania ceny rynkowej na etapie zgłoszenia
         "market": {    // wyliczona przez nas najniższa cena sprzedaży w ofercie z ostatnich 30 dni. Wyświetlimy ją jako przekreśloną na liście ofert.
           "amount": "19.99",
           "currency": "PLN"
         },
         "subsidy": null, 
       "process": {
         "status": "ACTIVE",    // status oznaczenia, dostępne wartości: IN_VERIFICATION (wniosek jest w trakcie weryfikacji), WAITING_FOR_PUBLICATION (oznaczenie jest w trakcie publikacji w serwisie), ACTIVE (oznaczenie jest aktywne i widoczne w serwisie), FINISHED (minął czas trwania oferty w kampanii lub administrator zakończył udział oferty w kampanii), DECLINED (oznaczenie zostało odrzucone i nie pojawi się w serwisie
         "rejectionReasons": []
       },
       "campaignStock": {     // opcjonalne - stock zadeklarowany lub zatwierdzony
         "quantity": 10
       }
     }
   ]
 }
```

#### Zmiana ceny i zakończenie oznaczenia

##### Zmiana ceny oferty w kampanii

Za pomocą [PATCH /sale/badges/offers/{offerId}/campaigns/{campaignId}](https://developer.allegro.pl/documentation/#operation/patchBadge) zlecisz operację zmiany ceny oferty w kampanii.

Przykładowy request:

```
  curl -X PATCH \
  'https://api.allegro.pl/sale/badges/offers/12345678/campaigns/BLACK_WEEKS_2025_PL' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
      "prices": {
        "bargain": {
          "value": {
            "amount": "9.99",
            "currency": "PLN"
          }
        }
      }
   }'
```

Przykładowy response:

```
{
  "id": "154179f0-ed4c-4b84-9260-302d2dec3801"    // identyfikator operacji zmiany ceny oferty w kampanii
}
```

##### Zakończenie oznaczenia oferty w kampanii

Za pomocą [PATCH /sale/badges/offers/{offerId}/campaigns/{campaignId}](https://developer.allegro.pl/documentation/#operation/patchBadge) zlecisz też operację zakończenia oznaczenia oferty w kampanii.

Przykładowy request:

```
curl -X PATCH \
    'https://api.allegro.pl/sale/badges/offers/12345678/campaigns/BLACK_WEEKS_2025_PL' \
    -H 'Authorization: Bearer {token}' \
    -H 'Content-Type: application/vnd.allegro.public.v1+json' \
    -d '{
        "process": {
          "status": "FINISHED"
        }
    }'
```

Przykładowy response:

```
{
  "id": "154179f0-ed4c-4b84-9260-302d2dec3801"    // identyfikator operacji zakończenia oznaczenia oferty w kampanii
}
```

##### Sprawdzenie statusu operacji

Za pomocą [GET /sale/badge-operations/{operationId}](https://developer.allegro.pl/documentation/#operation/badgeOperations_get_one) sprawdzisz status wykonania operacji zmiany ceny lub zakończenia oznaczenia.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/badge-operations/154179f0-ed4c-4b84-9260-302d2dec3801' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
    "id": "154179f0-ed4c-4b84-9260-302d2dec3801",
    "createdAt": "2025-05-16T12:49:17.347Z",
    "updatedAt": "2025-05-16T12:49:17.530Z",
    "campaign": {
      "id": "BLACK_WEEKS_2025_PL"
    },
    "offer": {
      "id": "12345678"
    },
    "process": {
      "status": "PROCESSED",
      "rejectionReasons": []
    }
  }
```

#### Jak testować kampanie

W [środowisku testowym](https://developer.allegro.pl/tutorials/informacje-podstawowe-b21569boAI1#srodowisko-testowe) skonfigurowaliśmy kampanie aby można było samodzielnie sprawdzić proces:

’SANDBOX_TEST_CAMPAIGN’ - kampania typu DISCOUNT bez deklaracji stocku,

’CAMPAIGN_WITH_STOCK_API_TEST’ - kampania typu DISCOUNT z deklaracją stock.

### Allegro Ceny - jak zarządzać zgodami na uczestnictwo w programie

#### Jak pobrać aktualne zgody dla oferty

Użyj [GET /sale/allegro-prices-offer-consents/{offerId}](https://developer.allegro.pl/documentation/#operation/getAllegroPricesConsentForOffer), gdzie jako offerId wskaż numer konkretnej oferty.

Przykładowy request:

```
 curl -X GET \
 'https://api.allegro.pl/sale/allegro-prices-offer-consents/993723618' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \
 -H 'Content-Type: application/vnd.allegro.public.v1+json' 
```

Przykładowy response:

```
 {
  "status": "ALLOWED",    // status zgody dla serwisu bazowego oferty
  "additionalMarketplaces": {    // status zgody dla serwisów dodatkowych
      "allegro-cz": {
          "status": "ALLOWED"
      },
      "allegro-xy": {
          "status": "DENIED"
      }
  }
 }
```

#### Jak zaktualizować zgodę dla oferty

Zrobisz to za pomocą [PUT /sale/allegro-prices-offer-consents/{offerId}](https://developer.allegro.pl/documentation/#operation/updateAllegroPricesConsentForOffer). Jako offerId wskaż konkretny numer oferty.

Zgodę na uczestnictwo w programie Allegro Ceny możesz wyrazić dla serwisu bazowego oferty lub/i serwisów dodatkowych.

Pamiętaj:

- jedno z pól - “status” lub “additionalMarketplaces” musisz zawsze przekazać w wywołaniu.
- jeżeli przekażesz pole “additionalMarketplaces” to musisz określić w nim status zgody dla minimum jednego serwisu dodatkowego;
- w polu “additionalMarketplaces” określisz status zgody dla serwisów dodatkowych;
- pole “status” jest opcjonalne;
- w polu “status” przekażesz status zgody tylko dla serwisu bazowego oferty;

Przykładowy request:

```
 curl -X PUT \
 'https://api.allegro.pl/sale/allegro-prices-offer-consents/993723618'
 -H 'Accept: application/vnd.allegro.public.v1+json' \
 -H 'Content-Type: application/vnd.allegro.public.v1+json' \
 -d '{
  "status": "ALLOWED",    // status zgody dla serwisu bazowego oferty
  "additionalMarketplaces": {    // status zgody dla serwisów dodatkowych
      "allegro-cz": {
          "status": "ALLOWED"
      },
      "allegro-xy": {
          "status": "DENIED"
      }
  }
 }'
```

Przykładowy response:

```
 {
  "status": "ALLOWED",    // status zgody dla serwisu bazowego oferty
  "additionalMarketplaces": {    // status zgody dla serwisów dodatkowych
      "allegro-cz": {
          "status": "ALLOWED"
      },
      "allegro-xy": {
          "status": "DENIED"
      }
  }
 }
```

#### Jak pobrać aktualne uprawnienia dla konta

Skorzystaj w tym celu z [GET /sale/allegro-prices-account-eligibility](https://developer.allegro.pl/documentation/#operation/getAllegroPricesEligibilityForAccount). W odpowiedzi otrzymasz:

statusy zgód:

- w polu “additionalMarketplaces.[].consent” - dla serwisów dodatkowych,
- w polu “consent” - dla serwisu bazowego,

informację, czy konto kwalifikuje się do uczestnictwa w programie:

- w polu “additionalMarketplaces.[].qualification.status” - dla serwisów dodatkowych.
- w polu “qualification.status” - dla serwisu bazowego,

Kryteria kwalifikacji znajdziesz na [stronie dla sprzedających](https://allegro.pl/pomoc/dla-sprzedajacych/abc-sprzedazy/poznaj-allegro-ceny-na-czym-polega-program-wsparcia-dla-sprzedajacych-MR45D5zADiy#co-zrobic-aby-twoja-oferta-trafila-do-programu).

Przykładowy request:

```
 curl -X GET \
 'https://api.allegro.pl/sale/allegro-prices-account-eligibility' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \
 -H 'Content-Type: application/vnd.allegro.public.v1+json' 
```

Przykładowy response:

```
{
    "consent": "ALLOWED",    // status zgody dla serwisu bazowego
    "qualification": {
          "status": "QUALIFIED"    // informacja, czy konto kwalifikuje się do programu
    },
    "additionalMarketplaces": {    // status zgody dla serwisów dodatkowych
          "allegro-cz": {
               "consent": "ALLOWED",
               "qualification": {
                    "status": "QUALIFIED"
               }
          },
          "allegro-xy": {
               "consent": "DENIED",
               "qualification": {
                    "status": "DISQUALIFIED"
               }
          }
    }
}
```

#### Jak zaktualizować zgodę dla konta

Zrobisz to za pomocą [PUT /sale/allegro-prices-account-consent](https://developer.allegro.pl/documentation/#operation/updateAllegroPricesConsentForAccount). Zgodę na uczestnictwo konta w programie Allegro Ceny możesz wyrazić dla serwisu bazowego lub/i serwisów dodatkowych.

Pamiętaj:

- jedno z pól - “status” lub “additionalMarketplaces” musisz zawsze przekazać w wywołaniu.
- jeżeli przekażesz pole “additionalMarketplaces” to musisz określić w nim status zgody dla minimum jednego serwisu dodatkowego;
- w polu “additionalMarketplaces” określisz status zgody dla serwisów dodatkowych;
- pole “status” jest opcjonalne;
- w polu “status” przekażesz status zgody tylko dla serwisu bazowego;

Przykładowy request:

```
curl -X PUT \
'https://api.allegro.pl/sale/allegro-prices-account-consent’ \
-H 'Authorization: Bearer {token}'  \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \ 
-d '{
    "status": "ALLOWED",    // status zgody dla serwisu bazowego
    "additionalMarketplaces": {    // status zgody dla serwisów dodatkowych
        "allegro-cz": {
            "status": "ALLOWED"
        },
        "allegro-xy": {
            "status": "DENIED"
        }
    }
}'
```

Przykładowy response:

```
{
    "consent": "ALLOWED",    // status zgody dla serwisu bazowego
    "qualification": {
          "status": "QUALIFIED"    // informacja, czy konto kwalifikuje się do programu
    },
    "additionalMarketplaces": {    // status zgody dla serwisów dodatkowych
          "allegro-cz": {
               "consent": "ALLOWED",
               "qualification": {
                    "status": "QUALIFIED"
               }
          },
          "allegro-xy": {
               "consent": "DENIED",
               "qualification": {
                    "status": "DISQUALIFIED"
               }
          }
    }
}
```

### AlleObniżka - jak zarządzać udziałem w programie

[AlleObniżka](https://help.allegro.com/sell/pl/a/czym-jest-program-alleobnizka-i-jak-do-niego-dolaczyc-oAd1MRa8Bc6) to cykliczny program, dzięki któremu możesz zaoferować klientom wybrane produkty w atrakcyjnych cenach. Pozwala wypromować oferty i zwiększyć sprzedaż bez dodatkowych opłat. Każda edycja trwa jeden tydzień. Program AlleObniżka możemy też uruchomić w ramach okazjonalnych kampanii, takich jak Allegro Days, BlackWeek czy SmartWeek.

#### Lista dostępnych kampanii AlleObniżka

Za pomocą [GET /sale/alle-discount/campaigns](https://developer.allegro.pl/documentation/#operation/getAlleDiscountCampaigns) pobierzesz listę dostępnych kampanii w ramach programu AlleObniżka.

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/alle-discount/campaigns' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
{
   "alleDiscountCampaigns":[
      {
         "id": "ALLEOBNIZKA_20240827_PL",    // identyfikator kampanii
         "name": "AlleObniżka 27.08-10.09.2024", // nazwa kampanii
         "type": "SOURCING",    // typ kampanii, dostępne wartości: SOURCING - kampania bez dodatkowych wymogów, DISCOUNT - kampania z wymogiem ceny niższej niż cena z ostatnich 30 dni.
         "visibility": {    // okres widoczności kampanii w Moje Allegro
          "type": "WITHIN",    // typ widoczności, dostępna wartość: WITHIN - w okresie dostępności
          "from": "2024-08-22T22:00:00Z",    // data początkowa
          "to": "2024-11-09T23:00:00Z"    // data końcowa
         },
         "application": {    // okres zgłaszania ofert do kampanii    
          "type": "WITHIN",    // typ widoczności, dostępna wartość: WITHIN
          "from": "2024-08-22T22:00:00Z",    // data początkowa
          "to": "2024-09-09T22:00:00Z"    // data końcowa
         },
         "publication": {    // okres widoczności obniżonej ceny w ofercie
          "type": "WITHIN",    // typ widoczności, dostępna wartość: WITHIN
          "from": "2024-08-26T22:00:00Z",    // data początkowa
          "to": "2024-09-09T22:00:00Z"    // data końcowa
         },
         "marketplace": {
          "id": "allegro-pl"     // identyfikator serwisu, dla którego kampania jest dostępna
         }
      },
      {
         "id": "ALLDEALS_ALLEOBNIZKA_202409_PL",
         "name": "Allegro Days AlleObniżka 02-08.09.2024",
         "type": "DISCOUNT",
         "visibility": {
          "type": "WITHIN",
          "from": "2024-08-26T13:00:00Z",
          "to": "2024-11-08T22:59:00Z"
         },
         "application": {
          "type": "WITHIN",
          "from": "2024-08-26T13:00:00Z",
          "to": "2024-09-08T21:59:00Z"
         },
         "publication": {
          "type": "WITHIN",
          "from": "2024-09-01T22:00:00Z",
          "to": "2024-09-08T21:59:00Z"
         },
         "marketplace": {
          "id": "allegro-pl"
         }
      }
   ],
   "count":2    // łączna liczba kampanii
}
```

#### Lista ofert kwalifikujących się do kampanii

Za pomocą [GET /sale/alle-discount/{campaignId}/eligible-offers](https://developer.allegro.pl/documentation/#operation/getOffersEligibleForAlleDiscount) pobierzesz listę swoich ofert kwalifikujących się do wybranej kampanii AlleObniżka. Przy wywołaniu musisz podać parametr campaignId (identyfikator kampanii).

Aby dostosować listę do swoich potrzeb, możesz skorzystać z parametrów:

- offerId - identyfikator wybranej oferty.
- meetsConditions - jeżeli “true” to zwrócimy listę tylko ofert spełniających kryteria danej kampanii;
- offset - by wskazać miejsce, od którego chcesz pobrać kolejną porcję danych;
- limit - maksymalna liczba ofert na liście, max 200;

Ważne! Aktualną listę produktów, które kwalifikują się do programu AlleObniżka, znajdziesz na stronie [Pomocy Allegro](https://help.allegro.com/sell/pl/a/alleobnizka-sprawdz-liste-towarow-O3PDg2XzeHR).

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/alle-discount/ALLEOBNIZKA_20240827_PL/eligible-offers' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
{
   "eligibleOffers": [
      {
          "id": "10394822344",    // identyfikator oferty
          "product": {
            "id": "765a6e61-b16f-4cad-bde4-8ed5d57b70a0"    // identyfikator produktu
          },
          "basePrice": {
            "amount": "4000.00",    // aktualna cena w ofercie
            "currency": "PLN"    // waluta
          },
          "alleDiscount": {
             "campaignConditions": {
                 "meetsConditions": true,    // informacja, czy oferta spełnia warunki kampanii
                 "violations": []    // powody wykluczenia z kampanii
            },
            "requiredMerchantPrice": {    // maksymalna cena w ofercie, aby spełniła kryteria kampanii
                 "amount": "3600.00",
                 "currency": "PLN"
            },
            "minimumGuaranteedDiscount": {    // minimalny poziom obniżki, który ustawimy od ceny zaproponowanej przez sprzedającego
                 "percentage": "7.50"
            }
          }
      },
      {
          "id": "10394822345",
          "product": {
            "id": "a19c189d-4717-412c-af63-d3eab8699672"
          },
          "basePrice": null,
          "alleDiscount":{
            "campaignConditions": {
                 "meetsConditions": false,
                 "violations": [
                  {
                     "code": "OFFER_PRICE_VERIFICATION_IN_PROGRESS",
                     "message": "OFFER_PRICE_VERIFICATION_IN_PROGRESS"
                  },
                  {
                     "code": "NOT_ENOUGH_STOCK",
                     "message": "NOT_ENOUGH_STOCK"
                  }
                 ]
            },
            "requiredMerchantPrice": {
                 "amount": "190.00",
                 "currency": "PLN"
            },
            "minimumGuaranteedDiscount": {
                 "percentage": "10.00"
            }
          }
      }
   ],
   "count": 2,
   "totalCount": 2    // łączna liczba ofert
}
```

#### Jak zgłosić ofertę do kampanii

Za pomocą [POST /sale/alle-discount/submit-offer-commands](https://developer.allegro.pl/documentation/#operation/submitOfferToAlleDiscountCommands) zgłosisz ofertę do wybranej kampanii AlleObniżka.

Przykładowy request:

```
curl -X POST \
'https://api.allegro.pl/sale/alle-discount/submit-offer-commands' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-d '{
  "commandId": "c1b3f63d-d293-4333-911d-a0c1053e2c81",    // niewymagane, unikalny identyfikator UUID; jeżeli go nie przekażesz, wygenerujemy go automatycznie
  "input": {
      "offer": {
            "id": "10394822344"     // identyfikator zgłaszanej oferty
      },
      "campaign": {            
            "id": "ALLEOBNIZKA_20240827_PL"    // identyfikator kampanii
      },
      "proposedPrice": {    // poziom ceny, do której zgadzasz się ją obniżyć. Musi być równa lub niższa niż maksymalna cena w ofercie, 
            "amount": "100.00",    // która spełnia kryteria kampanii ("requiredMerchantPrice") zwracana w GET /sale/alle-discount/{campaignId}/eligible-offers.
            "currency": "PLN"    // waluta
      }
   }
}'
```

Przykładowy response:

```
{
  "id": "c1b3f63d-d293-4333-911d-a0c1053e2c81", 
  "input": {
    "offer": {
      "id": "10394822344"
    },
    "campaign": {
      "id": "ALLEOBNIZKA_20240827_PL"
    },
    "proposedPrice": {
      "amount": "100.00",
      "currency": "PLN"
    }
  },
  "output": {
    "status": "NEW",    // status zgłoszenia
    "createdAt": "2024-08-23T10:15:30.000Z",    // data utworzenia zgłoszenia
    "updatedAt": "2024-08-23T10:15:30.000Z"    // data aktualizacji zgłoszenia
  }
}
```

Dodatkowo, w odpowiedzi zwrócimy nagłówek Location, gdzie znajdziesz odnośnik do zasobu ([GET /sale/alle-discount/submit-offer-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getSubmitOfferToAlleDiscountCommandsStatus)), którym sprawdzisz status swojego zgłoszenia.

#### Jak sprawdzić status zgłoszenia oferty do kampanii

Skorzystaj z [GET /sale/alle-discount/submit-offer-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getSubmitOfferToAlleDiscountCommandsStatus), aby pobrać status zgłoszenia oferty do wybranej kampanii AlleObniżka.

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/alle-discount/submit-offer-commands/c1b3f63d-d293-4333-911d-a0c1053e2c81' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
{
   "id": "c1b3f63d-d293-4333-911d-a0c1053e2c81",    // identyfikator UUID
   "input": {
      "offer": {
            "id": "10394822344"    // identyfikator zgłaszanej oferty
      },
      "campaign": {
            "id": "ALLEOBNIZKA_20240827_PL"    // identyfikator kampanii
      },
      "proposedPrice": {    // poziom ceny, do której zgadzasz się ją obniżyć. Musi być równa lub niższa niż maksymalna cena w ofercie,
            "amount": "100.00",    // która spełnia kryteria kampanii ("requiredMerchantPrice") zwracana w GET/ sale/alle-discount/{campaignId}/eligible-offers.
            "currency": "PLN"    // waluta
      }
   },
   "output": {
      "status": "SUCCESSFUL",    // status zgłoszenia, dostępne wartości: NEW, IN_PROGRESS, FAILED, SUCCESSFUL
      "createdAt": "2024-08-23T10:15:30.000Z",    // data utworzenia zgłoszenia
      "updatedAt": "2024-08-23T12:15:30.000Z",    // data aktualizacji zgłoszenia
      "newOfferParticipation": {
            "participationId": "f9a4a70c-6db9-4473-976c-90f8df9f74e8"    // identyfikator zgłoszenia oferty do kampanii
      },
      "errors": [].   // lista błędów
   }
}
```

#### Jak wycofać ofertę z kampanii

Aby wycofać ofertę z wybranej kampanii AlleObniżka skorzystaj z [POST /sale/alle-discount/withdraw-offer-commands](https://developer.allegro.pl/documentation/#operation/withdrawOfferFromAlleDiscountCommands). W requeście musisz przekazać “participationId” (identyfikator zgłoszenia oferty do kampanii), który znajdziesz w [GET /sale/alle-discount/submit-offer-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getSubmitOfferToAlleDiscountCommandsStatus) lub [GET /sale/alle-discount/{campaignId}/submitted-offers](https://developer.allegro.pl/documentation/#operation/getOffersSubmittedToAlleDiscount).

Przykładowy request:

```
curl -X POST \
'https://api.allegro.pl/sale/alle-discount/withdraw-offer-commands' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-d '{
  "commandId": "c1b3f63d-d293-4333-911d-a0c1053e2c81",         // niewymagane, unikalny identyfikator UUID; jeżeli go nie przekażesz, wygenerujemy go automatycznie
  "input": {
     "participationId": "f9a4a70c-6db9-4473-976c-90f8df9f74e8" // identyfikator zgłoszenia oferty do kampanii
  }
}'
```

Przykładowy response:

```
{
   "id": "c1b3f63d-d293-4333-911d-a0c1053e2c81", // identyfikator UUID
   "input": {
      "participationId": {
            "id": "f9a4a70c-6db9-4473-976c-90f8df9f74e8"
      }
   },
   "output":{
      "status": "NEW",                           // status wycofania
      "createdAt": "2024-08-23T10:15:30.000Z",   // data utworzenia wycofania
      "updatedAt": "2024-08-23T12:15:30.000Z"    // data aktualizacji wycofania
   }
}
```

Dodatkowo, w odpowiedzi zwrócimy nagłówek Location, gdzie znajdziesz odnośnik do zasobu ([GET /sale/alle-discount/withdraw-offer-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getWithdrawOfferFromAlleDiscountCommandsStatus)), którym sprawdzisz status swojego wycofania.

#### Jak sprawdzić status wycofania oferty z kampanii

Skorzystaj z [GET /sale/alle-discount/withdraw-offer-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getWithdrawOfferFromAlleDiscountCommandsStatus), aby pobrać status wycofania oferty z kampanii AlleObniżka.

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/alle-discount/withdraw-offer-commands/c1b3f63d-d293-4333-911d-a0c1053e2c81' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
{
  "id": "c1b3f63d-d293-4333-911d-a0c1053e2c81",    // identyfikator UUID
  "input": {
    "participationId": "f9a4a70c-6db9-4473-976c-90f8df9f74e8"
  },
  "output": {
    "status": "SUCCESSFUL",    // status wycofania, dostępne wartości: NEW, IN_PROGRESS, FAILED, SUCCESSFUL
    "createdAt": "2024-08-23T10:15:30.000Z",    // data utworzenia wycofania
    "updatedAt": "2024-08-23T12:15:30.000Z",    // data aktulizacji wycofania
    "withdrawnOfferParticipation": {  
       "participationId": "f9a4a70c-6db9-4473-976c-90f8df9f74e8"    // identyfikator wycofanego zgłoszenia oferty z kampanii
    },
    "errors": []    // lista błędów
  }
}
```

#### Lista ofert zgłoszonych do wybranej kampanii

Za pomocą [GET /sale/alle-discount/{campaignId}/submitted-offers](https://developer.allegro.pl/documentation/#operation/getOffersSubmittedToAlleDiscount) pobierzesz listę swoich ofert zgłoszonych do wybranej kampanii AlleObniżka. Przy wywołaniu musisz podać parametr campaignId (identyfikator kampanii).

Aby dostosować listę do swoich potrzeb, możesz skorzystać z parametrów:

- participationId - identyfikator zgłoszenia do kampanii.
- offerId - identyfikator wybranej oferty;
- offset - by wskazać miejsce, od którego chcesz pobrać kolejną porcję danych;
- limit - maksymalna liczba ofert na liście, max 200;

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/alle-discount/ALLEOBNIZKA_20240827_PL/submitted-offers' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
{
   "submittedOffers": [
      {
           "participationId": "765a6e61-b16f-4cad-bde4-8ed5d57b70a0", // identyfikator zgłoszenia oferty do kampanii 
           "offer": {
            "id": "10394822344"    / identyfikator oferty
           },
           "campaign": {
            "id": "ALLEOBNIZKA_DISCOUNT_TEST"    // identyfikator kampanii
           },
           "prices": {
            "proposedPrice": {    // poziom ceny, do której zgadzasz się ją obniżyć
                 "amount": "3600.00",
                 "currency": "PLN"
            },
            "minimalPriceReduction": {    // minimalna obniżka ceny
                 "amount": "270.00",
                 "currency": "PLN"
            },
            "maximumSellingPrice": {    // maksymalna cena w ofercie po obniżce
                 "amount": "3330.00",
                 "currency": "PLN"
            }
         },
         "process":{
            "status": "ACCEPTED",    // status udziału oferty w kampanii, dostępne wartości: VERIFICATION, ACCEPTED, ACTIVE, DECLINED, FINISHED.
            "errors": []    // lista błędów
         },
         "purchaseLimit": 1    // limit zakupów w ofercie
      }
   ],
   "count": 1,
   "totalCount": 1    // łączna liczba ofert
}
```

### Lista zasobów

Pełną dokumentację zasobów w postaci pliku swagger.yaml znajdziesz [tu](https://developer.allegro.pl/swagger.yaml).

Lista zasobów podstawowych opisanych w poradniku:

- [GET /sale/alle-discount/submit-offer-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getSubmitOfferToAlleDiscountCommandsStatus)- pobierz status zgłoszenia
- [POST /sale/alle-discount/submit-offer-commands](https://developer.allegro.pl/documentation/#operation/submitOfferToAlleDiscountCommands)- zgłoś ofertę do kampanii
- [GET /sale/alle-discount/campaigns](https://developer.allegro.pl/documentation/#operation/getAlleDiscountCampaigns)- pobierz listę dostępnych kampanii AlleObniżka
- [GET /sale/badge-applications/{applicationId}](https://developer.allegro.pl/documentation/#operation/badgeApplications_get_one)- pobierz szczegóły danego zgłoszenia
- [POST /sale/badges](https://developer.allegro.pl/documentation/#operation/postBadges)- zgłoś ofertę do danego oznaczenia
- [GET /sale/badge-campaigns](https://developer.allegro.pl/documentation/#operation/badgeCampaigns_get_all)- pobierz listę dostępnych kampanii

Lista zasobów wspierających opisanych w poradniku:

- [GET /sale/alle-discount/{campaignId}/submitted-offers](https://developer.allegro.pl/documentation/#operation/getOffersSubmittedToAlleDiscount)- pobierz listę ofert biorących udział w wybranej kampanii
- [GET /sale/alle-discount/{campaignId}/eligible-offers](https://developer.allegro.pl/documentation/#operation/getOffersEligibleForAlleDiscount)- pobierz listę ofert kwalifikujących się do wybranej kampanii
- [GET /sale/alle-discount/withdraw-offer-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getWithdrawOfferFromAlleDiscountCommandsStatus)- pobierz status wycofania
- [POST /sale/alle-discount/withdraw-offer-commands](https://developer.allegro.pl/documentation/#operation/withdrawOfferFromAlleDiscountCommands)- wycofaj ofertę z kampanii
- [PUT /sale/allegro-prices-account-consent](https://developer.allegro.pl/documentation/#operation/updateAllegroPricesConsentForAccount)- zaktualizuj zgodę dla konta na uczestnictwo w programie Allegro Ceny
- [GET /sale/allegro-prices-account-eligibility](https://developer.allegro.pl/documentation/#operation/getAllegroPricesEligibilityForAccount)- pobierz aktualne uprawnienia dla konta na uczestnictwo w programie Allegro Ceny
- [PUT /sale/allegro-prices-offer-consents/{offerId}](https://developer.allegro.pl/documentation/#operation/updateAllegroPricesConsentForOffer)- zaktualizuj zgodę na udział oferty w programie wsparcia Allegro Ceny
- [GET /sale/allegro-prices-offer-consents/{offerId}](https://developer.allegro.pl/documentation/#operation/getAllegroPricesConsentForOffer)- pobierz aktualną informację o zgodzie na udział oferty w programie wsparcia Allegro Ceny
- [GET /sale/badge-operations/{operationId}](https://developer.allegro.pl/documentation/#operation/badgeOperations_get_one) sprawdź status wykonania operacji zmiany ceny lub zakończenia oznaczenia
- [PATCH /sale/badges/offers/{offerId}/campaigns/{campaignId}](https://developer.allegro.pl/documentation/#operation/patchBadge) zleć operację zakończenia oznaczenia oferty w kampanii
- [PATCH /sale/badges/offers/{offerId}/campaigns/{campaignId}](https://developer.allegro.pl/documentation/#operation/patchBadge)- zleć operację zmiany ceny w kampanii
- [GET /sale/badge-applications](https://developer.allegro.pl/documentation/#operation/badgeApplications_get_all)- pobierz listę swoich zgłoszeń
- [GET /sale/badges](https://developer.allegro.pl/documentation/#operation/getBadges)- pobierz kampanie i oznaczenia przypisane do ofert

---

[Zgłoś błąd](https://github.com/allegro/allegro-api/issues/new/choose) lub [zasugeruj zmianę](https://github.com/allegro/allegro-api/discussions/new)

Czy ten artykuł był dla Ciebie przydatny?

Tak Nie

Serwisy Grupy Allegro

- [Allegro.cz](https://allegro.cz/)

- [Allegro.sk](https://allegro.sk/)

- [Allegro.hu](https://allegro.hu/)

- [Mall.hr](https://mall.hr/)

- [Mimovrste.com](https://mimovrste.com/)

- [Onedelivery.cz](https://onedelivery.cz/)

#### Dostosuj ustawienia wyświetlania

ustawienia dotyczą tylko tej przeglądarkiużyj preferencji systemowych

Automatycznie dostosujemy wygląd na podstawie ustawień systemowych Twojego urządzenia

motyw jasny zapisz