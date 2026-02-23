Zarządzanie ofertami - Allegro Developer Portal - baza wiedzy o Allegro REST API

Dziennik zdarzeń w ofertach sprzedawcy

Jak pobrać moje oferty w REST API

Edycja pojedynczej oferty

Edycja wielu ofert jednocześnie

Reguły cenowe

Kategorie i parametry

Jak zarządzać warunkami zwrotów

Jak zarządzać warunkami reklamacji

Jak zarządzać informacjami o gwarancjach

Jak zarządzać usługami dodatkowymi

Jak zarządzać promowaniem

Jak zarządzać tłumaczeniami

Jak zakończyć ofertę

Jak wznowić ofertę

Dodatkowe informacje

Najczęstsze błędy

FAQ

Lista zasobów

Limity

# Zarządzanie ofertami

Opis procesów, dzięki którym dowiesz się, jak zarządzać ofertami m.in. zbiorcza zmiana ceny, liczby sztuk, cenników dostawy, opcji promowania, itd.

### Dziennik zdarzeń w ofertach sprzedawcy

[GET /sale/offer-events](https://developer.allegro.pl/documentation/#operation/getOfferEvents) to dziennik zdarzeń w ofertach zalogowanego sprzedawcy, który zwraca informacje z ostatnich 24 godzin o:

wystawieniu oferty ("type": "OFFER_ACTIVATED");

zmianie w ofercie ("type": "OFFER_CHANGED");

zmianie liczby sztuk w ofercie - zwracany również po zakupie ("type": "OFFER_STOCK_CHANGED");

zmianie ceny w ofercie ("type": "OFFER_PRICE_CHANGED");

zakończeniu oferty ("type": "OFFER_ENDED");

zarchiwizowaniu oferty ("type": "OFFER_ARCHIVED");

złożeniu oferty w licytacji ("type": "OFFER_BID_PLACED");

wycofaniu oferty w licytacji ("type": "OFFER_BID_CANCELED");

aktualizacji tłumaczenia oferty ("type": "OFFER_TRANSLATION_UPDATED")

zmianie statusu widoczności oferty w serwisie dodatkowym ( "type": "OFFER_VISIBILITY_CHANGED")

W wywołaniu możesz podać parametry wejściowe, które pozwolą ci dopasować odpowiedź do twoich potrzeb:

from - podaj id eventu, by uzyskać wszystkie eventy które nastąpiły później (np. from=MTEzMjQzODU3NA);

limit - podaj liczbę eventów, które chcesz uzyskać w odpowiedzi (domyślnie 100, max. 1000);

type - podaj typ eventów, które chcesz uzyskać w odpowiedzi (np. type=OFFER_ENDED).

Przykładowy request - którym uzyskasz 200 zdarzeń o zmianie liczby sztuk, które nastąpiły po evencie o "id": "MTU2Mzg2NTM5MTU2Mzg0Ng"

```
  curl -X GET \
  'https://api.allegro.pl/sale/offer-events?from=MTU2Mzg2NTM5MTU2Mzg0Ng&limit=200&type=OFFER_STOCK_CHANGED' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Authorization: Bearer {token}'
```

### Jak pobrać moje oferty w REST API

Aby otrzymać listę wszystkich ofert danego użytkownika, wywołaj [GET /sale/offers](https://developer.allegro.pl/documentation/#operation/searchOffersUsingGET). Musisz być zautoryzowanym jako sprzedawca, który utworzył te oferty. Domyślnie oferty posortowane są po identyfikatorze oferty malejąco.

Aby dostosować listę wyszukiwania do swoich potrzeb, możesz skorzystać z parametrów:

limit by określić liczbę ofert na liście (przyjmuje wartości od 1 do 1000),

offset by wskazać miejsce, od którego chcesz pobrać kolejną porcję danych (min. 0),

np. GET sale/offers?limit=100&offset=10

#### Filtry

Przeszukiwanie listy ułatwią ci filtry:

oferty z odpowiednim statusem - wywołaj GET /sale/offers?publication.status={status} - może zawierać jedną lub więcej wartości, np. GET sale/offers?publication.status=INACTIVE&publication.status=ACTIVE

INACTIVE - draft oferty,

ACTIVE - wystawiona oferta,

ACTIVATING - zaplanowana oferta lub w czasie wystawiania,

ENDED - zakończona oferta.

szukanie po identyfikatorze oferty - wywołaj GET /sale/offers?offer.id={offer.id}

szukanie po sygnaturze (jednym lub więcej external.id) - wywołaj GET /sale/offers?external.id={external_id}&external.id={external_id}

szukanie po tytule - wywołaj GET /sale/offers?name={name} - należy podać choć jedną literę, na którą zaczyna się jakikolwiek wyraz z tytułu

szukanie po identyfikatorze kategorii - wywołaj GET /sale/offers?category.id={categoryId}

szukanie ofert z konkretną regułą cenową - wywołaj GET /sale/offers?sellingMode.priceAutomation.rule.id={ruleId}, aby wyświetlić tylko te oferty, których ceną zarządza ta konkretna reguła cenowa

szukanie ofert bez żadnej reguły cenową lub z jakąkolwiek regułą cenową - wywołaj GET /sale/offers?sellingMode.priceAutomation.rule.id.empty={boolean} i przekaż wartość false, aby znaleźć tylko takie oferty, które posiadają jakąkolwiek regułę cenową, lub true, aby znaleźć tylko oferty bez takiej reguły.

szukanie ofert, które nie posiadają przypisanego produktu - wywołaj GET /sale/offers?product.id.empty=true

szukanie ofert, które należą do kategorii, w których produktyzacja jest obowiązkowa - wywołaj GET /sale/offers?productizationRequired=true

szukanie po cenniku dostawy - wywołaj GET/sale/offers?delivery.shippingRates.id={id}

szukanie ofert bez cennika dostawy - wywołaj GET/sale/offers?delivery.shippingRates.id.empty=true

szukanie po warunkach zwrotów - wywołaj GET /sale/offers?afterSalesServices.returnPolicy.id={id}

minimalna cena - wywołaj GET /sale/offers?sellingMode.price.amount.gte={price}

maksymalna cena - wywołaj GET /sale/offers?sellingMode.price.amount.lte={price}

format sprzedaży - wywołaj GET /sale/offers?sellingMode.format={format} - może zawierać jedną lub więcej wartości oddzielonych przecinkiem:

BUY_NOW - Kup teraz,

ADVERTISEMENT - ogłoszenie,

AUCTION - licytacja.

szukanie ofert dla biznesu - wywołaj GET /sale/offers?b2b.buyableOnlyByBusiness=true

szukanie ofert wybranej zbiórki charytatywnej - wywołaj GET /sale/offers?fundraisingCampaign.id={id}

szukanie ofert danego typu - wywołaj GET /sale/offers?fundraisingCampaign.id.empty={wartość} - pole przyjmuje dwie wartości:

- false - jeżeli chcesz pobrać tylko listę ofert charytatywnych,
- true - jeżeli chcesz pobrać tylko listę ofert komercyjnych,

szukanie według serwisu - wywołaj GET /sale/offers?publication.marketplace={marketplaceId}.

#### Sortowanie

Domyślnie oferty posortowane są od najnowszej (po ID malejąco). Aby otrzymać oferty w innej kolejności, możesz je posortować korzystając z GET /sale/offers?sort={value}. Możesz skorzystać z następujących wartości:

sellingMode.price.amount - sortowanie po cenie rosnąco,

-sellingMode.price.amount - sortowanie po cenie malejąco,

stock.sold - sortowanie po liczbie sprzedanych przedmiotów rosnąco,

-stock.sold - sortowanie po liczbie sprzedanych przedmiotów malejąco,

stock.available - sortowanie po liczbie dostępnych przedmiotów rosnąco,

-stock.available - sortowanie po liczbie dostępnych przedmiotów malejąco.

Użyj parametrów limit (przyjmuje wartości od 1 do 1000) i offset (min. 0, maksymalnie ilość ofert -1) do pobierania odpowiednich porcji ofert.

Poniżej kilka przykładów wywołań dla listy ofert:

wyszukaj wszystkie moje aktywne oferty i posortuj je po liczbie sprzedanych przedmiotów rosnąco: GET /sale/offers?publication.status=ACTIVE&sort=stock.sold,

wyszukaj wszystkie moje oferty kup teraz, które w tytule mają frazę "suszarka" GET /sale/offers?sellingMode.format=BUY_NOW&name=suszarka,

wyszukaj wszystkie moje oferty, w których cena przedmiotu mieści się w przedziale od 50 do 120 PLN i posortuj je po cenie malejąco: GET /sale/offers?sellingMode.price.amount.gte=50&sellingMode.price.amount.lte=120&sort=-sellingMode.price.amount,

wyświetl wszystkie oferty łącznie z draftami: GET /sale/offers?publication.status=INACTIVE&publication.status=ACTIVATING&publication.status=ACTIVE& publication.status=ENDED,

wyświetl listę moich ofert.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/offers' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json'
```

```
 {
    "offers": [
        {
            "id": "7610768778",    // numer identyfikacyjny oferty
            "name": "Suszarka do włosów A180 dyfuzor",    // tytuł oferty
            "category": {
                "id": "67481"    // kategoria najniższego rzędu, w której znajduje się oferta
            },
            "primaryImage": {    // zdjęcie główne w ofercie (miniaturka)
                "url": "https://9.allegroimg.com/original/03d631/d744e5be46dfbfb687d2faee38b9"
            },
            "sellingMode": {
                "format": "BUY_NOW",     // format sprzedaży, przyjmuje wartości:
                                              "BUY_NOW" (Kup teraz), "ADVERTISEMENT"
                                              (ogłoszenie), "AUCTION" (licytacja)
                "price": {
                    "amount": "133.0",    // cena dla oferty w formacie BUY_NOW (Kup Teraz), ADVERTISEMENT (ogłoszenie)
                    "currency": "PLN"
                },
                "priceAutomation": {
                    "rule": {
                        "id": "641c73feaef0a8281a3d11f8",    // ID reguły cenowej
                        "type": "FOLLOW_BY_ALLEGRO_MIN_PRICE"    // typ reguły cenowej
                  }
                },
                "minimalPrice": null,    // cena minimalna, dostępna w formacie sprzedaży AUCTION (licytacja)
                "startingPrice": null    // cena początkowa licytacji, dostępna w formacie sprzedaży AUCTION (licytacja)
            },
            "saleInfo": {
                "currentPrice": null,     // cena zakupu w licytacji
                "biddersCount": 0    // liczba osób licytujących
            },
            "stats": {
                "watchersCount": 0,    // liczba obserwowanych
                "visitsCount": 0    // liczba odwiedzonych
            },
            "stock": {
                "available": 8,    // liczba przedmiotów aktualnie dostępnych w ofercie
                "sold": 0    // liczba sprzedanych przedmiotów w ofercie z ostatnich 30 dni
            },
            "publication": {
                "status": "ACTIVE",    // status oferty, przyjmuje wartości: "INACTIVE" (draft), "ACTIVE" (wystawiona), "ACTIVATING" (planowana lub w czasie wystawiania), "ENDED" (zakończona)
                "startingAt": null,     // data zaplanowanego wystawienia
                "startedAt": "2018-10-11T12:16:02Z",    // data wystawienia oferty
                "endingAt": "2018-10-21T12:16:02Z",     // data planowanego zakończenia oferty
                "endedAt": null    // faktyczna data zakończenia oferty
            },
            "afterSalesServices": {
                "warranty": {
                  "id": "2d15741b-93b1-4d24-989c-dc2d412d91ff"    // identyfikator warunków gwarancji
                },
                "returnPolicy": {
                  "id": "cf5f8e7a-4488-4420-810d-259bd84b745f"    // identyfikator polityki zwrotów
                },
                "impliedWarranty": {
                  "id": "de2ad368-2682-47ab-9868-d813d968846a"    // identyfikator opisu reklamacji
                }
            },
            "additionalServices": {
                "id": "ab18d75d-5db2-4bee-aca5-32de952a7b44"    // identyfikator usług dodatkowych
            },
            "external": {
                "id": "external_id"    // sygnatura - zewnętrzny identyfikator
            },
            "delivery": {
                "shippingRates": {
                    "id": "2991e29e-5fbc-46f5-963a-65c326ba65c2"    // identyfikator cennika dostaw
                }
            },
            "b2b": {
                "buyableOnlyByBusiness": false    // informacja, czy oferta jest dostępna do zakupu tylko dla kupujących z kontem firmowym
            },                                    
            "fundraisingCampaign": {
                "id": "e2307b4f-6903-4be6-85e6-19e8ea303760"    // identyfikator zbiórki charytatywnej
            }
        },
        {
            "id": "7569844187",
            "name": "fotel bujany",
            "category": {
                "id": "20285"
            },
            "primaryImage": {
                "url": "https://9.allegroimg.com/original/03d631/d744e5be46dfbfb687d2faee37b9"
            },
            "sellingMode": {
                "format": "AUCTION",
                "price": {
                    "amount": "220.0",
                    "currency": "PLN"
                },
                "minimalPrice": null,
                "startingPrice": {
                    "amount": "150.0",
                    "currency": "PLN"
                }
            },
            "saleInfo": {
                "currentPrice": {
                    "amount": "150.0",
                    "currency": "PLN"
                },
                "biddersCount": 0
            },
            "stats": {
                "watchersCount": 0,
                "visitsCount": 17
            },
            "stock": {
                "available": 1,
                "sold": 0
            },
            "publication": {
                "status": "ENDED",
                "startingAt": null,
                "startedAt": "2018-10-02T11:16:13Z",
                "endingAt": "2018-10-07T11:16:13Z",
                "endedAt": "2018-10-07T11:16:13Z"
            },
            "afterSalesServices": {
                "warranty": {
                    "id": "2d15741b-93b1-4d24-989c-dc2d412d91ff"
                },
                "returnPolicy": {
                    "id": "cf5f8e7a-4488-4420-810d-259bd84b745f"
                },
                "impliedWarranty": {
                    "id": "de2ad368-2682-47ab-9868-d813d968846a"
                }
            },
            "additionalServices": null,
            "external": null
            },
            "delivery": {
                "shippingRates": {
                    "id": "2991e29e-5fbc-46f5-963a-65c326ba65c2"
                }
            },
            "b2b": {
                "buyableOnlyByBusiness": false
            },
            "fundraisingCampaign": {
                "id": "e2307b4f-6903-4be6-85e6-19e8ea303760"
            }
    ],
    "count": 2,    // liczba ofert w tej odpowiedzi
    "totalCount": 2    // liczba ofert dostępnych dla tego zapytania
 }
```

zamknij

Przykładowy response z listą ofert

### Edycja pojedynczej oferty

Za pomocą [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/editProductOffers) zmienisz dane w ofercie w prosty sposób - edytujesz dowolne pole oferty, a jednocześnie nie musisz przekazywać całego jej modelu.

W ten sposób edytujesz niezależnie m.in:

- identyfikator produktu.
- status oferty,
- opis oferty,
- cenę,
- lokalizację,
- parametry,
- zdjęcia,

Ważne! Jeśli w sekcji produktowej (opisującej sprzedawany produkt - productSet.product) wskażesz nam tylko product.id - jest to równoważne z żądaniem aktualizacji oferty aktualnymi danymi z produktu. Zatem, jeśli chcesz mieć pełną kontrolę, jak będzie wyglądała oferta po wykonaniu żądania, sam zdefiniuj również takie pola jak: description, images, product.parameters. Dane edytowanej oferty możesz pobrać za pomocą G [ET /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/getProductOffer).

Przy edycji zapewniliśmy te same udogodnienia, które przy tworzeniu ofert daje [POST /sale/product-offers](https://developer.allegro.pl/documentation/#operation/createProductOffers), dlatego dzięki [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/editProductOffers) możesz:

- posługiwać się nazwami warunków ofert zamiast ich identyfikatorami (cenniki dostawy, warunki zwrotów oraz reklamacji).
- dodać do oferty zdjęcia bezpośrednio z zewnętrznych serwerów,
- zmienić status oferty bez konieczności wywołania osobnej komendy publikacji,

Ważne! Gdy skorzystasz z [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/editProductOffers), a w ofercie powiązanej z danym produktem wartości pola tecdocSpecification i compatibilityList nie będą aktualne, tzn. niezgodnie z danymi w produkcie - automatycznie je zaktualizujemy.

Poniższy diagram obrazuje, w jaki sposób aktualizujemy dane w ofercie:

W tabeli poniżej znajdziesz informacje, w jaki sposób obsłużymy parametry w ofercie:

- P - parametr produktowy,
- O - parametr ofertowy,

\

poniżej zdjęcia:

- I - obrazek,

oraz opis:

- D - opis

#### Edycja oferty w asynchronicznym API

W odpowiedzi na prawidłowe żądanie metodą PATCH /sale/product-offers/{offerId} otrzymasz jeden z statusów:

200 OK - gdy żądanie odnosi się do modyfikacji atrybutów oferty, które nie wiążą się z długo wykonywanymi operacjami. Zmiany wdrożymy od razu.

202 Accepted - gdy żądanie wiąże się z długo wykonywanymi operacjami. np. zmiana statusu publikacji oferty. Zmianę wprowadzimy asynchronicznie.

W przypadku, gdy zwrócimy status 200 OK - w odpowiedzi przekażemy dane oferty z wprowadzonymi już zmianami:

Przykładowy request:

```
  curl -X PATCH
  ‘https://api.allegro.pl/sale/product-offers/9531382307’
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
  -d ’{
  "sellingMode": {
     "price": {
       "amount": "50",
       "currency": "PLN"
    }
  }    
  }’
```

```
  HTTP/1.1 200 OK
  {
    "id": "9531382307’",
    "name": "Przykładowa nazwa",
    "productSet": [{
        "product": {
            "id": null,
            "publication": {
                "status": "NOT_LISTED"
            },
            "parameters": [
                {
                        "id": "234925",
                        "name": "Testowy tytuł",
                        "values": [
                            "Test LP9"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    }, ...
            ]
            },
            "quantity": {
                "value": 1
            }
    }],
    "parameters": [
        {
            "id": "11323",
            "name": "State",
            "values": [
                "New"
            ],
            "valuesIds": [
                "11323_1"
            ],
            "rangeValue": null
        }
    ],
    "afterSalesServices": {
        "impliedWarranty": {
            "id": "f86078a6-9f42-4b76-9696-1e5c0646a60a"
        },
        "returnPolicy": {
            "id": "47101223-7236-4201-9779-316e6d10af2a"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "NO_INVOICE"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": 50,
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 1,
        "unit": "UNIT"
    },
    "location": {
        "countryCode": "PL",
        "province": "WIELKOPOLSKIE",
        "city": "Poznań",
        "postCode": "66-166"
    },
    "delivery": {
        "shippingRates": {
            "id": "17221a3c-f4cf-4e47-953a-8e125013b014"
        },
        "handlingTime": "PT336H",
        "additionalInfo": ""
    },
    "publication": {
        "duration": null,
        "status": "ACTIVE",
        "endedBy": null,
        "endingAt": null,
        "startingAt": null,
        "republish": false
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>test</p>"
                    }
                ]
            }
        ]
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2020-11-06T15:39:53.898Z"
    },
    "createdAt": "2020-10-01T05:44:23Z",
    "updatedAt": "2020-11-06T15:39:55.574Z",
    "images": [
        "https://a.allegroimg..pl/original/116421/ece7111d4b8fbbc4662ab92f84ce"
    ],
    "external": null,
    "category": {
        "id": "79419"
    },
    "taxSettings": null,
    "sizeTable": null,
    "b2b": {
        "buyableOnlyByBusiness": false
    }
 }
```

Jeżeli w odpowiedzi zwrócimy status 202 Accepted, zwrócimy dane oferty z aktualnym jej stanem - nie uwzględniającym jeszcze danych, które są procesowane. Zmiany w ofercie wprowadzimy asynchronicznie.

Aby sprawdzić status ukończenia zadania, skorzystaj z adresu otrzymanego w nagłówku Location - jest to odnośnik do zasobu, który powinieneś odpytywać, aby sprawdzić status wykonania żądania. Z kolei w nagłówku retry-after przekazujemy informację, po jakim czasie (w sekundach) możesz ponownie odpytać zasób.

Przykładowy request:

```
  curl -X PATCH
  ‘https://api.allegro.pl/sale/product-offers/9531382307’
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
  -d ’{
    "publication": {
         "status": "ACTIVE"
     }
  }’
```

```
  HTTP/1.1 202 Accepted
  location: ‘https://api.allegro.pl/sale/product-offers/9531382307/sale/operations/ef5dd966-d370-44f7-bb30-3631e3511536’
  retry-after: 5
  {
    "id": "9531382307’",
    "name": "Przykładowa nazwa",
    "productSet": [{
        "product": {
            "id": null,
            "publication": {
                "status": "NOT_LISTED"
            },
            "parameters": null
        },
        "quantity": {
                "value": 1
            }
    }],
    "parameters": [
        {
            "id": "11323",
            "name": "State",
            "values": [
                "New"
            ],
            "valuesIds": [
                "11323_1"
            ],
            "rangeValue": null
        }
    ],
    "afterSalesServices": {
        "impliedWarranty": {
            "id": "f86078a6-9f42-4b76-9696-1e5c0646a60a"
        },
        "returnPolicy": {
            "id": "47101223-7236-4201-9779-316e6d10af2a"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "NO_INVOICE"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": 50,
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 1,
        "unit": "UNIT"
    },
    "location": {
        "countryCode": "PL",
        "province": "WIELKOPOLSKIE",
        "city": "Poznań",
        "postCode": "66-166"
    },
    "delivery": {
        "shippingRates": {
            "id": "17221a3c-f4cf-4e47-953a-8e125013b014"
        },
        "handlingTime": "PT336H",
        "additionalInfo": ""
    },
    "publication": {
        "duration": null,
        "status": "ENDED",
        "endedBy": "USER",
        "endingAt": null,
        "startingAt": null,
        "republish": false
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>test</p>"
                    }
                ]
            }
        ]
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2020-11-06T15:39:53.898Z"
    },
    "createdAt": "2020-10-01T05:44:23Z",
    "updatedAt": "2020-11-06T15:42:06.315Z",
    "images": [
        "https://a.allegroimg.pl/original/116421/ece7111d4b8fbbc4662ab92f84ce"
    ],
    "external": null,
    "category": {
        "id": "79419"
    },
    "taxSettings": null,
    "sizeTable": null,
    "b2b": {
        "buyableOnlyByBusiness": false
    }
 }
```

Skorzystaj z metody GET oraz otrzymanego adresu w Location, aby sprawdzić status wykonania zadania. Do czasu zakończenia operacji w odpowiedzi na to żądanie wyślemy odpowiedź status 202 Accepted.

Przykładowy request:

```
  curl -X GET
  ‘https://api.allegro.pl/sale/product-offers/9531382307/operations/ef5dd966-d370-44f7-bb30-3631e3511536’
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
HTTP/1.1 202 Accepted
location: https://api.allegro.pl/sale/product-offers/9531382307/operations/ef5dd966-d370-44f7-bb30-3631e3511536
retry-after: 5
 {
  "offer": {
    "id": "9531382307"
  },
  "operation": {
    "id": "ef5dd966-d370-44f7-bb30-3631e3511536",
    "status": "IN_PROGRESS",
    "startedAt": "2019-05-29T12:00:00Z"
  }
}
```

Gdy zakończymy przetwarzać operację, w odpowiedzi na żądanie GET /sale/product-offers/{offerId}/operations/{operationId} wyślemy status HTTP 303 See Other, a w nagłówku Location przekażemy odnośnik kierujący do zasobu z danymi oferty.

Przykładowy request:

```
  curl -X GET
  ‘https://api.allegro.pl/sale/product-offers/9531382307/operations/ef5dd966-d370-44f7-bb30-3631e3511536’
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  HTTP/1.1 303 See Other
  location: https://api.allegro.pl/sale/product-offers/9531382307
```

Skorzystaj z metody GET oraz przesłanego otrzymanego w nagłówku location, aby uzyskać aktualne dane oferty. Utworzysz dzięki temu żądanie w następującej formie: GET /sale/product-offers/{offerId}.

Przykładowy request:

```
  curl -X GET
  ‘https://api.allegro.pl/sale/product-offers/9531382307’
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json
```

```
'{
    "id": "9531382307",
    "name": "Przykładowa nazwa",
    "productSet": [{
        "product": {
            "id": "21a0e252-aa3f-4666-9278-b0417743790f",
            "publication": {
                "status": "LISTED"
            },
            "parameters": [
                {
                        "id": "234925",
                        "name": "Testowy tytuł",
                        "values": [
                            "Test LP9"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    }, ...
            ]
        },
        "quantity": {
                "value": 1
            }
    }],
    "parameters": [
        {
            "id": "11323",
            "name": "State",
            "values": [
                "New"
            ],
            "valuesIds": [
                "11323_1"
            ],
            "rangeValue": null
        }
    ],
    "afterSalesServices": {
        "impliedWarranty": {
            "id": "ad2a9867-71b1-499b-8211-0048536992c5"
        },
        "returnPolicy": {
            "id": "b20a9525-f431-495f-96a8-45af3255374f"
        },
        "warranty": {
            "id": "74cf0d61-590d-4235-8229-8f0d7e7c54e3"
        }
    },
    "payments": {
        "invoice": "VAT"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": 50,
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 2,
        "unit": "UNIT"
    },
    "location": {
        "countryCode": "PL",
        "province": "WIELKOPOLSKIE",
        "city": "Poznań",
        "postCode": "60-130"
    },
    "delivery": {
        "shippingRates": {
            "id": "04624cf1-558f-4356-bf2b-1fa34a091ca3"
        },
        "handlingTime": "PT168H",
        "additionalInfo": ""
    },
    "publication": {
        "duration": "PT240H",
        "status": "ACTIVE",
        "endedBy": null,
        "endingAt": "2020-10-04T12:13:20Z",
        "startingAt": null,
        "republish": false
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>testowy opis</p>"
                    }
                ]
            },
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>testowy opis</p>"
                    }
                ]
            }
        ]
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2020-09-28T08:22:34.223Z"
    },
    "createdAt": "2020-07-24T13:50:33Z",
    "updatedAt": "2020-09-28T08:22:35.851Z",
    "images": [
        "https://c.allegroimg.com/original/0587c4/1a7a1b46438da3de2cf8a328791a",
        "https://c.allegroimg.com/original/0587c4/1a7a1b46438da3de2cf8a328791b"
    ],
    "external": null,
    "category": {
        "id": "260395"
    },
    "sizeTable": {
      "id": “5727b598-6608-4bd3-b198-f165b011bb69”
    },
    "taxSettings": null,
    "b2b": {
        "buyableOnlyByBusiness": false
    }
}'
```

#### Edycja pól oferty

Skorzystaj z [PATCH /sale/product-offers/{offerId](https://developer.allegro.pl/documentation/#operation/editProductOffers) oraz przekaż w strukturze żądania tylko te pola, które rzeczywiście chcesz zmienić. W pozostałych polach pozostawimy dotychczasową wartość. Działanie zasobu jest zgodnie z dokumentem [RFC7396](https://tools.ietf.org/html/rfc7396).

Oto kilka przykładowych wywołań:

zmiana ceny:

Przykładowy request:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ’{
"sellingMode": {
"price": {
  "amount": "50",
  “currency”: “PLN”
}
}    
}’
```

zmiana lokalizacji:

Przykładowy request:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ‘{
   "location": {
     "countryCode": "PL",
      "province": "WIELKOPOLSKIE",
      "city": "Poznań",
      "postCode": "60-166"
}
}’
```

zmiana liczby sztuk:

Przykładowy request:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ‘{
"stock": {
    "available": 2,
    "unit": "UNIT"
}
}’
```

Ważne! Pamiętaj, że w przypadku tablic (np. productSet, parameters, images, description) przyjmujemy zasadę wszystko albo nic (zgodnie z [RFC7396](https://tools.ietf.org/html/rfc7396)). Oznacza to, że np. jeżeli chcesz dodać do oferty nowe zdjęcia, ale równocześnie chcesz pozostawić te, które były już wcześniej w tej ofercie - musisz przekazać zarówno nowe zdjęcia, jak i te, które były już w tablicy images.

Przykładowy request:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ‘{
   "images": [
       "https://c.allegroimg.com/original/0587c4/1a7a1b46438da3de2cf8a328791a",
       "https://c.allegroimg.com/original/0587c4/1a7a1b46438da3de2cf8a328791b"
   ]
}’
```

```
'{
    "id": "9531382307",
    "name": "Książka",
    "productSet": [{
        "product": {
            "id": "21a0e252-aa3f-4666-9278-b0417743790f",
            "publication": {
                "status": "LISTED"
            },
            "parameters": [
                {
                    "id": "234925",
                    "name": "Testowy tytuł",
                    "values": [
                        "Test LP9"
                    ],
                    "valuesIds": null,
                    "rangeValue": null
                    }, ...
            ]
        },
        "quantity": {
                "value": 1
            }
    }],
    "parameters": [
        {
            "id": "11323",
            "name": "State",
            "values": [
                "New"
            ],
            "valuesIds": [
                "11323_1"
            ],
            "rangeValue": null
        }
    ],
    "afterSalesServices": {
        "impliedWarranty": {
            "id": "ad2a9867-71b1-499b-8211-0048536992c5"
        },
        "returnPolicy": {
            "id": "b20a9525-f431-495f-96a8-45af3255374f"
        },
        "warranty": {
            "id": "74cf0d61-590d-4235-8229-8f0d7e7c54e3"
        }
    },
    "payments": {
        "invoice": "VAT"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": 50,
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 2,
        "unit": "UNIT"
    },
    "location": {
        "countryCode": "PL",
        "province": "WIELKOPOLSKIE",
        "city": "Poznań",
        "postCode": "60-130"
    },
    "delivery": {
        "shippingRates": {
            "id": "04624cf1-558f-4356-bf2b-1fa34a091ca3"
        },
        "handlingTime": "PT168H",
        "additionalInfo": ""
    },
    "publication": {
        "duration": "PT240H",
        "status": "ACTIVE",
        "endedBy": null,
        "endingAt": "2020-10-04T12:13:20Z",
        "startingAt": null,
        "republish": false
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>testowy opis</p>"
                    }
                ]
            },
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>testowy opis</p>"
                    }
                ]
            }
        ]
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2020-09-28T08:22:34.223Z"
    },
    "createdAt": "2020-07-24T13:50:33Z",
    "updatedAt": "2020-09-28T08:22:35.851Z",
    "images": [
        "https://c.allegroimg.com/original/0587c4/1a7a1b46438da3de2cf8a328791a",
        "https://c.allegroimg.com/original/0587c4/1a7a1b46438da3de2cf8a328791b"
    ],
    "external": null,
    "category": {
        "id": "260395"
    },
    "sizeTable": {
      "id": “5727b598-6608-4bd3-b198-f165b011bb69”
    },
    "taxSettings": null,
    "b2b": {
        "buyableOnlyByBusiness": false
    }
}'
```

#### Jak przypisać produkt do oferty

Za pomocą [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/editProductOffers) możesz dodać produkt do oferty, która nie jest połączona z produktem lub zmienić go w ofercie, która produkt już posiada.

W polu product.id wskaż identyfikator danego produktu lub parametr GTIN (EAN, ISBN, ISSN). W odpowiedzi automatycznie zaktualizujemy w ofercie:

- specyfikację techniczną TecDoc
- sekcję pasuje do,
- zdjęcia,
- opis,
- kategorię i parametry,

zgodnie z danymi w powiązanym produkcie.

Ważne! Jeżeli chcesz zachować aktualny opis, zdjęcia i parametry produktowe, oprócz product.id powinieneś przekazać również takie pola jak: description, images i product.parameters. Możesz je pobrać z edytowanej przez Ciebie oferty, korzystając z [GET /sale/offers/{offerId}](https://developer.allegro.pl/documentation/#operation/getOfferUsingGET)

Nie możesz usunąć produktu z oferty. W przypadku, gdy w polu product.id przekażesz wartość null - zwrócimy błąd 422.

Pamiętaj również, że kategorię możesz zmienić do 12 godzin po pierwszym wystawieniu oferty. Oznacza to, że po 12 godzinach nie przypiszesz do oferty produktu z innej kategorii, niż ta, w której wystawiłeś ofertę.

Zapoznaj się z poniższym przykładem procesu powiązania oferty z produktem metodą PATCH.

Aktualne dane oferty, którą chcesz połączyć z produktem, pobierzesz za pomocą [GET /sale/offers/{offerId}](https://developer.allegro.pl/documentation/#operation/getOfferUsingGET).

Przykładowy response:

```
{
    "id": "7680042192",
    "name": "Żarówka samochodowa LED",
    "category": {
        "id": "257359"
    },
    "product": null,
    "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_1"
            ],
            "values": [],
            "rangeValue": null
        },
        {
            "id": "127634",
            "valuesIds": [
                "127634_3"
            ],
            "values": [],
            "rangeValue": null
        },
        {
            "id": "23910",
            "valuesIds": [
                "23910_13"
            ],
            "values": [],
            "rangeValue": null
        },
        {
            "id": "208602",
            "valuesIds": [
                "208602_794154"
            ],
            "values": [],
            "rangeValue": null
        },
        {
            "id": "202269",
            "valuesIds": [
                "202269_210981"
            ],
            "values": [],
            "rangeValue": null
        },
        {
            "id": "215858",
            "valuesIds": [],
            "values": [
                "BA15SSMD-Rx5"
            ],
            "rangeValue": null
        }
    ],
    "customParameters": null,
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<h2>Żarówka LED Nieprzezroczysta matowa soczewka</h2>"
                    }
                ]
            },
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Mój opis żarówki</p>"
                    }
                ]
            }
        ]
    },
    "compatibilityList": null,
    "tecdocSpecification": null,
    "images": [
        {
            "url": "https://a.allegroimg.com/original/11ea99/7efbfdb341d78d380f459672a95f"
        }
    ],
```

Dane konkretnego produktu uzyskasz za pomocą [GET /sale/products/{productId}.](https://developer.allegro.pl/documentation/#operation/getSaleProduct)

Przykładowy response:

```
{
    "id": "0475a562-fbbb-4260-b772-59a82aa96554",
    "name": "5 x 12v 24v 382 BA15S R5W 245207 Żarówka LED",
    "category": {
        "id": "257359",
        "similar": [
            {
                "id": "19028"
            }
        ]
    },
    "parameters": [
        {
            "id": "127634",
            "name": "Rodzaj",
            "valuesLabels": [
                "Brak informacji"
            ],
            "valuesIds": [
                "127634_384881"
            ],
            "values": null,
            "unit": null,
            "options": {
                "identifiesProduct": true
            }
        },
        {
            "id": "23910",
            "name": "Typ żarówki",
            "valuesLabels": [
                "P21"
            ],
            "valuesIds": [
                "23910_527293"
            ],
            "values": null,
            "unit": null,
            "options": {
                "identifiesProduct": true
            }
        },
        {
            "id": "208602",
            "name": "Producent",
            "valuesLabels": [
                "inny"
            ],
            "valuesIds": [
                "208602_236402"
            ],
            "values": null,
            "unit": null,
            "options": {
                "identifiesProduct": true
            }
        },
        {
            "id": "225693",
            "name": "EAN",
            "valuesLabels": [
                "5060620944660"
            ],
            "values": [
                "5060620944660"
            ],
            "unit": null,
            "options": {
                "identifiesProduct": true,
                "isGTIN": true
            }
        },
        {
            "id": "202269",
            "name": "Liczba sztuk",
            "valuesLabels": [
                "inna"
            ],
            "valuesIds": [
                "202269_210981"
            ],
            "values": null,
            "unit": null,
            "options": {
                "identifiesProduct": false
            }
        },
        {
            "id": "215858",
            "name": "Numer katalogowy części",
            "valuesLabels": [
                "BA15SSMD-Rx5"
            ],
            "values": [
                "BA15SSMD-Rx5"
            ],
            "unit": null,
            "options": {
                "identifiesProduct": false
            }
        }
    ],
    "images": [
        {
            "url": "https://a.allegroimg.com/original/119247/d50959f64c568b3cd1421c70f31e"
        },
        {
            "url": "https://a.allegroimg.com/original/1112b4/d03b421247169a2835880cc39d88"
        }
    ],
    "offerRequirements": {
        "id": null,
        "parameters": []
    },
    "compatibilityList": null,
    "tecdocSpecification": null,
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<h2>5 x CZERWONA 12v 24v 382 BA15S R5W 245207 Żarówka LED Nieprzezroczysta matowa soczewka</h2>"
                    }
                ]
            },
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<ul><li>Wrażliwe na brak polaryzacji 300</li>\n<li>lm na żarówkę 12-30V działają zarówno w samochodach 12 V, jak i ciężarówkach 24 V</li></ul>"
                    },
                    {
                        "type": "IMAGE",
                        "url": "https://a.allegroimg.com/original/119247/d50959f64c568b3cd1421c70f31e"
                    }
                ]
            },
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Nazwa koloru:\nczerwony\n\n\n\n\n\n\n | \n\nNazwa rozmiaru:\nPakiet 5\n\n\n\n\n\n\n10-30 V napięcia roboczego, będzie działać zarówno na 12 v, jak i 24 v.\nNiezwykle jasne, niepolarne, super jasne, 6 x 2865 chipów SMD na żarówkę\nNieprzezroczysta konstrukcja zapewnia równomierny strumień światła!\nDostępne w kolorze czerwonym, chłodnym białym, bursztynowym \nNie są przyjazne dla Canbus i mogą pokazywać błąd zerwania żarówki na desce rozdzielczej\nPojedyncze włókno z przeciwległymi pinami 300 lm na żarówkę\nZgodne z numerami części:\nBA15S\n382\nP21\n207\n245\n1156\nR5W\nZwykle używane jako:\nŚwiatło stop lub tylne\nTylne światło przeciwmgielne\nPrzednie\nkierunkowskazy DRL\nZnaczniki boczne\nPrzednie światła postojowe</p>"
                    }
                ]
            }
        ]
    }
}
```

Następnie za pomocą: [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/editProductOffers) możesz edytować ofertę, przekazując wartość product.id.

Poniżej przykładowy request:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/7680042192’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ’{
  "productSet": [{
        "product": {
             "id": "0475a562-fbbb-4260-b772-59a82aa96554"
        }
  }]
 }'
```

Przykładowy response:

```
{
    "id": "7680042192",
    "name": "Żarówka samochodowa LED",
    "productSet": [{
        "product": {
            "id": "0475a562-fbbb-4260-b772-59a82aa96554",
            "publication": {
                "status": "NOT_LISTED"
        },
        "parameters": [
                {
                        "id": "234925",
                        "name": "Testowy tytuł",
                        "values": [
                            "Test LP9"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    }, ...
            ]
        },
        "quantity": {
                "value": 1
            }
    }],
    "parameters": [
        {
            "id": "11323",
            "name": "State",
            "values": [
                "New"
            ],
            "valuesIds": [
                "11323_1"
            ],
            "rangeValue": null
        }
    ],
    "afterSalesServices": {
        "impliedWarranty": {
            "id": "f4f3541e-41c2-481f-938a-2a1b8c0ce65a"
        },
        "returnPolicy": {
            "id": "7068910b-29b9-449b-8ad0-99625a6312db"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "NO_INVOICE"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": 100,
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 3,
        "unit": "UNIT"
    },
    "location": {
        "countryCode": "PL",
        "province": "WIELKOPOLSKIE",
        "city": "Poznań",
        "postCode": "60-166"
    },
    "delivery": {
        "shippingRates": {
            "id": "7dd8049c-1753-4842-8870-e29a2efc3d62"
        },
        "handlingTime": "PT48H",
        "additionalInfo": ""
    },
    "publication": {
        "duration": null,
        "status": "ACTIVE",
        "endedBy": null,
        "endingAt": null,
        "startingAt": null,
        "republish": false
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<h2>5 x CZERWONA 12v 24v 382 BA15S R5W 245207 Żarówka LED Nieprzezroczysta matowa soczewka</h2>"
                    }
                ]
            },
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<ul><li>Wrażliwe na brak polaryzacji 300</li>\n<li>lm na żarówkę 12-30V działają zarówno w samochodach 12 V, jak i ciężarówkach 24 V</li></ul>"
                    },
                    {
                        "type": "IMAGE",
                        "url": "https://a.allegroimg.allegrosandbox.pl/original/119247/d50959f64c568b3cd1421c70f31e"
                    }
                ]
            },
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Nazwa koloru:\nczerwony\n\n\n\n\n\n\n | \n\nNazwa rozmiaru:\nPakiet 5\n\n\n\n\n\n\n10-30 V napięcia roboczego, będzie działać zarówno na 12 v, jak i 24 v.\nNiezwykle jasne, niepolarne, super jasne, 6 x 2865 chipów SMD na żarówkę\nNieprzezroczysta konstrukcja zapewnia równomierny strumień światła!\nDostępne w kolorze czerwonym, chłodnym białym, bursztynowym \nNie są przyjazne dla Canbus i mogą pokazywać błąd zerwania żarówki na desce rozdzielczej\nPojedyncze włókno z przeciwległymi pinami 300 lm na żarówkę\nZgodne z numerami części:\nBA15S\n382\nP21\n207\n245\n1156\nR5W\nZwykle używane jako:\nŚwiatło stop lub tylne\nTylne światło przeciwmgielne\nPrzednie\nkierunkowskazy DRL\nZnaczniki boczne\nPrzednie światła postojowe</p>"
                    }
                ]
            }
        ]
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2021-03-16T14:01:53.434Z"
    },
    "createdAt": "2021-02-24T07:01:55Z",
    "updatedAt": "2021-03-16T14:01:53.793Z",
    "images": [
        "https://a.allegroimg.allegrosandbox.pl/original/119247/d50959f64c568b3cd1421c70f31e",
        "https://a.allegroimg.allegrosandbox.pl/original/1112b4/d03b421247169a2835880cc39d88"
    ],
    "external": null,
    "category": {
        "id": "257359"
    },
    "taxSettings": null,
    "sizeTable": null,
    "discounts": {
        "wholesalePriceList": null
    },
    "b2b": {
        "buyableOnlyByBusiness": false
    }
}
```

Zwróć uwagę na pola, które uległy zmianie. Po połączeniu oferty z produktem, w response otrzymujesz product.id oraz nowe wartości pól: description i images, które pobraliśmy bezpośrednio z danych zawartych w produkcie.

#### Obsługa GPSR

Do oferty automatycznie dołączymy informacje o GPSR z produktu (responsibleProducer oraz safetyInformation), jeśli w strukturze przekażesz pole product.id:

```
 {
    "productSet": [{
       "product": {
          "id": "0475a562-fbbb-4260-b772-59a82aa96554"
    }
  }]}
```

Jeśli chcesz zachować informacje o GPSR, które aktualnie posiadasz zapisane w ofercie, uwzględnij w strukturze również pola productSet.[].responsibleProducer i productSet.[].safetyInformation:

```
{
  "productSet": [
    {
    "id": "0475a562-fbbb-4260-b772-59a82aa96554"
    },
      "responsibleProducer": {
          "id": "54918390-7452-4452-8b7b-bf507a2db074"
         },
      "safetyInformation": {
           "description": "Lista ostrzeżeń dotyczących 
           bezpieczeństwa ...",
           "type": "TEXT"
         },
  ...
}
```

#### Obsługa zdjęć

Do oferty automatycznie dołączymy zdjęcia z produktu, jeśli w strukturze przekażesz tylko product.id:

```
  {
    "productSet": [{
       "product": {
          "id": "0475a562-fbbb-4260-b772-59a82aa96554"
    }
  }]}
```

Jeśli chcesz w ofercie zaprezentować wyłącznie własne zdjęcia, bez obrazków, które pochodzą z naszej bazy produktowej, przekaż dodatkowo w polu product.images pustą tablicę:

```
  {
    "productSet": [{
       "product": {
          "id": "0475a562-fbbb-4260-b772-59a82aa96554",
          "images": []
    }}],
    …
    "images": [
        "https://...zewnetrzny-adres-pierwszego-obrazka.jpeg",    // zdjęcia, które są aktualnie przypisane do oferty    
        "https://...zewnetrzny-adres-drugiego-obrazka.jpeg"
    ]
   }
```

W ten sposób w ofercie pozostaną tylko zdjęcia ofertowe, zawarte w sekcji images. Jeśli nie przekazałbyś zdjęć, które są aktualnie przypisane do oferty w polu images, to zdjęcia zostałyby usunięte z oferty. Jeśli oferta nie posiada żadnych zdjęć, a chcesz je dodać wraz z przypisaniem produktu, przekaż także powyższą strukturę.

#### Zmiana statusu oferty

Dzięki [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/editProductOffers) możesz także zmienić status oferty - jako osobna operacja lub w jednej operacji wraz z edycją oferty. Nie musisz dodatkowo korzystać z zasobu do publikacji oferty. Wystarczy, że w polu publication.status przekażesz odpowiednią wartość:

- ENDED - zakończ ofertę.
- ACTIVE - aktywuj ofertę,

Przykładowy request:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ’{
  "sellingMode": {
     "price": {
      "amount": "101",
      "currency": "PLN"
    }
  },
  "publication": {
        "status": "ENDED"
    }
}’
```

Ważne! Jeśli w strukturze żądania zawrzesz w polu status wartość ENDED, to zakończymy ofertę, nawet jeśli edycja innych pól się nie powiedzie.

Jeżeli oferta jest w statusie INACTIVE, to aby ją aktywować przekaż wartość ACTIVE w polu publication.status.

Przykładowy request:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ‘{
  "publication": {
        "status": "ACTIVE"
    }
}’
```

#### Jak usunąć dane

Jeżeli chcesz usunąć wartość w wybranym polu, o ile nie jest ona wymagana - przekaż w nim wartość null.

Przykładowy request - jak usunąć informacje o gwarancji:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ‘{
      "warranty": {
            "id": null
     }
}’
```

Przykładowy respone:

```
{
    …
     "warranty": {
            "id": null
     }
    …
}
```

Przykładowy request - jak usunąć informację o liczbie sztuk:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ‘{
      "stock": null
}’
```

Przykładowy respone:

```
{
    …
    "stock": null
    …
}
```

Przykładowy request - jak usunąć zdjęcia:

```
curl -X PATCH
‘https://api.allegro.pl/sale/product-offers/9531382307’
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d ‘{
      “images”: null   // analogicznie możesz użyć []
}’
```

Przykładowy respone:

```
{
    …
     "images": []
    …
}
```

### Edycja wielu ofert jednocześnie

W pojedynczym wywołaniu możesz wyedytować do 1000 ofert.

#### Cena

[PUT /sale/offer-price-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/priceModificationCommandUsingPUT)- tym zasobem zlecisz zmianę ceny w wybranych ofertach. W commandId podaj wartość w formacie UUID - wygeneruj go we własnym zakresie. Musisz być zautoryzowany jako sprzedawca, który wystawił te oferty. Udostępniamy poniższe typy modyfikacji ceny:

##### Zmiana ceny w ofertach - wartościowo

Przykładowy request:

```
  curl -X PUT \
  'https://api.allegro.pl/sale/offer-price-change-commands/{CommandId}' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
    "modification":{
        "type":"FIXED_PRICE",    // dostępne wartości: "FIXED_PRICE" (zmiana ceny na podaną wartość), "INCREASE_PRICE" (zwiększenie ceny o podaną wartość), "DECREASE_PRICE" (zmniejszenie ceny o podaną wartość)
        "marketplaceId": "allegro-pl",    // serwis allegro na którym chcesz zmienić cenę
        "price":{    // jeśli jako "type" wybierzesz "INCREASE_PRICE" lub "DECREASE_PRICE", zmień nazwę tego pola na "value"
            "amount":"10.50",    // wartość zmiany ceny. 
            "currency":"PLN"
           }
        },
    "offerCriteria":[
        {
          "type":"CONTAINS_OFFERS",
          "offers":[     // lista ofert w których chcesz dokonać zmian
           {
             "id":"7660573029"
           },
           {
             "id":"7644576839"
           }
          ]
        }
     ]
  }'
```

##### Zmiana ceny w ofertach o podany procent

Przykładowy request:

```
  curl -X PUT \
  https://api.allegro.pl/sale/offer-price-change-commands/{CommandId} \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
    "modification":{
        "type":"INCREASE_PERCENTAGE",    // dostępne wartości: INCREASE_PERCENTAGE" (zwiększenie ceny o podany %), "DECREASE_PERCENTAGE" (zmniejszenie ceny o podany %
        "marketplaceId": "allegro-pl"    // serwis allegro na którym chcesz zmienić cenę
        "percentage": 10    // procent o jaki chcesz zwiększyć lub zmniejszyć cenę
        },
    "offerCriteria":[
        {
          "type":"CONTAINS_OFFERS",
          "offers":[     // lista ofert w których chcesz dokonać zmian
           {
             "id":"7660573029"
           },
           {
             "id":"7644576839"
           }
          ]
        }
     ]
  }'
```

Przykładowy response dla edycji ceny:

```
  {
    "id": "aacfb40c-daca-4252-91ef-244d68d28123",
    "createdAt": "2019-08-24T14:15:22Z",  - data utworzenia zadania
    "completedAt": null,    // data realizacji zadania. Dla tej metody zawsze zwrócimy null
    "taskCount": {    // do momentu rozpoczęcia przetwarzania pokazujemy wartość 0, dopiero po chwili pojawią się właściwe liczby ofert do przetworzenia
            "total": 0,
            "success": 0,
            "failed": 0
    }
  }
```

[GET /sale/offer-price-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getPriceModificationCommandStatusUsingGET) Przy pomocy tego zasobu dowiesz się, w ilu ofertach wprowadziliśmy zmiany w ramach podanego [{commandId}](https://developer.allegro.pl/command/). Otrzymasz zestawienie, przy ilu ofertach edycja przebiegła pomyślnie, a przy ilu zakończyła się niepowodzeniem. Musisz być zautoryzowany jako sprzedawca, który wystawił te oferty.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/offer-price-change-commands/{commandId}' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
    "id": "aacfb40c-daca-4252-91ef-244d68d28123",
    "createdAt": "2019-08-24T14:15:22Z",
    "completedAt": "2019-08-24T14:15:22Z",
    "taskCount": {
        "total": 2,     // liczba ofert, w których zleciłeś edycję
        "success": 2,    // liczba ofert, w których zmiany zostały wprowadzone
        "failed": 0     // liczba ofert, w których zmiany nie zostały wprowadzone
    }          
  }
```

[GET /sale/offer-price-change-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getPriceModificationCommandTasksStatusesUsingGET) Tym zasobem sprawdzisz statusy zadań operacji grupowej zmiany ceny w ramach jednego {commandId}. W odpowiedzi otrzymasz listę edytowanych ofert ze statusem i czasem edycji. Musisz być zalogowany jako sprzedawca, który wystawił te oferty. Dla tego zasobu można skorzystać z parametrów, które pozwolą pobrać odpowiednie porcje danych:

limit by określić liczbę ofert na liście (przyjmuje wartości od 1 do 1000),

offset by wskazać miejsce, od którego chcesz pobrać kolejną porcję danych (domyślnie 0).

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/offer-price-change-commands/aacfb40c-daca-4252-91ef-244d68d28123/tasks' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
    "tasks": [
        {
            "offer": {
                "id": "7644576839"    // identyfikator oferty
            },
            "message": "",
            "status": "SUCCESS",    // status wykonanej edycji
            "field": "price"    // pole, które edytowałeś
        },
        {
            "offer": {
                "id": "7660573029"
            },
            "message": "",
            "status": "SUCCESS",
            "field": "price"
        }
    ]
 }
```

#### Liczba przedmiotów

[PUT /sale/offer-quantity-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/quantityModificationCommandUsingPUT)- tym zasobem zlecisz operację grupową zmiany liczby przedmiotów w wybranych ofertach. W commandId podaj wartość w formacie UUID - wygeneruj go we własnym zakresie. Musisz być zautoryzowany jako sprzedawca, który wystawił te oferty.

Przykładowy request:

```
  curl -X PUT \
  'https://api.allegro.pl/sale/offer-quantity-change-commands/{commandId}' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -d '{
    "modification":{
        "changeType":"FIXED",    // dostępne wartości: “FIXED” (docelowa liczba sztuk w ofercie), “GAIN” (dodaj/odejmij od liczby przedmiotów w ofercie. By odjąć wpisz w polu value wartość z minusem)
        "value":30    // wartość na jaką (FIXED) lub o jaką (GAIN) chcesz zmienić liczbę sztuk w ofercie       
            },
    "offerCriteria":[
    {
        "type":"CONTAINS_OFFERS",
        "offers":[    // lista ofert w których chcesz dokonać zmian
         {
           "id":"7660573029"
         },
         {
           "id":"7644576839"
         }
        ]
     }
    ]
 }'
```

Przykładowy response:

```
  {
    "id": "e476171a-18b1-44e5-81d1-d142b86ff13d",
    "createdAt": "2019-08-24T14:15:22Z", - data utworzenia zadania
    "completedAt": null, - data realizacji zadania. Dla tej metody zawsze zwrócimy null.
    "taskCount": {     // do momentu rozpoczęcia przetwarzania pokazujemy wartość 0, dopiero po chwili pojawią się właściwe liczby ofert do przetworzenia
            "total": 0,
            "success": 0,
            "failed": 0
    }
  }
```

[GET /sale/offer-quantity-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getQuantityModificationCommandStatusUsingGET)- użyj tego zasobu, by sprawdzić ogólny status zleconej operacji grupowej zmiany liczby przedmiotów w ramach jednego {commandId}. Musisz być zalogowany jako sprzedawca, który wystawił te oferty.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/offer-quantity-change-commands/e476171a-18b1-44e5-81d1-d142b86ff13d' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
    "id": "e476171a-18b1-44e5-81d1-d142b86ff13d",
    "createdAt": "2019-08-24T14:15:22Z",
    "completedAt": "2019-08-24T14:15:22Z",
    "taskCount": {
        "total": 2,    // liczba ofert, w których zleciłeś edycję
        "success": 2,    // liczba ofert, w których zmiany zostały wprowadzone
        "failed": 0    // liczba ofert, w których zmiany nie zostały wprowadzone
    }          
  }
```

[GET /sale/offer-quantity-change-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getQuantityModificationCommandTasksStatusesUsingGET) użyj tego zasobu, by sprawdzić statusy zadań operacji grupowej zmiany liczby przedmiotów w ramach jednego [{commandId}](https://developer.allegro.pl/command/). Musisz być zalogowany jako sprzedawca, który wystawił te oferty. Dla tego zasobu można skorzystać z parametrów, które pozwolą pobrać odpowiednie porcje danych:

limit by określić liczbę ofert na liście (domyślnie 100, min.1 max 1000),

offset by wskazać miejsce, od którego chcesz pobrać kolejną porcję danych (domyślnie 0).

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/offer-quantity-change-commands/e476171a-18b1-44e5-81d1-d142b86ff13d/tasks' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
    "tasks": [
        {
            "offer": {
                "id": "7644576839"    // dentyfikator oferty
            },
            "message": "",
            "status": "SUCCESS",    // status wykonanej edycji
            "field": "quantity"    // pole, które edytowałeś
        },
        {
            "offer": {                    
                "id": "7660573029"
            },
            "message": "",
            "status": "SUCCESS",
            "field": "quantity"
        }
    ]
  }
```

[PUT /sale/offer-modification-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/modificationCommandUsingPUT)- to zasób, którym wyedytujesz wiele ofert na raz. W commandId podaj wartość w formacie UUID - wygeneruj go we własnym zakresie. Musisz być zautoryzowany jako sprzedawca, który wystawił te oferty.

Możesz grupowo zmienić tylko jeden element podczas jednego requestu.

#### Cennik dostawy

Przykładowy request dla zmiany cennika dostawy:

```
  curl -X PUT \
  'https://api.allegro.pl/sale/offer-modification-commands/{commandId}' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
    "modification":
        {
            "delivery": {
                "shippingRates": {
                "id": "4b9ad5b9-7ee9-409b-86f5-578672c13df8"    // numer identyfikacyjny cennika dostawy, pobierzesz go za pomocą metody GET /sale/shipping-rates Przed przypisaniem cennika dostawy uzupełnij pole "location". Dla formatu sprzedaży typu ADVERTISEMENT(ogłoszenie) zostaw to pole puste - prześlij "delivery": null
                }
            }
        },
      "offerCriteria":[
        {
            "type":"CONTAINS_OFFERS",
            "offers":[
                {
                  "id":"7531636067"
                },
                {
                  "id":"7512439587"
                }
            ]
        }
     ]
   }'
```

Przykładowy response:

```
 {
    "id": "30354f98-6788-4db6-83c4-1e7e404dc137",    // {commandId} - wartość, którą podasz w zapytaniu. Na jej podstawie możesz sprawdzić stan wprowadzanych zmian
   "createdAt": "2019-08-24T14:15:22Z",    // data utworzenia zadania
   "completedAt": null,    // data realizacji zadania. Dla tej metody zawsze zwrócimy null.
    "taskCount": {    // do momentu rozpoczęcia przetwarzania pokazujemy wartość 0, dopiero po chwili pojawią się właściwe liczby ofert do przetworzenia
        "total": 0,                         
        "success": 0,
        "failed": 0
    }
  }
```

[GET /sale/offer-modification-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getGeneralReportUsingGET) Przy pomocy tego zasobu dowiesz się, w ilu ofertach wprowadziliśmy zmiany w ramach podanego [{commandId}](https://developer.allegro.pl/command/). Otrzymasz zestawienie, przy ilu ofertach edycja przebiegła pomyślnie, a przy ilu zakończyła się niepowodzeniem. Musisz być zautoryzowany jako sprzedawca, który wystawił te oferty.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/offer-modification-commands/{commandId}'
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
    "id": "6666c97f-0d32-4747-8a17-1da38f9499de",
    "createdAt": "2019-08-24T14:15:22Z",
    "completedAt": "2019-08-24T14:15:22Z",
    "taskCount": {
        "total": 2,    // liczba ofert, w których zleciłeś edycję
        "success": 2,    // liczba ofert, w których zmiany zostały wprowadzone
        "failed": 0    // liczba ofert, w którychzmiany nie zostały wprowadzone
    }          
  }
```

[GET /sale/offer-modification-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getTasksUsingGET) Tym zasobem pobierzesz raport zmian, których dokonałeś w wielu ofertach dla danego [{commandId}](https://developer.allegro.pl/command/). Znajdziesz w nim informacje, czy edycja zakończyła się sukcesem, czy nie, a także pola w których dokonałeś edycji. Musisz być zautoryzowany jako sprzedawca, który wystawił te oferty.

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/offer-modification-commands/{commandId}/tasks'
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
    "tasks": [
        {
            "offer": {
                "id": "7512439587"    // numer identyfikacyjny oferty
            },
            "message": "",
            "status": "SUCCESS",
            "field": "shippingRates"    // pole, które edytowałeś
        },
        {
            "offer": {
                "id": "7531636067"
            },
            "message": "",
            "status": "SUCCESS",
            "field": "shippingRates"
        }
    ]
  }
```

Poza cennikami dostawy, za pomocą tego zasobu dodasz lub zmienisz:

#### Czas wysyłki

```
  {
    "modification":
        {
            "delivery": {
                "handlingTime": "P7D"    // czas wysyłki w formacie ISO 8601
            }
        },
      "offerCriteria":[
        {
            "type":"CONTAINS_OFFERS",
            "offers":[
                {
                  "id":"7531636067"
                },
                {
                  "id":"7512439587"
                }
            ]
        }
     ]
   }'
```

#### Cennik hurtowy

```
  {
    "modification": {
    "discounts": {     // typ zmiany
      "wholesalePriceList": {                    
       "id": "9de4be5d-9c60-48aa-8711-363625c9d793"    // identyfikator cennika
      }
    }
  },
  "offerCriteria":[
      {
        "type":"CONTAINS_OFFERS",
        "offers":[
         {
           "id":"9292002929"    // identyfikator oferty
         },
         {
           "id":"9876543210"
         }
        ]
      }
   ]
  }
```

#### Tabele rozmiarów

```
  {
    "modification": {
    "sizeTable": {          
      "id": "de2689bc-3d47-11e8-811c-246e9677f638"    // identyfikator tabeli rozmiarów, pobierzesz go przy pomocy metody GET /sale/size-tables
     }
    },
    "offerCriteria":[
      {
        "type":"CONTAINS_OFFERS",
        "offers":[
         {
           "id":"7531636067"
         },
         {
           "id":"7512439587"
         }
       ]
      }
    ]
  }
```

#### Informacje o fakturze

```
  {
    "modification": {
    "payments": {
      "invoice": "VAT",    // informacja o fakturze; dostępne są 4 wartości: VAT (faktura VAT); VAT_MARGIN (faktura VAT marża); WITHOUT_VAT (faktura bez VAT); NO_INVOICE (nie wystawiam faktury)   
      "tax": {    // stawka podatku VAT, możesz określić tylko, gdy jako typ faktury wybrana jest opcja "VAT", dostępne wartości: 0%, 5%, 8%, 23%
         "percentage": "23.00"
      }
    }
   },
    "offerCriteria":[
      {
        "type":"CONTAINS_OFFERS",
        "offers":[
         {
        "  id":"7531636067"
         },
         {
          "id":"7512439587"
         }
       ]
     }
    ]
 }
```

#### Usługi dodatkowe

```
 {
    "modification": {
        "additionalServicesGroup": {    // określa grupę usług dodatkowych jaką chcesz przypisać do ofert
        "id": "240e22a8-9e57-4fc2-b386-8b5ac1aeaa34"    // identyfikator grupy usług dodatkowych pobierzesz go przy pomocy metody: GET /sale/offer-additional-services/groups
     }
   },
     "offerCriteria":[
      {
        "type":"CONTAINS_OFFERS",
        "offers":[
         {
          "id":"7531636067"
         },
         {
          "id":"7512439587"
         }
       ]
      }
    ]
}
```

#### Czas trwania oferty

W statusie INACTIVE w ofertach typu Kup Teraz i w licytacjach możesz dowolnie zmienić czas trwania.

W statusie ACTIVE:

w licytacjach nie możesz zmienić czasu trwania;

w ofertach typu Kup Teraz czas trwania możesz zmienić jedynie na „do wyczerpania przedmiotów”.

W statusie ENDED:

w licytacjach nie możesz zmienić czasu trwania;

w ofertach typu Kup Teraz czas trwania możesz zmieniać dowolnie - na „do wyczerpania przedmiotów” lub na określony czas trwania. Pamiętaj, że po tej zmianie musisz aktywować ofertę, by była widoczna w serwisie.

Możesz ustawić wartość dla jednego z dwóch parametrów:

duration - czas trwania w formacie ISO8601, np. “PT72H”;

durationUnlimited - czas trwania do wyczerpania przedmiotów;

W przypadku, gdy prześlesz dwa parametry, API zwróci błąd walidacji.

Przykładowy request - ustawienie określonego czasu trwania:

```
 {
    "modification": {
        "publication": {
            "duration": “PT720H”                       
        }
    },
    "offerCriteria": [
        {
        "offers": [
            {
                "id": "8360057987"
            }
        ],
                "type": "CONTAINS_OFFERS"
        }
    ]
 }
```

Przykładowy request - ustawienie opcji do wyczerpania zapasów:

```
 {
    "modification": {
        "publication": {
            "durationUnlimited": true                      
        }
    },
    "offerCriteria": [
        {
        "offers": [
            {
                "id": "8360057987"
            }
        ],
                "type": "CONTAINS_OFFERS"
        }
    ]
 }
```

#### Lokalizacja

```
 {
          "modification": {
              "location": {
                  "countryCode": "PL",    // kod kraju
                  "province": "wielkopolskie",     // województwo (wymagane dla kraju PL)
                  "city": "Poznań",    // miejscowość
                  "postCode": "60-166"    // kod pocztowy (wymagane dla kraju PL)
                  }
          },
          "offerCriteria": [
              {
                  "offers": [
                      {
                             "id": "11223344556"
                      },
                      {
                             "id": "11335577991"
                      }
                  ],
                  "type": "CONTAINS_OFFERS"
              }
          ]
 }
```

#### Dane teleadresowe producenta

```
{
    "modification": {
            "responsibleProducer": {
               "id": "59a8b818-0a38-4540-92f4-3645923cb9c6" // identyfikator danych teleadresowych pobrany z GET /sale/responsible-producers lub GET /sale/responsible-producers/{id}
            }
    },
    "offerCriteria": [
            {
               "offers": [    // lista ofert, w których chcesz dokonać zmian
                  {
                        "id": "11223344556"
                  },
                  {
                        "id": "11335577991"
                  }
               ],
               "type": "CONTAINS_OFFERS"
            }
    ]
}
```

Uwaga! Grupowo dane teleadresowe producentów produktów zmienisz tylko dla pierwszego produktu w zestawie (productSet).

#### Osoba odpowiedzialna za zgodność produktu z przepisami unijnymi

```
{
    "modification": {
            "responsiblePerson": {
               "id": "817ab828-255e-4ca8-a4da-c6defa3e6918"    // identyfikator osoby odpowiedzialnej pobrany z GET /sale/responsible-persons
            }
    },
    "offerCriteria": [        
            {
               "offers": [    // lista ofert, w których chcesz dokonać zmian
                  {
                        "id": "11223344556"
                  },
                  {
                        "id": "11335577991"
                  }
               ],
               "type": "CONTAINS_OFFERS"
            }
    ]
}
```

Uwaga! Grupowo osobę odpowiedzialną za zgodność produktu z przepisami unijnymi zmienisz tylko dla pierwszego produktu w zestawie (productSet).

#### Informacje o bezpieczeństwie produktu

```
{
    "modification": {
            "safetyInformation": {
               "type": "TEXT",     // dostępne wartości: TEXT, ATTACHMENTS
               "description": "To jest informacja o bezpieczeństwie produktu.\n Jedná se o bezpečnostní informace o výrobku."
            }
    },
    "offerCriteria": [        
            {
               "offers": [     // lista ofert, w których chcesz dokonać zmian
                  {
                        "id": "11223344556"
                  },
                  {
                        "id": "11335577991"
                  }
               ],
               "type": "CONTAINS_OFFERS"
            }
    ]
}
```

Uwaga! Grupowo informacje o bezpieczeństwie produktu zmienisz tylko dla pierwszego produktu w zestawie (productSet).

### Reguły cenowe

Reguły cenowe to funkcjonalności, które pozwalają Ci zarządzać ceną oferty bez edytowania jej ręcznie. Możesz samodzielnie ustawić sposób, w jaki ceny będą się zmieniać.

Za pomocą wybranego typu reguł możesz automatycznie zmieniać swoje ceny na rynku rejestracji i na rynkach zagranicznych. Reguły ustawisz osobno dla każdego rynku, na którym dana oferta jest widoczna. Oznacza to, że z jedną ofertą możesz połączyć kilka reguł.

Ważne! Gdy w ofercie korzystasz z reguł cenowych, ale zdecydujesz się ustawić w niej własną cenę – automatycznie wyłączymy daną regułe w tej ofercie.

Nie zmieniamy automatycznie cen w ofertach, które aktualnie biorą udział w kampaniach lub programach wpływających na cenę bazową oferty. Dzięki temu tymczasowe obniżki nie wpłyną na Twoją politykę cenową. Gdy Twoja oferta zakończy udział w kampanii, ponownie zaczniemy stosować w niej wybraną regułę cenową.

#### Jakie typy reguł cenowych możesz połączyć z ofertami

Możesz skorzystać z gotowych typów reguł:

"EXCHANGE_RATE" (Przelicznik cen) - aby zmieniać ceny tylko na rynkach zagranicznych na podstawie informacji o kursach publikowanych przez Europejski Bank Centralny.

"FOLLOW_BY_ALLEGRO_MIN_PRICE" (Najniższa cena na Allegro) - aby zmieniać ceny na swoim rynku rejestracji oraz na rynkach zagranicznych w oparciu o najniższą cenę danego produktu na Allegro.

"FOLLOW_BY_MARKET_MIN_PRICE" (Najniższa cena na rynku) - aby zmieniać ceny na swoim rynku rejestracji oraz na rynkach zagranicznych, w oparciu o najniższą cenę danego produktu na Allegro oraz w innych sklepach internetowych. Jeśli nie posiadamy takiej ceny, weźmiemy pod uwagę cenę Top Oferty (jeśli istnieje). Szczegóły znajdziesz poniżej, w opisie działania reguły.

“FOLLOW_BY_TOP_OFFER_PRICE” (Top Oferta) - aby zmieniać ceny na swoim rynku rejestracji oraz na rynkach zagranicznych (bez rynków B2B), w oparciu o cenę Top Oferty danego produktu.

Na podstawie powyższych typów możesz też tworzyć własne reguły cenowe.

##### Jak obliczamy ceny dla reguły “EXCHANGE_RATE”

Ceny obliczamy na podstawie informacji o kursach publikowanych przez Europejski Bank Centralny.

Podane przez Ciebie ceny w walucie serwisu bazowego przeliczamy na walutę serwisu dodatkowego według wzoru:

cena w walucie serwisu bazowego x kurs walut = cena w walucie serwisu dodatkowego

Europejski Bank Centralny publikuje informacje o kursie walut raz dziennie. Dlatego gdy skorzystasz z przelicznika cen, zaktualizuje on ceny na podstawie informacji o kursie z poprzedniego dnia roboczego, np. Europejski Bank Centralny publikuje dane o 16:21 w piątek. Na Allegro nowy kurs obowiązuje od godziny 00:00:01 w poniedziałek, aż do wtorku 00:00:01 (obowiązuje strefa czasowa CET/CEST).

Dodatkowe informacje:

- gdy wznawiasz ofertę z włączonym przelicznikiem cen, zaktualizujemy w niej cenę w walucie serwisu dodatkowego zgodnie z aktualnym kursem.
- przelicznik wylicza cenę w serwisach dodatkowych na podstawie ceny w serwisie bazowym. Nie uwzględnia cen, które zostały obniżone w związku z udziałem w kampaniach i programach,
- ceny w ofertach, które są widoczne w serwisach dodatkowych, przeliczymy automatycznie zawsze, gdy zmienisz cenę w serwisie bazowym,

Przykład

Dla rynku allegro.sk ustawiasz regułę cenową, która:

- korzysta z Przelicznika cen, aby przeliczyć tę kwotę na euro po aktualnym kursie.
- dodaje 10% do ceny w złotówkach

##### Jak działają reguły cenowe typu “FOLLOW_BY_ALLEGRO_MIN_PRICE”

Reguła cenowa “FOLLOW_BY_ALLEGRO_MIN_PRICE” automatycznie zmienia cenę w Twojej ofercie na podstawie:

- zakresu cen, w ramach którego chcesz zmieniać swoją cenę - jest to warunek, który musi zostać spełniony. Jeśli nie podasz zakresu, uwzględnimy regułę w ofercie, jednak nie będziemy przeliczać cen. Dla rynków zagranicznych możesz podać zakres w walucie tego rynku lub w walucie Twojego rynku rejestracji
- aktualnie najniższej ceny danego produktu na Allegro, którą sprawdzamy co godzinę
- Twojej ceny produktu w tej ofercie
- Zastosujemy wtedy Twoją regułę, aby zaktualizować cenę w euro. Po dodaniu 10% do nowej ceny w złotówkach otrzymamy 15,40 zł – tę kwotę przeliczymy po aktualnym kursie (1 PLN = 0,246 EUR). Nowa cena na allegro.sk wyniesie zatem 3,79 EUR.

###### Jak ustalamy najniższą cenę dla danego produktu

Najniższą cenę produktu na Allegro ustalamy cyklicznie – raz na godzinę.

Najniższą cenę określamy na podstawie ofert z danym produktem, które spełniają poniższe warunki:

są wystawione przez aktywnego sprzedającego, który:

- wystawia fakturę VAT.
- ma co najmniej Neutralny poziom jakości sprzedaży

Nie wyznaczamy najniższej ceny dla produktów, których rozbieżności w cenie są zbyt duże. Przykładowo, jeśli różnica między najwyższą i najniższą ceną danego produktu to ponad 50% – nie wyznaczymy dla niego najniższej ceny na Allegro.

Sprawdzamy, czy zmiana najniższej ceny nie przekracza 30% mediany z ostatnich 14 dni. W ten sposób upewniamy się, że nie porównujesz swojej ceny z ograniczonymi liczbowo wyprzedażami.

Gdy dla danego produktu pojawi się nowa najniższa cena na Allegro, zaktualizujemy cenę w Twojej ofercie. Zrobimy to tylko w ramach zakresu cen, który podasz dla tej oferty.

Przykład 1

1. Najniższa cena na Allegro mieści się w Twoim zakresie cen – dlatego zaktualizujemy cenę oferty na 16 zł.
2. Aktualna najniższa cena danego produktu na Allegro to 16 zł.
3. Dla oferty z ceną 20 zł ustawiasz regułę cenową typu “FOLLOW_BY_ALLEGRO_MIN_PRICE”. Podajesz zakres cen dla tej oferty: od 15 do 25 zł.

Przykład 2

1. Najniższa cena na Allegro nie mieści się w Twoim zakresie cen – dlatego ustawimy w ofercie najniższą możliwą cenę z tego zakresu: 18 zł.
2. Aktualna najniższa cena danego produktu na Allegro to 16 zł.
3. Dla oferty z ceną 20 zł ustawiasz regułę cenową typu “FOLLOW_BY_ALLEGRO_MIN_PRICE”. Podajesz zakres cen dla tej oferty: od 18 do 25 zł.

Jeśli nie podasz zakresu cen, nie będziemy stosować reguł i aktualizować ceny w ofercie. W ten sposób chronimy Cię przed automatyczną obniżką poniżej kwoty, która jest dla Ciebie opłacalna.

###### Kiedy aktualizujemy ceny w ofertach z regułą “FOLLOW_BY_ALLEGRO_MIN_PRICE”

Pierwszy raz zaktualizujemy cenę Twojej oferty na wybranym rynku, gdy połączysz ją z regułą cenową “FOLLOW_BY_ALLEGRO_MIN_PRICE” i ustawisz zakres cen.

Od tego czasu będziemy aktualizować cenę oferty za każdym razem, gdy:

- kurs walut zmieni się w taki sposób, że wpływa na cenę w walucie wybranego rynku – jeśli zdefiniujesz zakres cen w walucie rynku rejestracji.
- edytujesz regułę cenową połączoną z ofertą
- zmienisz zakres cen dla tej oferty
- zmienisz coś w tej ofercie – na przykład status oferty, jej widoczność na rynkach zagranicznych lub produkt w Katalogu Allegro, z którym jest połączona
- zmieni się aktualna najniższa cena danego produktu na Allegro

Cenę zmienimy zawsze tylko w zakresie, który masz ustawiony dla danej oferty. Jeśli nie zdefiniujesz zakresu cen, reguła cenowa nie będzie działać w tej ofercie.

##### Jak działają reguły cenowe typu “FOLLOW_BY_MARKET_MIN_PRICE”

Reguła cenowa “FOLLOW_BY_MARKET_MIN_PRICE” (Najniższa cena na rynku) automatycznie zmienia cenę w Twojej ofercie na podstawie:

- zakresu cen, w ramach którego chcesz zmieniać swoją cenę - jest to warunek, który musi zostać spełniony. Jeśli nie podasz zakresu, uwzględnimy regułę w ofercie, jednak nie będziemy przeliczać cen. Dla rynków zagranicznych możesz podać zakres w walucie tego rynku lub w walucie Twojego rynku rejestracji
- aktualnie najniższej ceny danego produktu na Allegro i w najlepszych sklepach internetowych – sprawdzamy ją co godzinę. Jeśli nie posiadamy takiej ceny, weźmiemy pod uwagę cenę Top Oferty (jeśli istnieje). Szczegóły znajdziesz poniżej.
- twojej ceny produktu w tej ofercie

W ustalaniu najniższej ceny produktu na Allegro korzystamy [z tych samych wytycznych](https://developer.allegro.pl/tutorials/jak-zarzadzac-ofertami-7GzB2L37ase#jak-ustalamy-najnizsza-cene-dla-danego-produktu), co w przypadku reguły "FOLLOW_BY_ALLEGRO_MIN_PRICE" (Najniższa cena na Allegro).

Jeśli cena produktu:

- nie istnieje w ramach żadnej z reguł: “FOLLOW_BY_MARKET_MIN_PRICE”, "FOLLOW_BY_ALLEGRO_MIN_PRICE” i "FOLLOW_BY_TOP_OFFER_PRICE", to nie będziemy jej przeliczać.
- nie istnieje w ramach obu reguł: “FOLLOW_BY_MARKET_MIN_PRICE” i "FOLLOW_BY_ALLEGRO_MIN_PRICE”, to weźmiemy pod uwagę cenę Top Oferty (jeśli istnieje dla produku),
- istnieje w ramach reguły “FOLLOW_BY_MARKET_MIN_PRICE”, ale nie w "FOLLOW_BY_ALLEGRO_MIN_PRICE", to weźmiemy pod uwagę najniższą cenę na rynku,
- istnieje w ramach reguły "FOLLOW_BY_ALLEGRO_MIN_PRICE", ale nie w “FOLLOW_BY_MARKET_MIN_PRICE”, to weźmiemy pod uwagę najniższą cenę na Allegro,
- istnieje w ramach reguł "FOLLOW_BY_ALLEGRO_MIN_PRICE" (“Najniższa cena na Allegro”) i “FOLLOW_BY_MARKET_MIN_PRICE” (“Najniższa cena na rynku”), weżmiemy pod uwagę najniższą cenę,

###### Kiedy aktualizujemy ceny w ofertach z regułą “FOLLOW_BY_MARKET_MIN_PRICE”

Pierwszy raz zaktualizujemy cenę Twojej oferty na wybranym rynku, gdy połączysz ją z regułą cenową “FOLLOW_BY_MARKET_MIN_PRICE” i ustawisz zakres cen.

Od tego czasu będziemy aktualizować cenę oferty za każdym razem, gdy:

- kurs walut zmieni się w taki sposób, że wpływa na cenę w walucie wybranego rynku – jeśli zdefiniujesz zakres cen w walucie rynku rejestracji.
- edytujesz regułę cenową połączoną z ofertą
- zmienisz zakres cen dla tej oferty
- zmienisz niektóre dane w tej ofercie – na przykład status oferty, jej widoczność na rynkach zagranicznych lub produkt w Katalogu Allegro, z którym jest połączona
- zmieni się najniższa cena produktu w jednym ze sklepów, z którymi się porównujemy, lub na Allegro

Cenę zmienimy zawsze tylko w zakresie, który masz ustawiony dla danej oferty. Jeśli nie zdefiniujesz zakresu cen, reguła cenowa nie będzie działać w tej ofercie.

Przykład:

1. Cena sprzedającego, który włączył regułę cenową Najniższa cena na rynku automatycznie aktualizuje się i wynosi 99 zł.
2. Następnie cena w konkurencyjnym sklepie zmienia się i wynosi obecnie 99 zł.
3. Sprzedający ustawia regułę cenową Najniższa cena na rynku i wynosi ona 100 zł. Ustawia zakres cen: 110 - 99 zł.
4. Najniższa cena w innym sklepie internetowym, z którym porównujemy ceny to 110 zł.
5. Najniższa cena na Allegro to 100 zł.

##### Jak działają reguły cenowe typu “FOLLOW_BY_TOP_OFFER_PRICE”

Reguła cenowa “FOLLOW_BY_TOP_OFFER_PRICE” (Top Oferta) automatycznie zmienia cenę w Twojej ofercie na podstawie:

- zakresu cen, w ramach którego chcesz zmieniać swoją cenę - jest to warunek, który musi zostać spełniony. Jeśli nie podasz zakresu, uwzględnimy regułę w ofercie, jednak nie będziemy przeliczać cen. Dla rynków zagranicznych możesz podać zakres w walucie tego rynku lub w walucie Twojego rynku rejestracji.
- aktualnej ceny Top Oferty danego produktu na Allegro - sprawdzamy ją co godzinę
- Twojej ceny produktu w tej ofercie,

[W artykule](https://help.allegro.com/sell/pl/a/jak-dziala-trafnosc-produktowa-i-czym-jest-top-oferta-q0a53w4Kxto#jak-wybieramy-top-oferte) na stronie Dla Sprzedających sprawdzisz dokładnie, jakie wytyczne bierzemy pod uwagę przy wyborze Top Oferty.

###### Kiedy aktualizujemy ceny w ofertach z regułą “FOLLOW_BY_TOP_OFFER_PRICE”

Pierwszy raz zaktualizujemy cenę Twojej oferty na wybranym rynku, gdy połączysz ją z regułą cenową “FOLLOW_BY_TOP_OFFER_PRICE” i ustawisz zakres cen.

Od tego czasu będziemy aktualizować cenę oferty za każdym razem, gdy:

- kurs walut zmieni się w taki sposób, że wpływa na cenę w walucie wybranego rynku – jeśli zdefiniujesz zakres cen w walucie rynku rejestracji.
- edytujesz regułę cenową połączoną z ofertą,
- zmienisz zakres cen dla tej oferty,
- zmienisz niektóre dane w tej ofercie – na przykład status oferty, jej widoczność na rynkach zagranicznych lub produkt w Katalogu Allegro, z którym jest połączona
- zmieni się cena Top Oferty danego produktu na Allegro,

Cenę zmienimy zawsze tylko w zakresie, który masz ustawiony dla danej oferty. Jeśli nie zdefiniujesz zakresu cen, reguła cenowa nie będzie działać w tej ofercie.

Przykład:

1. Nowa cena mieści się z zakresie sprzedającego, dlatego cenę w ofercie zmienimy na 105zł.
2. Cena w Top Ofercie zmienia się na 105zł.
3. Z uwagi na to, że cena w Top Ofercie nie mieści się w zakresie zdefiniowanym przez sprzedającego, nie uruchamiamy działania reguły cenowej w ofercie.
4. Sprzedający ustawia regułę cenową Top Oferta, gdzie cena danego produktu w Top Ofercie wynosi 100 zł. Ustawia zakres cen w swojej regule na 105zł - 110zł.
5. Cena w ofercie sprzedającego to 110zł.

#### Jak utworzyć własne reguły cenowe

Domyślnie na koncie użytkownik posiada dwie reguły utworzone przez Allegro, typu:

- “FOLLOW_BY_TOP_OFFER_PRICE” - o nazwie “Top Oferta”. Reguła nie jest automatycznie przypisana do żadnej oferty.
- "FOLLOW_BY_MARKET_MIN_PRICE" - o nazwie “Najniższa cena na rynku”. Reguła nie jest automatycznie przypisana do żadnej oferty.
- "FOLLOW_BY_ALLEGRO_MIN_PRICE" - o nazwie "Najniższa cena na Allegro". Reguła nie jest automatycznie przypisana do żadnej oferty.
- “EXCHANGE_RATE” - o nazwie “Przelicznik cen”. Tworzymy ją automatycznie w oparciu o ofertę z cennikiem dostawy dla rynku zagranicznego. Regułę automatycznie przypisujemy do ofert, które kwalifikują się do widoczności w serwisach zagranicznych.

Powyższe reguły oznaczone są jako “default”: true, nie zawierają dodatkowych konfiguracji cen, które zdefiniować może wyłącznie sprzedający. Reguł domyślnych nie możesz edytować lub usunąć.

Aby utworzyć nową reguły, skorzystaj z [POST /sale/price-automation/rules](https://developer.allegro.pl/documentation#operation/createAutomaticPricingRulesUsingPost). Możesz posiadać maksymalnie 20 reguł cenowych (2 utworzone przez Allegro oraz 18 własnych).

Każda reguła cenowa, którą stworzysz, będzie jednocześnie:

dodawać lub odejmować określony procent ceny (maksymalnie 50%), który zdefiniujesz w polu “configuration.changeByPercentage”. Dla reguł cenowych typu:

- “EXCHANGE_RATE” – dodamy lub odejmiemy określony procent do ceny w walucie rynku rejestracji, czyli przed przewalutowaniem ceny
- “FOLLOW_BY_TOP_OFFER_PRICE” - dodamy lub odejmiemy określony procent do nowej ceny Top Oferty produktu. Dodatkowo sprawdzimy, czy otrzymana kwota mieści się w Twoim zakresie cen (który będziesz definiować na poziomie przypisywania reguły cenowej do oferty).
- "FOLLOW_BY_ALLEGRO_MIN_PRICE" i "FOLLOW_BY_MARKET_MIN_PRICE"- dodamy lub odejmiemy określony procent do nowej najniższej ceny produktu, który jest przypisany w ofercie. Dodatkowo sprawdzimy, czy otrzymana kwota mieści się w Twoim zakresie cen (który będziesz definiować na poziomie przypisywania reguły cenowej do oferty).

Przykładowy request dla reguły typu “EXCHANGE_RATE”:

```
curl  -X  POST  \
'https://api.allegro.pl/sale/price-automation/rules' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
-d ‘{
  "name": "Exchange Rate add 10%",    // nazwa reguły cenowej
  "type": "EXCHANGE_RATE",    // typ reguły 
  "configuration": {     // opcjonalnie, konfiguracja reguły
    "changeByPercentage": {     // ustawienia procentowe, jakie będą zastosowane do reguły
      "operation": "ADD",    // typ operacji: ADD (dodaj) albo SUBTRACT (odejmij)
      "value": "10"    // wartość operacji. W tym przypadku reguła będzie dodawać 10% do ceny w serwisie bazowym
    }
  }
}’
```

Przykładowe response:

```
{
    "id": "66950bc04a57a95dfad0890d",    // ID reguły cenowej
    "type": "EXCHANGE_RATE",    // typ reguły 
    "name": "Exchange Rate add 10%",    // nazwa reguły
    "default": false,    // czy reguła została utworzona przez Allegro (true) czy przez sprzedawcę (false)
    "configuration": {    // konfiguracja reguły
        "changeByPercentage": {    // ustawienia procentowe, jakie będą zastosowane do reguły
            "operation": "ADD",    // typ operacji
            "value": "10"    // wartość operacji. W tym przypadku reguła będzie odejmować 10% do ceny w  serwisie bazowym
        }
    },
    "updatedAt": "2024-07-15T11:45:04.567Z" // data modyfikacji reguły
}
```

Przykładowy request dla reguły typu "FOLLOW_BY_ALLEGRO_MIN_PRICE":

```
curl  -X  POST  \
'https://api.allegro.pl/sale/price-automation/rules' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
-d ‘{
  "name": "Follow price subtract 15%",    // nazwa reguły cenowej
  "type": "FOLLOW_BY_ALLEGRO_MIN_PRICE",    // typ reguły 
  "configuration": {     // opcjonalnie, konfiguracja reguły
    "changeByPercentage": {    // ustawienia procentowe, jakie będą zastosowane do reguły
      "operation": "SUBTRACT",    // typ operacji: ADD (dodaj) albo SUBTRACT (odejmij)
      "value": "15"    // wartość operacji. W tym przypadku reguła będzie odejmować 15% od nowej najniższej ceny produktu w ofercie
    }
  }
}’
```

Przykładowe response:

```
{
    "id": "66950bc04a57a95dfad0891d",    // ID reguły cenowej
    "type": "FOLLOW_BY_ALLEGRO_MIN_PRICE",    // typ reguły 
    "name": "Follow price subtract 15%",    // nazwa reguły
    "default": false,    // czy reguła została utworzona przez Allegro (true) czy przez sprzedawcę (false)
    "configuration": {    // konfiguracja reguły
        "changeByPercentage": {     // ustawienia procentowe, jakie będą zastosowane do reguły
            "operation": "SUBTRACT",    // typ operacji
            "value": "15".   // wartość operacji. W tym przypadku reguła będzie odejmować 15% od nowej najniższej ceny produktu w ofercie
        }
    },
    "updatedAt": "2024-07-15T11:45:04.567Z"    // data modyfikacji reguły
}
```

Przykładowy request dla reguły typu "FOLLOW_BY_MARKET_MIN_PRICE":

```
curl  -X  POST  \
'https://api.allegro.pl/sale/price-automation/rules' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
-d ‘{
  "name": "Follow market price subtract 5%",    // nazwa reguły cenowej
  "type": "FOLLOW_BY_MARKET_MIN_PRICE",    // typ reguły 
  "configuration": {     // opcjonalnie, konfiguracja reguły
    "changeByPercentage": {    // ustawienia procentowe, jakie będą zastosowane do reguły
      "operation": "SUBTRACT",    // typ operacji: ADD (dodaj) albo SUBTRACT (odejmij)
      "value": "5"    // wartość operacji. W tym przypadku reguła będzie odejmować 5% od nowej najniższej ceny produktu w ofercie
    }
  }
}’
```

Przykładowy response:

```
{
    "id": "66950bc04a57a95dfad0891d",    // ID reguły cenowej
    "type": "FOLLOW_BY_MARKET_MIN_PRICE",  // typ reguły 
    "name": "Follow market price subtract 5%",    // nazwa reguły
    "default": false,    // czy reguła została utworzona przez Allegro (true) czy przez sprzedawcę (false)
    "configuration": {    // konfiguracja reguły
        "changeByPercentage": {     // ustawienia procentowe, jakie będą zastosowane do reguły
            "operation": "SUBTRACT",    // typ operacji
            "value": "5".   // wartość operacji. W tym przypadku reguła będzie odejmować 5% od nowej najniższej ceny produktu w ofercie
        }
    },
    "updatedAt": "2024-07-15T11:45:04.567Z"    // data modyfikacji reguły
}
```

#### Jak pobrać dostępne reguły cenowe

Wykonasz to za pomocą [GET /sale/price-automation/rules](https://developer.allegro.pl/documentation#operation/getAutomaticPricingRulesUsingGET). Zasób jest dodatkowo limitowany do 5 requestów na sekundę.

Przykładowy request:

```
curl  -X  GET  \
'https://api.allegro.pl/sale/price-automation/rules' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
```

Przykładowy response:

```
{
    "rules": [     // lista reguł cenowych zdefiniowanych na koncie
        {
            "id": "644773f274c48fb91dbaf1de",    // ID reguły cenowej
            "type": "EXCHANGE_RATE",    // typ reguły 
            "name": "Przelicznik cen",    // nazwa reguły
            "default": true,    // czy reguła została utworzona przez Allegro
            "updatedAt": "2023-04-25T06:32:18Z"    // data ostatniej modyfikacji
        },
        {
            "id": "664dcce914d5bb52af70bd27",
            "type": "FOLLOW_BY_ALLEGRO_MIN_PRICE",
            "name": "Najniższa cena na Allegro",
            "default": true,
            "updatedAt": "2024-05-22T10:46:01.115Z"
        },
        {
            "id": "66950bc04a57a95dfad0890d",
            "type": "EXCHANGE_RATE",
            "name": "Exchange Rate add 10%",
            "default": false,
            "configuration": {    // konfiguracja reguły
                "changeByPercentage": {
                    "operation": "ADD",
                    "value": "10"
                }
            },
            "updatedAt": "2024-07-15T11:45:04.567Z"
        },
        {
            "id": "669511cf4a57a95dfad08956",
            "type": "FOLLOW_BY_ALLEGRO_MIN_PRICE",
            "name": "Follow price subtract 15%",
            "default": false,
            "configuration": {
                "changeByPercentage": {
                    "operation": "SUBTRACT",
                    "value": "15"
                }
            },
            "updatedAt": "2024-07-15T12:10:55.949Z"
        },
             {
            "id": "164dcce914d5bb52af70bd26",
            "type": "FOLLOW_BY_MARKET_MIN_PRICE",
            "name": "Najniższa cena na rynku",
            "default": true,
            "updatedAt": "2024-10-22T10:46:01.115Z"
        }
    ]
}
```

#### Jak edytować regułę cenową

Aby edytować regułę cenową, skorzystaj z [PUT /sale/price-automation/{ruleId}](https://developer.allegro.pl/documentation#operation/updateAutomaticPricingRuleUsingPut). Zmienić możesz wyłącznie nazwę lub konfigurację reguły cenowej. Nie możesz modyfikować reguł domyślnych, utworzonych przez Allegro, oznaczonych jako “default”: true.

Przykładowy request:

```
curl  -X  PUT  \
'https://api.allegro.pl/sale/price-automation/rules/644773f274c48fb91dbaf1de' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
-d ‘{
  "name": "Follow price subtract 20%",    // nazwa reguły cenowej
  "configuration": {    // opcjonalnie, konfiguracja reguły
    "changeByPercentage": {    // ustawienia procentowe, jakie będą zastosowane do reguły
      "operation": "SUBTRACT",    // typ operacji: ADD (dodaj) albo SUBTRACT (odejmij)
      "value": "20"    // wartość operacji. W tym przypadku reguła będzie odejmować 20% od nowej najniższej ceny danego produktu
    }
  }
}’
```

Przykładowy response:

```
{
    "id": "66950bc04a57a95dfad0890d",    // ID reguły cenowej
    "type": "FOLLOW_BY_ALLEGRO_MIN_PRICE",    // typ reguły
    "name": "Follow price subtract 20%",    // nazwa reguły
    "default": false,    // czy reguła została utworzona przez Allegro
    "configuration": {    // konfiguracja reguły
        "changeByPercentage": {
            "operation": "SUBTRACT",    // typ operacji: ADD (dodaj) albo SUBTRACT (odejmij)
            "value": "20"    // wartość operacji. W tym przypadku reguła będzie odejmować 20% od nowej najniższej ceny danego produktu
        }
    },
    "updatedAt": "2024-07-15T12:37:05.325Z"    // data modyfikacji
}
```

#### Jak usunąć regułę cenową

Wykonasz to za pomocą [DELETE /sale/price-automation/{ruleId}](https://developer.allegro.pl/documentation#operation/deleteAutomaticPricingRuleUsingDelete). Regułę usuniesz wyłącznie wtedy, gdy nie jest przypisana do żadnej oferty.

Przykładowy request:

```
curl  -X  DELETE  \
'https://api.allegro.pl/sale/price-automation/rules/644773f274c48fb91dbaf1de' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
```

Przykładowy response:

```
204 No Content
```

#### Jak przypisać i usunąć reguły przelicznika cen w ofertach

Użyj w tym celu [POST /sale/offer-price-automation-commands](https://developer.allegro.pl/documentation#operation/offerAutomaticPricingModificationCommandUsingPOST). Zasób jest dodatkowo limitowany do 150 tys. zmian w pojedynczej ofercie na godzinę lub 9 tys. na minutę.

Przykładowy request:

```
'https://api.allegro.pl/sale/offer-price-automation-commands' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
-d '{
  "id": "123a08d7-ab9b-460d-b9cb-d6ed64b3a018",    // niewymagane, ID  komendy. Jeśli nie przekażesz wartości w tym polu, ID w odpowiedzi wygenerujemy automatycznie
  "modification": {    // informacje o modyfikacji reguł przeliczania cen. Przekaż jedno z pól: set (przypisanie reguły) albo “remove” (usunięcie)
    "set": [                          
      {
        "marketplace": {
          "id": "allegro-cz"    // ID serwisu, do którego chcesz przypisać regułę cenową podaną w polu rule.id
        },
        "rule": {
          "id": "641c73feaef0a8281a3d11f8"    // ID reguły cenowej. Dostępne wartości pobierzesz za pomocą GET /sale/price-automation/rules
        },
        "configuration": {    // dodatkowa konfiguracja zakresu cen. Wymagane, abyśmy przeliczali ceny dla reguły typu FOLLOW_BY_ALLEGRO_MIN_PRICE, FOLLOW_BY_MARKET_MIN_PRICE oraz FOLLOW_BY_TOP_OFFER_PRICE, brak możliwości uzupełnienia dla reguły EXCHANGE_RATE
          "priceRange": {    // zakres cen
            "type": "MARKETPLACE_CURRENCY",    // typ zakresu wg waluty. Dla każdego serwisu możesz wskazać MARKETPLACE_CURRENCY  (zakres cenowy musisz określić w walucie serwisu, do którego przypisujesz regułę), dla serwisów dodatkowych możesz wskazać zarówno MARKETPLACE_CURRENCY albo BASE_MARKETPLACE_CURRENCY (wtedy zakres cenowy musisz określić w walucie serwisu bazowego)
            "minPrice": {    // minimalna cena
              "amount": "123.45",     // kwota
              "currency": "PLN"     // waluta
            },
            "maxPrice": {    // maksymalna cena
              "amount": "125.45",    // kwota 
              "currency": "PLN"    // waluta
            }
          }
        }
      }
    ],
     "remove": [
      {
        "marketplace": {
           "id": "allegro-xx"    // ID serwisu, w którym chcesz usunąć biężącą regułę cenową
         }
        }
      ]
  },
  "offerCriteria": [
    {
      "offers": [    // wymagane, tablica obiektów z  numerami identyfikacyjnymi ofert - maksymalnie 1000 ofert
        {
          "id": "123456789"
        }
      ],
      "type": "CONTAINS_OFFERS"    // wymagane, obecnie dostępna jest jedna wartość: CONTAINS_OFFERS (oferty, w których zmienimy ustawienia reguł cenowych)
    }  
  ]
}'
```

Przykładowy response:

```
{
    "id": "0e09c6fe-dabd-42b7-8bbe-4daa1526df80",    // ID komendy
    "createdAt": "2019-08-24T14:15:22Z",    // data utworzenia zadania
    "completedAt": null,    // data realizacji zadania (dla tej metody zawsze zwrócimy null)
    "taskCount": {
        "total": 0,
        "success": 0,
        "failed": 0
    }
}
```

Aby sprawdzić status wykonania zadania, skorzystaj z [GET /sale/offer-price-automation-commands/{commandId}](https://developer.allegro.pl/documentation#operation/getofferPriceAutomationModificationCommandStatusUsingGET). W odpowiedzi otrzymasz zestawienie, w ilu ofertach operacja wykonała się poprawnie, a z iloma wystąpił problem.

Przykładowy request:

```
curl  -X  GET  \
'https://api.allegro.pl/sale/offer-price-automation-commands/123a08d7-ab9b-460d-b9cb-d6ed64b3a018' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
```

Przykładowy response:

```
 {
    "id": "123a08d7-ab9b-460d-b9cb-d6ed64b3a018",
    "createdAt": "2019-08-24T14:15:22Z",
    "completedAt": "2019-08-24T14:15:22Z",
    "taskCount": {
        "total": 2,
        "success": 2,
        "failed": 0
    }
  }
```

Jeśli chcesz pobrać szczegółowy raport, użyj w tym celu [GET /sale/offer-price-automation-commands/{commandId}/tasks](https://developer.allegro.pl/documentation#operation/getofferPriceAutomationModificationCommandTasksStatusesUsingGET).

Przykładowy request:

```
curl  -X  GET  \
'https://api.allegro.pl/sale/offer-price-automation-commands/123a08d7-ab9b-460d-b9cb-d6ed64b3a018/tasks' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
```

Przykładowy response:

```
{
    "tasks": [
        {
            "offer": {
                "id": "1234567"
            },
            "message": null,                                   
            "status": "SUCCESS",
            "field": "repricing",
            "errors": []
        }
    ]
}
```

Oba wyżej wymienione zasoby są dodatkowo limitowane do 270 tys. ofert w zleconych komendach na minutę.

#### Jak sprawdzić aktualnie przypisane reguły przelicznika cen w ofercie

Użyj w tym celu [GET /sale/price-automation/offers/{offerId}/rules](https://developer.allegro.pl/documentation#operation/getPriceAutomationRulesForOfferUsingGET). Zasób jest dodatkowo limitowany do 5 requestów na sekundę.

Przykładowy request:

```
curl  -X  GET  \
'https://api.allegro.pl/sale/price-automation/offers/123456789/rules' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-H 'Authorization: Bearer {token}' \
```

Przykładowy response:

```
{
  "rules": [
    {
      "marketplace": {
        "id": "allegro-pl"    // ID serwisu, którego dotyczy dana reguła
      },
      "rule": {
        "id": "641c73feaef0a8281a3d11f8"    // ID reguły przelicznika cen
      },
      "updatedAt": "2023-03-23T15:45:02Z"   // data, kiedy dana reguła była ostatnio modyfikowana
    }
  ],
  "updatedAt": "2023-03-23T15:45:02Z"    // data, kiedy ostatnio nastąpiła zmiana w przypisaniu reguł w ofercie
}
```

### Kategorie i parametry

#### Dziennik zmian w kategoriach

Skorzystaj z [GET /sale/category-events](https://developer.allegro.pl/documentation/#operation/getCategoryEventsUsingGET_1), aby pobrać informację o zmianach w kategoriach, które wydarzyły się w ostatnich 3 miesiącach. Domyślnie w odpowiedzi otrzymasz 100 najstarszych zdarzeń. Aby dopasować wyniki do swoich potrzeb, użyj filtrów:

from - ID eventu, od którego chcesz pobrać kolejną porcję danych. W odpowiedzi otrzymasz zdarzenia, które nastąpiły po tym ID;

limit - liczba wyników, które zwrócimy w odpowiedzi. Domyślna wartość to 100, maksymalna 1000;

type - rodzaj zdarzenia:

CATEGORY_CREATED - utworzyliśmy nową kategorię;

CATEGORY_RENAMED - zmieniliśmy nazwę kategorii;

CATEGORY_MOVED - przenieśliśmy kategorię w inne miejsce w drzewie kategorii, zmieniliśmy tym samym wartość parent.id danej kategorii;

CATEGORY_DELETED - usunęliśmy kategorię, nie jest już dostępna. W swoich żądaniach użyj category.id widoczne w polu redirectCategory. \ Żądanie może zawierać jedną lub więcej wartości, np. GET /sale/category-events?type=CATEGORY_CREATED&type=CATEGORY_MOVED

Przykładowy request:

```
  curl -X GET 
  ‘https://api.allegro.pl/sale/category-events’/
  -H ‘Authorization: Bearer {token}’ /
  -H ‘Accept: application/vnd.allegro.public.v1+json’
```

Przykładowy response:

```
   {
    ...
      {    
          "id": "MTEzMjQzODU3NA",        // ID zdarzenia
        "occurredAt": "2021-01-12T15:26:43.891Z",    - czas wystąpienia zdarzenia
        "type": "CATEGORY_CREATED",    // typ zdarzenia
        "category": {    // dane kategorii, której dotyczy zdarzenie
            "id": "165",    // ID kategorii
            "name": "Smartphones and Cell Phones",    // nazwa kategorii
            "parent": {
                "id": "4"    // ID kategorii nadrzędnej
                },
            "leaf": false    // czy dana kategoria jest kategorią najniższego rzędu
                }
          }
    ...
    }
```

#### Zmiana kategorii w ofercie

Kategorię w ofercie możesz zmienić do 12 godzin od momentu, kiedy została opublikowana. Wprowadziliśmy jednak ułatwienie, które umożliwia zmianę kategorii w aktywnej ofercie, jeśli:

- oferta nie ma podpiętego produktu, bo nigdy go nie miała, albo została odpięta od Katalogu produktów - pozwalamy podpiąć produkt i jednocześnie zmienić kategorię oferty na zgodną z kategorią produktu.
- oferta ma podpięty produkt, ale kategoria jest błędna - pozwalamy na zmianę kategorii oferty na zgodną z kategorią produktu,

Wyjątek stanowi kategoria “Pozostałe” - nie pozwalamy na przeniesienie oferty do takiej kategorii, nawet, jeżeli produkt tam się znajduje.

#### Jak sprawdzić nieuzupełnione parametry w ofertach

Skorzystaj z [GET /sale/offers/unfilled-parameters](https://developer.allegro.pl/documentation/#operation/getOffersUnfilledParametersUsingGET_1) i sprawdź brakujące parametry w ofertach. W odpowiedzi zwrócimy domyślnie listę 100 ofert, w których nie są uzupełnione parametry obowiązkowe oraz te, które w ciągu najbliższych 3 miesięcy oznaczymy jako wymagane. Jeżeli chcesz zawęzić wyniki, możesz skorzystać z dodatkowych filtrów:

offer.id - otrzymasz dane tylko dla wybranych ofert, np. GET /sale/offers/unfilled-parameters?offer.id=123456789&offer.id=98765432;

limit - liczba wyników, które zwrócimy w odpowiedzi. Domyślna wartość to 100, maksymalna 1000.

offset - miejsce, od którego chcesz pobrać kolejną porcję danych.

parameterType - typ parametrów:

- REQUIREMENT_PLANNED - parametry, które w ciągu najbliższych 3 miesięcy oznaczymy jako wymagane.
- REQUIRED - obecnie wymagane parametry,

Przykładowy request:

```
 curl -X GET \
 'https://api.allegro.pl/sale/offers/unfilled-parameters?offer.id=123456789' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  {
    "offers": [
             {
              "id": "123456789",    // ID oferty
              "parameters": [        // informacje o nieuzupełnionych parametrach
                  {
                      "id": "14228"    // ID parametru
                  }
              ],
              "category": {
                  "id": "257931"    // ID kategorii, w której występuje parametr
              }
             }
      ],
      "count": 1,    // liczba wyświetlanych wyników
      "totalCount": 1    // łączna liczba wyników
  }
```

#### Jak sprawdzić przyszłe zmiany w parametrach

Za pomocą [GET /sale/category-parameters-scheduled-changes](https://developer.allegro.pl/documentation/#operation/getCategoryParametersScheduledChangesUsingGET_1) sprawdzisz zmiany w parametrach, które zaplanowaliśmy na najbliższe 3 miesiące. Domyślnie w odpowiedzi otrzymasz listę 100 najwcześniej zaplanowanych zmian.

W wyjątkowych sytuacjach możemy zdecydować, aby nie wdrażać wybranych zaplanowanych zmian - np. jeżeli zrezygnujemy z oznaczenia danego parametru jako obowiązkowy. W takiej sytuacji dane zdarzenie usuniemy z odpowiedzi.

Jeżeli chcesz zawęzić wyniki, możesz skorzystać z dodatkowych filtrów:

limit - liczba wyników które zwrócimy w odpowiedzi. Domyślna wartość to 100, maksymalna 1000.

offset - miejsce, od którego chcesz pobrać kolejną porcję danych,

type - rodzaj zmiany, na tę chwilę zwracamy tylko jedną wartość - REQUIREMENT_CHANGE (dany parametr oznaczymy jako wymagany),

scheduledAt.gte - najwcześniejsza data, kiedy zaplanowaliśmy zmianę, np. GET /sale/category-parameters-scheduled-changes?scheduledAt.gte=2021-01-01T00:00:00Z

scheduledAt.lte - najpóźniejsza data, kiedy zaplanowaliśmy zmianę np. ET /sale/category-parameters-scheduled-changes?scheduledAt.lte=2021-01-13T23:59:59Z

scheduledFor.gte - najwcześniejsza data planowanego uobowiązkowienia, np. GET /sale/categories/parameters/required-changes?scheduledFor.gte=2021-02-01T00:00:00Z

scheduledFor.lte - najpóźniejsza data planowanego uobowiązkowienia, nie może być większa niż 3 miesiące od bieżącej daty, np. GET /sale/category-parameters-scheduled-changes?scheduledFor.lte=2021-02-28T23:59:59Z.

Przykładowy request:

```
  curl -X GET 
  'https://api.allegro.pl/sale/category-parameters-scheduled-changes' \
  -H ‘Authorization: Bearer {token}’ \
  -H ‘Accept: application/vnd.allegro.public.v1+json’
```

Przykładowy response:

```
   {
    ... 
     {
      "scheduledAt": "2021-01-12T15:26:43.891Z",    // data z przeszłości, kiedy  zaplanowaliśmy zmianę
      "scheduledFor": "2021-02-14T15:26:43.891Z",    // data z przyszłości, na kiedy planujemy wdrożyć zmianę
      "type": "REQUIREMENT_CHANGE",    // odzaj zmiany
      "category": {
          "id": "165"    // ID kategorii, w której znajduje się parametr, którego dotyczy zmiana
          },
      "parameter": {
          "id": "11323"    // ID parametru, którego dotyczy zmiana
          }
      }
    ...
    }
```

### Jak zarządzać warunkami zwrotów

#### Jak dodać informacje o warunkach zwrotów

Skorzystaj z [POST /after-sales-service-conditions/return-policies](https://developer.allegro.pl/documentation/#operation/createAfterSalesServiceReturnPolicyUsingPOST), aby dodać nowe [warunki zwrotów](https://allegro.pl/moje-allegro/sprzedaz/warunki-zwrotow). W strukturze żądania przekaż pola:

availability.range - wymagane, możliwość odstąpienia od umowy przez kupującego:

- DISABLED - brak możliwości.
- RESTRICTED - ograniczona możliwość,
- FULL - jest taka możliwość,

Wartości dostępne dla opcji RESTRICTED:

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Nagranie dźwiękowe, wizualne, program komputerowy w zapieczętowanym opakowaniu. Np.: kiedy kupujący zdejmie folię ochronną z fabrycznie nowej gry, lub płyty z muzyką czy filmem.

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Rzecz, która dostarczona jest w zapieczętowanym opakowaniu, a której po jego otwarciu nie możesz zwrócić ze względu na ochronę zdrowia lub higienę. Np.: bielizna osobista, test ciążowy, końcówki do szczoteczki elektrycznej, soczewki kontaktowe, maseczki.

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Rzecz, którą po dostarczeniu trwale połączysz z innymi rzeczami. Np.: olej samochodowy, który wlejesz do auta.

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Treść cyfrową, nie zapisaną na nośniku materialnym, z której kupujący zgodził się skorzystać. Np.: pobranie ebooka, kodu do gry.

| Wartość | Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy: |
| --- | --- |
| SEALED_MEDIA |
| SEALED_ITEM_NO_RETURN_DUE_HEALTH_OR_HYGIENE |
| INSEPARABLY_LINKED |
| NOT_RECORDED_DIGITAL_CONTENT |

Wartości dostępne dla opcji DISABLED:

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Rzecz wyprodukowaną na indywidualne zamówienie kupującego, według jego wytycznych.Np.: koszulka z zaprojektowanym przez kupującego nadrukiem.

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Produkt z krótkim terminem przydatności do użycia lub taki, który szybko się psuje. Np.: twaróg, świeże warzywa.

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Dziennik, periodyk lub czasopismo – z wyjątkiem umów o prenumeratę.

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Produkt leczniczy w rozumieniu prawa farmaceutycznego, środki spożywcze specjalnego przeznaczenia żywieniowego i wyroby medyczne wydane z apteki. Kategoria dostępna tylko na allegro.pl. Np.: leki OTC (bez recepty).

Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy:

Usługę lub przedmiot, których ceny zależą od wahań na rynku finansowym, nad którymi sprzedający nie ma kontroli, a które mogą wystąpić przed upływem terminu na odstąpienie od umowy. Np. produkty inwestycyjne: sztabki złota, monety kolekcjonerskie, srebro, platyna.

| Wartość | Prawo odstąpienia od umowy bez podania przyczyny nie przysługuje konsumentowi w przypadku gdy: |
| --- | --- |
| CUSTOM_ITEM |
| SHORT_SHELF_LIFE |
| PRESS |
| MEDICINAL_PRODUCT |
| VALUE_DEPENDENT_ON_FINANCIAL_MARKET |

- options - wymagana pełna struktura, jeśli w polu availability.range wybrano wartość FULL lub RESTRICTED, dodatkowe informacje. Poniżej znajdziesz listę dostępnych wartości wraz z opisem:
- contact - niewymagane, informacje kontaktowe - numer telefonu i adres email,
- address - wymagane, jeśli w polu availability.range wybrano wartość FULL lub RESTRICTED, opcjonalne dla DISABLED, adres do zwrotów,
- returnCost.coveredBy - wymagane, jeśli w polu availability.range wybrano wartość FULL lub RESTRICTED. Informacja o tym, kto pokrywa koszt przesyłki zwrotnej. Dostępne wartości to SELLER lub BUYER,
- withdrawalPeriod - wymagane, jeśli w polu availability.range wybrano wartość FULL lub RESTRICTED. Czas na odstąpienie umowy w formacie ISO 8601. Jako wartość możesz przekazać tylko dni, np. “P14D” - czas nie może być krótszy niż 14 dni.
- availability.restrictionCause.name - wymagane, jeśli w polu availability.range wybrałeś wartość RESTRICTED lub DISABLED. Poniżej znajdziesz listę dostępnych wartości wraz z opisem. Możesz wybrać tylko jedną wartość.

Zaznaczone informacje zobaczy kupujący na Twojej ofercie

Nie przyjmuję zwrotów nadanych za pobraniem.

Zaznaczone informacje zobaczy kupujący na Twojej ofercie

Otrzymałeś gratis? - w przypadku zwrotu towaru odeślij go również do nas.

Zaznaczone informacje zobaczy kupujący na Twojej ofercie

Otrzymałeś rabat na kolejną sztukę? - w przypadku zwrotu towaru pomniejszymy zwrot wpłaty o wartość udzielonego rabatu.

Zaznaczone informacje zobaczy kupujący na Twojej ofercie

Przyjmuję zwroty od firm (nie dotyczy jednoosobowych działalności gospodarczych).

Zaznaczone informacje zobaczy kupujący na Twojej ofercie

Osobiście odbieram zwrot od kupującego.

| Wartość | Zaznaczone informacje zobaczy kupujący na Twojej ofercie |
| --- | --- |
| cashOnDeliveryNotAllowed |
| freeAccessoriesReturnRequired |
| refundLoweredByReceivedDiscount |
| businessReturnAllowed |
| collectBySellerOnly |

```
  curl -X POST \
  'https://api.allegro.pl/after-sales-service-conditions/return-policies' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
    "name": "warunki zwrotu z ograniczeniami",    // wymagane, nazwa warunków zwrotu
    "availability": {    // wymagane, informacje o możliwości odstąpienia od umowy przez kupującego "range": "RESTRICTED",
        "restrictionCause": {    // wymagane, jeśli wybrałeś RESTRICTED
            "name": "PRESS"
        }
    },
    "withdrawalPeriod": "P30D",    // wymagane, czas na odstąpienie umowy
    "returnCost": {
        "coveredBy": "BUYER"    // wymagane, informacja o tym, kto pokrywa koszty przesyłki zwrotnej
    },
    "address": {    // wymagane, adres do zwrotów
        "name": "Allegro.pl Sp. z o.o.",
        "street": "Grunwaldzka 182",
        "postCode": "60-166",
        "city": "Poznań",
        "countryCode": "PL"
    },
    "contact": {     // niewymagane, dane kontaktowe
        "phoneNumber": "123123123",
        "email": "email@domain.com"
    },
    "options": { 
        "cashOnDeliveryNotAllowed": true,
        "freeAccessoriesReturnRequired": false,
        "refundLoweredByReceivedDiscount": false,
        "businessReturnAllowed": false,
        "collectBySellerOnly": false
    }
}'
```

zamknij

Przykładowy request

```
 {
    "id": "bc99b3fe-6953-46c6-80b7-40e6ad82d588",
    "seller": {
        "id": "44173117"
    },
    "name": "warunki zwrotu z ograniczeniami",
    "availability": {
        "range": "RESTRICTED",
        "restrictionCause": {
            "name": "PRESS",
            "description": "Dziennik, periodyk lub czasopismo – z wyjątkiem umów o prenumeratę."
        }
    },
    "withdrawalPeriod": "P30D",
    "returnCost": {
        "coveredBy": "BUYER"
    },
    "address": {
        "name": "Allegro.pl Sp. z o.o.",
        "street": "Grunwaldzka 182",
        "postCode": "60-166",
        "city": "Poznań",
        "countryCode": "PL"
    },
    "contact": {                                
        "phoneNumber": "123123123",
        "email": "email@domain.com"
    },
    "options": {                                
        "cashOnDeliveryNotAllowed": true,
        "freeAccessoriesReturnRequired": false,
        "refundLoweredByReceivedDiscount": false,
        "businessReturnAllowed": false,
        "collectBySellerOnly": false
    }
}
```

zamknij

Przykładowy request

#### Jak pobrać warunki zwrotów przypisane do konta

Za pomocą [GET /after-sales-service-conditions/return-policies](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET_1) pobierzesz warunki zwrotów przypisane do zautoryzowanego konta. W odpowiedzi otrzymasz listę 60 warunków, która zawiera informacje o identyfikatorze oraz nazwie warunku. Możesz ją dostosować do własnych potrzeb za pomocą filtrów:

- offset - miejsce, od którego chcesz pobrać następną porcję danych.
- limit - liczba wyników w odpowiedzi. Domyślna i maksymalna wartość to 60,

Jeżeli chcesz pobrać szczegóły warunków zwrotu, przekaż ich identyfikator za pomocą [GET /after-sales-service-conditions/return-policies/{returnPolicyId}](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceReturnPolicyUsingGET).

Przykladowy request:

```
  curl -X GET \
  'https://api.allegro.pl/after-sales-service-conditions/return-policies/bc99b3fe-6953-46c6-80b7-40e6ad82d588' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

```
 {
    "id": "bc99b3fe-6953-46c6-80b7-40e6ad82d588",
    "seller": {
        "id": "44173117"
    },
    "name": "ograniczone",
    "availability": {
        "range": "RESTRICTED",
        "restrictionCause": {
            "name": "PRESS",
            "description": "Dziennik, periodyk lub czasopismo – z wyjątkiem umów o prenumeratę."
        }
    },
    "withdrawalPeriod": "P14D",
    "returnCost": {
        "coveredBy": "BUYER"
    },
    "address": {
        "name": "Allegro.pl Sp. z o.o.",
        "street": "Grunwaldzka 182",
        "postCode": "60-166",
        "city": "Poznań",
        "countryCode": "PL"
    },
    "contact": {
        "phoneNumber": "123123123",
        "email": "email@domain.com"
    },
    "options": {
        "cashOnDeliveryNotAllowed": true,
        "freeAccessoriesReturnRequired": false,
        "refundLoweredByReceivedDiscount": false,
        "businessReturnAllowed": false,
        "collectBySellerOnly": false
    }
}
```

zamknij

Przykładowy request

#### Jak edytować informacje o warunkach zwrotu

Aby edytować informacje o warunkach zwrotu:

- dane, które otrzymałeś w poprzednim kroku, odpowiednio wyedytuj według własnych potrzeb i przekaż za pomocą [PUT /after-sales-service-conditions/return-policies/{returnPolicyId}](https://developer.allegro.pl/documentation/#operation/updateAfterSalesServiceReturnPolicyUsingPUT).
- przekaż wybrany identyfikator warunków zwrotu za pomocą [GET /after-sales-service-conditions/return-policies/{returnPolicyId}](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceReturnPolicyUsingGET), by otrzymać szczegółowe dane,
- za pomoca [GET /after-sales-service-conditions/return-policies](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET_1) pobierz warunki zwrotów przypisane do zautoryzowanego konta. W odpowiedzi otrzymasz identyfikatory oraz nazwy warunków zwrotu,

```
 curl -X PUT \
'https://api.allegro.pl/after-sales-service-conditions/return-policies/bc99b3fe-6953-46c6-80b7-40e6ad82d588' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
    "id": "bc99b3fe-6953-46c6-80b7-40e6ad82d588",
    "seller": {
        "id": "44173117"
    },
    "name": "ograniczone",
    "availability": {
        "range": "RESTRICTED",
        "restrictionCause": {
            "name": "PRESS",
            "description": "Dziennik, periodyk lub czasopismo – z wyjątkiem umów o prenumeratę."
        }
    },
    "withdrawalPeriod": "P30D",
    "returnCost": {
        "coveredBy": "BUYER"
    },
    "address": {
        "name": "Allegro.pl Sp. z o.o.",
        "street": "Grunwaldzka 182",
        "postCode": "60-166",
        "city": "Poznań",
        "countryCode": "PL"
    },
    "contact": {
        "phoneNumber": "123123123",
        "email": "email@domain.com"
    },
    "options": {
        "cashOnDeliveryNotAllowed": true,
        "freeAccessoriesReturnRequired": false,
        "refundLoweredByReceivedDiscount": false,
        "businessReturnAllowed": false,
        "collectBySellerOnly": false
    }
}'
```

zamknij

Przykładowy request

#### Jak usunąć informacje o warunkach zwrotu

Aby usunąć informacje o warunkach zwrotu, skorzystaj z [DELETE /after-sales-service-conditions/return-policies/{returnPolicyId}](https://developer.allegro.pl/documentation#operation/deleteAfterSalesServiceReturnPolicyUsingDELETE).

Próba usuniecia warunków zwrotów, które wciąż są przypisane do ofert, zakończy się błędem 400 Bad Request. Aby upewnić się, czy możesz je usunąć, skorzystaj z [GET /sale/offers](https://developer.allegro.pl/documentation#operation/searchOffersUsingGET) i użyj parametr wyszukiwania: afterSalesServices.returnPolicy.id, podając ID wybranych warunków zwrotu.

### Jak zarządzać warunkami reklamacji

#### Jak dodać informacje o warunkach reklamacji

Skorzystaj z [POST /after-sales-service-conditions/implied-warranties](https://developer.allegro.pl/documentation/#operation/createAfterSalesServiceImpliedWarrantyUsingPOST), aby dodać nowe warunki reklamacji. W strukturze żądania przekaż pola:

- description - niewymagane, opis reklamacji. Możesz także skorzystać z tagów HTML:,,,,. Inne znaczniki zostaną zignorowane.
- address - wymagane, adres do reklamacji,
- corporate.period - niewymagane, czas na reklamację z tytułu rękojmi dla przedsiębiorców w formacie ISO 8601. Jeżeli chcesz ją wyłączyć, nie przekazuj tego pola lub przekaż wartość null.
- individual.period - wymagane, czas na reklamację z tytułu rękojmi w formacie ISO 8601. Jako wartość możesz wskazać tylko lata, np. “P3Y” oznacza 3 lata.
- name - wymagane, nazwa dla warunków reklamacji,

```
  curl -X POST \
  'https://api.allegro.pl/after-sales-service-conditions/implied-warranties' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
    "name": "Główne warunki reklamacji",    // wymagane, nazwa warunków reklamacji
    "individual": {
        "period": "P1Y"    // wymagane, czas na reklamację z tytułu rękojmi
    },
    "corporate": {    // niewymagane, czas na reklamację z tytułu rękojmi dla przedsiębiorców. Jeżeli chcesz ją wyłączyć, przekaż wartość null.
        "period": "P1Y"
    },
    "address": {    // wymagane, adres do reklamacji
        "name": "test",
        "street": "ul. Testowa 7",
        "postCode": "61-135",
        "city": "Poznań",
        "countryCode": "PL"
    },
    "description":    // niewymagane, opis procedury reklamacji
    “<p>Co musi zawierać reklamacja? Reklamacja powinna zawierać:</p>
     <ul><li>Twoje imię i nazwisko oraz adres</li>
     <li>numer oferty na Allegro</li><li>numer zamówienia</li>
     <li>przedmiot reklamacji</li>
     <li>Twoje oczekiwania: wymiana towaru na nowy, naprawa,
     obniżenie ceny lub odstąpienie od umowy (zwrot pieniędzy)</li></ul>”
  }'
```

zamknij

Przykładowy request

```
 {
    "id": "1556c6f7-c6a9-469e-9b3f-8f01eafaedc4",
    "seller": {
        "id": "62799754"
    },
    "name": "Główne warunki reklamacji",
    "individual": {
        "period": "P1Y"
    },
    "corporate": {
        "period": "P1Y"
    },
    "address": {
        "name": "test",
        "street": "ul. Testowa 7",
        "postCode": "61-135",
        "city": "Poznań",
        "countryCode": "PL"
    },
    "description": “<p>Co musi zawierać reklamacja? Reklamacja powinna zawierać:</p>
    <ul><li>Twoje imię i nazwisko oraz adres</li>
 <li>numer oferty na Allegro</li><li>numer zamówienia SO</li>
 <li>przedmiot reklamacji</li><li>Twoje oczekiwania: wymiana towaru na nowy,
 naprawa, obniżenie ceny lub odstąpienie od umowy (zwrot pieniędzy)</li></ul>”
 }
```

zamknij

Przykładowy response

#### Jak pobrać warunki reklamacji przypisane do konta

Za pomocą [GET /after-sales-service-conditions/implied-warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET) pobierzesz warunki reklamacji przypisane do zautoryzowanego konta. W odpowiedzi otrzymasz listę 60 warunków, która zawiera informacje o identyfikatorze oraz nazwie warunku. Możesz ją dostosować do własnych potrzeb za pomocą filtrów:

- offset - miejsce, od którego chcesz pobrać następną porcję danych.
- limit - liczba wyników w odpowiedzi. Domyślna i maksymalna wartość to 60,

Jeżeli chcesz pobrać szczegóły warunków reklamacji, przekaż ich identyfikator za pomocą [GET /after-sales-service-conditions/implied-warranties/{impliedWarrantyId}](https://developer.allegro.pl/#operation/getAfterSalesServiceImpliedWarrantyUsingGET).

Przykladowy request:

```
  curl -X GET \
  'https://api.allegro.pl/after-sales-service-conditions/implied-warranties/bbb2458-54f1-4dff-a9d4-c9067554390d' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
```

```
 {
    "id": bbb2458-54f1-4dff-a9d4-c9067554390d",
    "seller": {
        "id": "627909754"
    },
    "name": "Główne warunki reklamacji",
    "individual": {
        "period": "P6Y"
    },
    "corporate": {
        "period": "P6Y"
    },
    "address": {
        "name": "test",
        "street": "ul. Testowa 7",
        "postCode": "61-135",
        "city": "Poznań",
        "countryCode": "PL"
    },
    "description": “<p>Co musi zawierać reklamacja? Reklamacja powinna zawierać:</p>
  <ul><li>Twoje imię i nazwisko oraz adres</li>
  <li>numer oferty na Allegro</li>
  <li>numer zamówienia SO</li><li>przedmiot reklamacji</li>
  <li>Twoje oczekiwania: wymiana towaru na nowy, naprawa,
  obniżenie ceny lub odstąpienie od umowy (zwrot pieniędzy)</li></ul>””
 }
```

zamknij

Przykładowy response

#### Jak edytować informacje o warunkach reklamacji

Aby edytować informacje o warunkach zwrotu:

- dane, które otrzymałeś w poprzednim kroku, odpowiednio wyedytuj według własnych potrzeb i przekaż za pomocą [PUT /after-sales-service-conditions/implied-warranties/{impliedWarrantyId}](https://developer.allegro.pl/documentation/#operation/updateAfterSalesServiceImpliedWarrantyUsingPUT).
- przekaż wybrany identyfikator warunków reklamacji za pomocą [GET /after-sales-service-conditions/implied-warranties/{impliedWarrantyId}](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceImpliedWarrantyUsingGET), by otrzymać szczegółowe dane,
- za pomoca [GET /after-sales-service-conditions/implied-warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET) pobierz warunki reklamacji przypisane do zautoryzowanego konta. W odpowiedzi otrzymasz identyfikatory oraz nazwy warunków reklamacji,

```
 curl -X PUT \
 'https://api.allegro.pl/after-sales-service-conditions/implied-warranties/bbbc9778-54f1-4dff-a9d4-c9067554390d' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
    "id": "1556c6f7-c6a9-469e-9b3f-8f01eafaedc4",
    "seller": {
        "id": "279934754"
    },
    "name": "Główne warunki reklamacji",
    "individual": {
        "period": "P1Y"
    },
    "corporate": null,
    "address": {
        "name": "test",
        "street": "ul. Testowa 7",
        "postCode": "61-135",
        "city": "Poznań",
        "countryCode": "PL"
    },
    "description": “<p>Co musi zawierać reklamacja? Reklamacja powinna zawierać:</p>
    <ul><li>Twoje imię i nazwisko oraz adres</li>
    <li>numer oferty na Allegro</li><li>numer zamówienia SO</li>
    <li>przedmiot reklamacji</li><li>Twoje oczekiwania: wymiana towaru na nowy,
    naprawa, obniżenie ceny lub odstąpienie od umowy (zwrot pieniędzy)</li></ul>””
 }'
```

zamknij

Przykładowy request

### Jak zarządzać informacjami o gwarancjach

#### Jak dodać załącznik do informacji o gwarancjach

Utwórz obiekt załącznika za pomocą [POST /after-sales-service-conditions/attachments](https://developer.allegro.pl/documentation/#operation/createAfterSalesServiceConditionsAttachmentUsingPOST). W strukturze przekaż nazwę pliku w formacie .pdf.

Przykładowy request:

```
  curl -X POST \
  'https://api.allegro.pl/after-sales-service-conditions/attachments' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '
  {
    “name”: “warranty.pdf”             - nazwa pliku, który chcesz załączyć
  }'
```

Przykładowy response:

```
  {
    "id": "7c8f40bc-3e50-408b-a66b-48122e05d84e",
    "name": "warranty.pdf",
    "url": null
  }
```

Teraz użyj [PUT /after-sales-service-conditions/attachments/{attachmentId}](https://developer.allegro.pl/documentation/#operation/uploadAfterSalesServiceConditionsAttachmentUsingPUT)- jako attachmentId przekaż wartość id, którą otrzymałeś krok wcześniej. Pamiętaj, aby użyć adresu, który zwróciliśmy w nagłówku location.

Przykładowy request:

```
  curl -X PUT \
  'https://upload.allegro.pl/after-sales-service-conditions/attachments/7c8f40bc-3e50-408b-a66b-48122e05d84e' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/pdf'
  --data-binary "@warranty.pdf"    // wymagany, zawartość pliku z załącznikiem w postaci binarnej
```

Przykładowy response:

```
  {
    "id": "7c8f40bc-3e50-408b-a66b-48122e05d84e",
    "name": "warranty.pdf",
    "url": "https://after-sales.allegrostatic.com/after-sales-service-5c/7c8f40bc-3e50-408b-a66b-48122e05d84e"
  }
```

Obiekt, który otrzymałeś, możesz dodać do informacji o gwarancjach w polu attachment. W dalszej części poradnika opisujemy ten proces.

#### Jak dodać informacje o gwarancjach

Skorzystaj z [POST /after-sales-service-conditions/warranties](https://developer.allegro.pl/documentation/#operation/createAfterSalesServiceWarrantyUsingPOST), aby dodać nowe informacje o gwarancjach. W strukturze żądania przekaż pola:

- description - niewymagane, informacje dodatkowe np. gdzie szukać informacji, z kim i jak ma się kontaktować, jakie dokumenty będą potrzebne itp.
- attachment - niewymagane, załącznik do gwarancji,
- corporate.period - niewymagane, okres gwarancji w formacie ISO 8601 dla przedsiębiorców. Jako wartość możesz wskazać tylko miesiące, np. “P12M” oznacza 12 miesięcy. Jeżeli chcesz wskazać dożywotnią gwarancję, pozostaw to miejsce puste, a w polu individual.lifetime przekaż wartość true,
- individual.period - wymagane, okres gwarancji w formacie ISO 8601. Jako wartość możesz wskazać tylko miesiące, np. “P12M”, co oznacza 12 miesięcy. Jeżeli chcesz wskazać dożywotnią gwarancję, pozostaw to miejsce puste, a w polu individual.lifetime przekaż wartość true,
- type - wymagane, rodzaj gwarancji, dostępne wartości to MANUFACTURER (od producenta/dystrybutora) lub SELLER (od sprzedawcy),
- name - wymagane, nazwa dla informacji o gwarancji,

```
  curl -X POST \
  'https://api.allegro.pl/after-sales-service-conditions/warranties' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
  "name": "12 miesięcy",    // wymagane, nazwa informacji o
                                            gwarancjach
  "type": "MANUFACTURER",    // wymagane, rodzaj gwarancji
  "individual": {
    "period": "P12M",    // wymagane, okres gwarancji
    "lifetime": false    // niewymagane, czy gwarancja jest dożywotnia,
  },
  "corporate": {    // niewymagane, okres gwarancji dla przedsiębiorców
    "period": "P12M",
    "lifetime": false
  },
  "attachment": {        // niewymagane, informacje o załączniku
    "id": "54702c96-4ccd-4c0e-b4c7-382a71e810b5",
    "name": "warranty.pdf",
    "url": "https://after-sales.allegrostatic.com/after-sales-service-5c/7c8f40bc-3e50-408x-a66b-48122e05d84e"
}
  },
  "description":     // niewymagane, informacje dodatkowe
  "<p>Gwarancja producenta na 12 miesięcy</p>"
}'
```

zamknij

Przykładowy request

```
  {
    "id": "bce9e4ad-4e06-4478-8038-04f3cbed73f4",
    "seller": {
        "id": "6279923754"
    },
    "name": "12 miesięcy",
    "type": "MANUFACTURER",
    "individual": {
        "period": "P12M",
        "lifetime": false
    },
    "corporate": {
        "period": "P12M",
        "lifetime": false
    },
    "attachment": {
        "id": "54702c96-4ccd-4c0e-b4c7-382a71e810b5",
        "name": "warranty.pdf",
        "url": "https://after-sales.allegrostatic.com/after-sales-service-00/54702c96-4ccd-4c0e-b4c7-382a71e810b5"
    },
    "description": "<p>Gwarancja producenta na 12 miesięcy</p>"
  }
```

zamknij

Przykładowy response

#### Jak pobrać informacje o gwarancjach przypisanych do konta

Za pomocą [GET /after-sales-service-conditions/warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET_2) pobierzesz informacje o gwarancjach przypisanych do zautoryzowanego konta. W odpowiedzi otrzymasz listę 60 gwarancji, która zawiera informacje o identyfikatorze oraz nazwie warunków. Możesz ją dostosować do własnych potrzeb za pomocą filtrów:

- offset - miejsce, od którego chcesz pobrać następną porcję danych.
- limit - liczba wyników w odpowiedzi. Domyślna i maksymalna wartość to 60,

Jeżeli chcesz pobrać szczegóły informacji o gwarancji, przekaż ich identyfikator za pomocą [GET /after-sales-service-conditions/warranties/{warrantyId}](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceWarrantyUsingGET).

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/after-sales-service-conditions/warranties/bbb2458-54f1-4dff-a9d4-c9067554390d' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

```
  {
    "id": "bbb2458-54f1-4dff-a9d4-c9067554390d",
    "seller": {
        "id": "627120754"
    },
    "name": "default",
    "type": "MANUFACTURER",
    "individual": {
        "period": null,
        "lifetime": true
    },
    "corporate": {
        "period": null,
        "lifetime": true
    },
    "attachment": {
        "id": "564c8680-505c-4d34-a6d3-bd8e4d20b49d",
        "name": "uploaded_file.pdf",
        "url": "https://after-sales.allegrostatic.com/after-sales-service-b5/564c8680-505c-4d34-a6d3-bd8e4d20b49d"
    },
    "description": null,
  }
```

zamknij

Przykładowy response

#### Jak edytować informacje o gwarancjach

Aby edytować informacje o gwarancjach:

- dane, które otrzymałeś w poprzednim kroku, odpowiednio wyedytuj według własnych potrzeb i przekaż za pomocą [PUT /after-sales-service-conditions/warranties/{warrantyId}](https://developer.allegro.pl/documentation/#operation/updateAfterSalesServiceWarrantyUsingPUT).
- przekaż wybrany identyfikator gwarancji za pomocą [GET /after-sales-service-conditions/warranties/{warrantyId}](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceWarrantyUsingGET), by otrzymać szczegółowe dane,
- za pomoca [GET /after-sales-service-conditions/warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET_2) pobierz informacje o gwarancjach przypisane do zautoryzowanego konta. W odpowiedzi otrzymasz identyfikatory oraz nazwy gwarancji,

```
  curl -X PUT \
  'https://api.allegro.pl/after-sales-service-conditions/warranties/bbbc9712-54f1-4dff-a9d4-c9067554390d' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
    "id": "62c9bede-82be-4d17-831d-af66270d1ade",
    "seller": {
        "id": "62799754"
    },
    "name": "default",
    "type": "MANUFACTURER",
    "individual": {
        "period": null,
        "lifetime": true
    },
    "corporate": {
        "period": null,
        "lifetime": true
    },
    "attachment": {
        "id": "564c8680-505c-4d34-a6d3-bd8e4d20b49d",
        "name": "uploaded_file.pdf",
        "url": "https://after-sales.allegrostatic.com/after-sales-service-b5/564c8680-505c-4d34-a6d3-bd8e4d20b49d"
    },
    "description": null,
  }'
```

zamknij

Przykładowy request

### Jak zarządzać usługami dodatkowymi

Aby uatrakcyjnić Twoje oferty, możesz skorzystać z usług dodatkowych, np. zapakowanie na prezent, wniesienie, montaż, itd. Więcej informacji znajdziesz w [Pomocy Allegro](https://allegro.pl/pomoc/dla-sprzedajacych/wystawianie-oferty-przez-formularz/wniesienie-montaz-i-inne-uslugi-dodatkowe-w-ofertach-xG71gnKLDCG).

#### Jak pobrać listę dostępnych usług dodatkowych

Skorzystaj z [GET /sale/offer-additional-services/categories](https://developer.allegro.pl/documentation/#operation/getListOfAdditionalServicesDefinitionsCategoriesUsingGET), aby pobrać listę dostępnych usług dodatkowych.

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/offer-additional-services/categories' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
```

```
{
  "categories": [{
   "name": "Usługi wykonywane przed wysyłką",
   "definitions": [
      {
         "id": "GIFT_WRAP",     // identyfikator usługi dodatkowej
         "name": "Zapakuj na prezent",     // nazwa usługi dodatkowej
         "description": "Usługa polegająca na zapakowaniu kupionego towaru w ozdobne pudełko lub papier",    // opis usługi dodatkowej  
         "availableConstraints": [    // ograniczenia usługi dodatkowej
            {
               "type": "COUNTRY_SAME_QUANTITY"    // ograniczenie ilości usług dodatkowych, tzn. liczba usług dodatkowych musi być równa liczbie kupionych przedmiotów. Ograniczenie dotyczy usługi - Zapakuj na prezent (GIFT_WRAP).

            }
         ],
         "updatedAt": "2019-07-04T14:50:34.985Z"
      },
      {
    "name": "Usługi wniesienia",
    "definitions": [
     {
         "id": "CARRY_IN",
         "name": "Wniesienie",
         "description": "Opisz, na co powinien przygotować się kupujący i czy są 
         jakieś ograniczenia, np. piętro, do którego dostarczasz przesyłkę.",
         "availableConstraints": [
            {
               "type": "COUNTRY_DELIVERY_SAME_QUANTITY",    // ograniczenie ilości usług  dodatkowych i metod dostawy. Liczba usług dodatkowych musi być równa liczbie kupionych przedmiotów. Ponadto usługi są dostępne tylko przy określonych metodach dostawy.
               "availableDeliveryMethods": [     // metody dostawy dostępne dla danej usługi dodatkowej (metody dostawy sprawdzisz za pomocą GET /sale/delivery-methods).
                  "7203cb90-864c-4cda-bf08-dc883f0c78ad",
                  "45309171-0415-49cd-b2cf-89e9143d20f0",
                  "2b6ca59d-1e4c-426c-82a9-efcbd730846b",
      …               ]
            }
         ],
         "updatedAt": "2021-04-29T14:55:04.025Z"
      },
      {
         "id": "CARRY_IN_AND_PREPARATION",
         "name": "Wniesienie i przygotowanie do pracy",
         "description": "Opisz, co realizujesz w ramach Przygotowania do pracy 
         i czy są jakieś ograniczenia, np. piętro, do którego dostarczasz przesyłkę.",
         "availableConstraints": [
            {
               "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
               "availableDeliveryMethods": [
                  "7203cb90-864c-4cda-bf08-dc883f0c78ad",
                  "45309171-0415-49cd-b2cf-89e9143d20f0",
                  "2b6ca59d-1e4c-426c-82a9-efcbd730846b",
                  …
               ]
            }
         ],
         "updatedAt": "2021-04-29T15:05:58.499Z"
      },
      {
         "id": "CARRY_IN_AND_SETUP",
         "name": "Wniesienie i ustawienie",
         "description": "Opisz, co realizujesz w ramach Ustawienia 
         i czy są jakieś ograniczenia, np. piętro, do którego dostarczasz przesyłkę.",
         "availableConstraints": [
            {
               "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
               "availableDeliveryMethods": [
                  "7203cb90-864c-4cda-bf08-dc883f0c78ad",
                  "45309171-0415-49cd-b2cf-89e9143d20f0",
                  "2b6ca59d-1e4c-426c-82a9-efcbd730846b",
                  …               ]
            }
         ],
         "updatedAt": "2021-04-29T15:13:26.141Z"
      },
      {
         "id": "INSTALLATION",
         "name": "Montaż",
         "description": "Opisz, co realizujesz w ramach Montażu 
         i czy są jakieś ograniczenia.",
         "availableConstraints": [
            {
               "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
               "availableDeliveryMethods": [
                  "7203cb90-864c-4cda-bf08-dc883f0c78ad",
                  "45309171-0415-49cd-b2cf-89e9143d20f0",
                  …
               ]
            }
         ],
         "updatedAt": "2021-04-29T15:10:59.230Z"
      },
      {
         "id": "CARRY_IN_AND_INSTALLATION",
         "name": "Wniesienie i montaż",
         "description": "Opisz, co realizujesz w ramach Montażu 
         i czy są jakieś ograniczenia, np. piętro, do którego dostarczasz przesyłkę.",
         "availableConstraints": [
            {
               "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
               "availableDeliveryMethods": [
                  "7203cb90-864c-4cda-bf08-dc883f0c78ad",
                  "45309171-0415-49cd-b2cf-89e9143d20f0",
                  "2b6ca59d-1e4c-426c-82a9-efcbd730846b",
                  …
               ]
            }
         ],
         "updatedAt": "2021-04-29T15:01:36.080Z"
      },
      {
         "id": "CARRY_IN_AND_INSTALLATION_AND_PREPARATION",
         "name": "Wniesienie, montaż i przygotowanie do pracy",
         "description": "Opisz, co realizujesz w ramach Montażu 
         i Przygotowania do pracy, i czy są jakieś ograniczenia, 
         np. piętro, do którego dostarczasz przesyłkę.",
         "availableConstraints": [
            {
               "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
               "availableDeliveryMethods": [
                  "7203cb90-864c-4cda-bf08-dc883f0c78ad",
                  "45309171-0415-49cd-b2cf-89e9143d20f0",
                  "2b6ca59d-1e4c-426c-82a9-efcbd730846b",
                  …
               ]
            }
         ],
         "updatedAt": "2021-04-29T15:08:56.827Z"
      },
      {
         "id": "DOOR_OPENING_DIRECTION_CHANGE",
         "name": "Zmiana kierunku otwierania drzwi",
         "description": "Zmiana kierunku otwierania drzwi",
         "availableConstraints": [
            {
               "type": "COUNTRY_SAME_QUANTITY"
            }
         ],
         "updatedAt": "2017-11-08T15:16:45.266Z"
      }
   ]
 }]
}
```

zamknij

Przykładowy response

#### Jak dodać nową grupę usług dodatkowych

Skorzystaj z [POST /sale/offer-additional-services/groups](https://developer.allegro.pl/documentation/#operation/createAdditionalServicesGroupUsingPOST), aby utworzyć nową grupę usług dodatkowych.

Przykładowy request:

```
curl -X POST \
  'https://api.allegro.pl/sale/offer-additional-services/groups' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json’ \
  -H 'Content-type: application/vnd.allegro.public.v1+json' \
  -d '{
  "name": "nazwa grupy",    // wymagane, nazwa nowej grupy usług
                                              dodatkowych
  "additionalServices": [    // wymagane, typy usług dodatkowych 
                                              dostępnych w ramach danej grupy
    {
      "definition": {
        "id": "CARRY_IN"    // wymagane, dostępną listę wartości pobierzesz za pomocą GET /sale/offer-additional-services/definitions
      },
      "description": "opis usługi dodatkowej",    // wymagane, opis usługi dodatkowej
      "configurations": [     // wymagane, cena danej usługi dodatkowej
        {
          "price": {
            "amount": "49.99",
            "currency": "PLN"
          },
          "constraintCriteria": {    // wymagane, ograniczenia danej usługi dodatkowej
            "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
            "country": "PL",
            "deliveryMethods": [    // wymagane dla typu COUNTRY_DELIVERY_SAME_QUANTITY, niewymagane dla  COUNTRY_SAME_QUANTITY; przypisane metody dostawy danej usługi dodatkowej
              {"id": "7203cb90-864c-4cda-bf08-dc883f0c78ad"}     // wymagane, identyfikator danej metody dostawy (metody dostawy sprawdzisz za pomocą GET /sale/delivery-methods)).
            ]
          }
        }
      ]
    }
  ]
"language": "pl-PL"    // opcjonalne, określ język bazowy grupy usług dodatkowych. Jeśli nie przekażesz tego pola, to domyślnie przypiszemy wartość “pl-PL”.
}'
```

```
{
    "id": "0aba7cf9-8896-44a4-8919-266bf6516a82",    // identyfikator utworzonej grupy usług dodatkowych
    "name": "nazwa grupy",     // nazwa utworzonej grupy usług dodatkowych
    "seller": {
        "id": "53703086"    // dentyfikator sprzedawcy
    },
    "additionalServices": [     // kryteria, które opisują warunki wybranej grupy sług dodatkowych. np. cena
        {
            "definition": {
                "id": "CARRY_IN"
            },
            "description": "opis usługi dodatkowej",
            "configurations": [
                {
                    "price": {
                        "amount": "49.99",
                        "currency": "PLN"
                    },
                    "constraintCriteria": {
                        "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
                        "country": "PL",
                        "deliveryMethods": [
                            {"id": "7203cb90-864c-4cda-bf08-dc883f0c78ad"}
                        ]
                    }
                }
            ]
        }
    ],
    "language": "pl-PL",
    "createdAt": "2017-10-04T11:41:30.904Z",
    "updatedAt": "2017-10-04T11:41:30.905Z",
    "managedByAllegro": false
}
```

zamknij

Przykładowy response

#### Jak zaktualizować grupę usług dodatkowych

Skorzystaj z [PUT /sale/offer-additional-services/groups/{groupId}](https://developer.allegro.pl/documentation/#operation/modifyAdditionalServicesGroupUsingPUT), aby zaktualizować dane wybranej grupy usług dodatkowych.

Przykładowy request:

```
curl -X PUT \
  'https://api.allegro.pl/sale/offer-additional-services/groups/{groupId}' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json’ \
  -H 'Content-type: application/vnd.allegro.public.v1+json' \
  -d '{
  "name": "nowa nazwa grupy",
  "additionalServices": [
    {
      "definition": {
        "id": "CARRY_IN"
      },
      "description": "nowy opis usługi dodatkowej",
      "configurations": [
        {
          "price": {
            "amount": "49.99",
            "currency": "PLN"
          },
          "constraintCriteria": {
            "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
            "country": "PL",
            "deliveryMethods": [
              {"id": "7203cb90-864c-4cda-bf08-dc883f0c78ad"}
            ]
          }
        }
      ]
    }
  ]
}'
```

```
{
    "id": "0aba7cf9-8896-44a4-8919-266bf6516a82",
    "name": "nowa nazwa grupy",
    "seller": {
        "id": "53703086"
    },
    "additionalServices": [
        {
            "definition": {
                "id": "CARRY_IN"
            },
            "description": "nowy opis usługi dodatkowej",
            "configurations": [
                {
                    "price": {
                        "amount": "49.99",
                        "currency": "PLN"
                    },
                    "constraintCriteria": {
                        "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
                        "country": "PL",
                        "deliveryMethods": [
                            {"id": "7203cb90-864c-4cda-bf08-dc883f0c78ad"}
                        ]
                    }
                }
            ]
        }
    ],
    "language": "pl-PL",
    "createdAt": "2017-10-04T11:41:30.904Z",
    "updatedAt": "2017-10-04T12:00:51.929Z",
    "managedByAllegro": false
}
```

zamknij

Przykładowy response

#### Jak pobrać listę grup usług dodatkowych na koncie

Skorzystaj z [GET /sale/offer-additional-services/groups](https://developer.allegro.pl/documentation/#operation/getListOfAdditionalServicesGroupsUsingGET), aby pobrać listę grup z dostępnymi usługami dodatkowymi na koncie.

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/offer-additional-services/groups \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
```

```
{
  "additionalServicesGroups": [    // konfiguracja tablica z grupami usług dodatkowych
    {
      "id": "8603fbbb-0f0e-4999-945e-258c4c96c7d6",    // identyfikator danej grupy usług dodatkowych
      "name": "Mój pakiet usług",    // nazwa danej grupy usług dodatkowych
      "seller": {    // identyfikator sprzedawcy
        "id": "53703086"
      },
      "additionalServices": [    // tablica usług dodatkowych w danej grupie
        {
          "definition": {
            "id": "GIFT_WRAP"
          },
          "description": "Zapakuj na prezent",
          "configurations": [    // konfiguracja danej usługi dodatkowej
            {
              "price": {
                "amount": "20",
                "currency": "PLN"
              },
              "constraintCriteria": {
                "type": "COUNTRY_SAME_QUANTITY",
                "country": "PL"
              }
            }
          ]
        },
        {
          "definition": {
            "id": "CARRY_IN"
          },
          "description": "Wniesienie na dowolne piętro",
          "configurations": [
            {
              "price": {
                "amount": "22",
                "currency": "PLN"
              },
              "constraintCriteria": {
                "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
                "country": "PL",
                "deliveryMethods": [
                  {"id": "7203cb90-864c-4cda-bf08-dc883f0c78ad"},
                  {"id": "4dd9c904-e892-4649-bdec-5454d6b53d28"},
                  {"id": "f7e952b5-9ae8-40a9-90dd-e71ab9da29dd"},
                  {"id": "5d9c7838-e05f-4dec-afdd-58e884170ba7"}
                ]
              }
            }
          ]
        },
        {
          "definition": {
            "id": "INSTALLATION"
          },
          "description": "Montaż",
          "configurations": [
            {
              "price": {
                "amount": "25",
                "currency": "PLN"
              },
              "constraintCriteria": {
                "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
                "country": "PL",
                "deliveryMethods": [
                  {"id": "7203cb90-864c-4cda-bf08-dc883f0c78ad"},
                  {"id": "4dd9c904-e892-4649-bdec-5454d6b53d28"},
                  {"id": "f7e952b5-9ae8-40a9-90dd-e71ab9da29dd"},
                  {"id": "ffb2643b-4b90-4925-9d29-0d93ad9488a6"},
                  {"id": "74bc07eb-552f-4581-b68c-da46716d4a9a"}
                ]
              }
            }
          ]
        }
      ],
      "language": "pl-PL",
      "createdAt": "2017-08-07T12:08:36.151Z",
      "updatedAt": "2017-08-07T12:08:36.151Z",
      "managedByAllegro": false
    }
  ]
}
```

zamknij

Przykładowy response

#### Jak pobrać wybraną grupę usług dodatkowych

Skorzystaj z [GET /sale/offer-additional-services/groups/{groupId}](https://developer.allegro.pl/documentation/#operation/getAdditionalServicesGroupUsingGET), aby pobrać wybraną grupę usług dodatkowych, którą możesz przypisać do oferty. Identyfikator grupy usług dodatkowych - {groupId} - uzyskasz za pomocą [GET /sale/offer-additional-services/groups](https://developer.allegro.pl/documentation/#operation/getListOfAdditionalServicesGroupsUsingGET).

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/offer-additional-services/groups/{groupId}' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
```

```
{
    "id": "0a3e6ca4-b8fb-4cce-9d47-4ca47ef49903",
    "name": "Pakiet prezent i wniesienie",
    "seller": {
        "id": "53703086"
    },
    "additionalServices": [
        {
            "definition": {
                "id": "GIFT_WRAP"
            },
            "description": "Opis zapakuj na prezent",
            "configurations": [
                {
                    "price": {
                        "amount": "15",
                        "currency": "PLN"
                    },
                    "constraints": {
                        "type": "COUNTRY_SAME_QUANTITY",
                        "country": "PL"
                    }
                }
            ]
        },
        {
            "definition": {
                "id": "CARRY_IN"
            },
            "description": "Opis wniesienia",
            "configurations": [
                {
                    "price": {
                        "amount": "16",
                        "currency": "PLN"
                    },
                    "constraintCriteria": {
                        "type": "COUNTRY_DELIVERY_SAME_QUANTITY",
                        "country": "PL",
                        "deliveryMethods": [
                            {"id": "7203cb90-864c-4cda-bf08-dc883f0c78ad"},
                            {"id": "45309171-0415-49cd-b2cf-89e9143d20f0"},
                            {"id": "2b6ca59d-1e4c-426c-82a9-efcbd730846b"},
                            {"id": "74bc07eb-552f-4581-b68c-da46716d4a9a"},
                            {"id": "ffb2643b-4b90-4925-9d29-0d93ad9488a6"}
                        ]
                    }
                }
            ]
        }
    ],
    "language": "pl-PL",
    "createdAt": "2017-08-04T12:46:36.996Z",
    "updatedAt": "2017-08-04T12:46:36.996Z",
    "managedByAllegro": false
}
```

zamknij

Przykładowy response

Aby skorzystać z [POST /sale/offer-additional-services/groups](https://developer.allegro.pl/documentation/#operation/createAdditionalServicesGroupUsingPOST) i [PUT /sale/offer-additional-services/groups/{groupId}](https://developer.allegro.pl/documentation/#operation/modifyAdditionalServicesGroupUsingPUT), musisz być zautoryzowany jako sprzedawca.

### Jak zarządzać promowaniem

#### Jak pobrać dostępne opcje promowania

Skorzystaj z [GET /sale/offer-promotion-packages](https://developer.allegro.pl/documentation/#operation/getAvailableOfferPromotionPackages), aby pobrać listę dostępnych opcji promowania. Udostępniamy dwa pakiety wyróżnień oraz jedną opcję dodatkową:

Flexible Feature - Wyróżnienie Elastyczne, za które opłatę naliczamy codziennie,

Emphasized - Wyróżnienie, za które opłatę naliczamy co dziesięć dni,

Department page promo - opcja dodatkowa, Promowanie na stronie działu, opłatę naliczamy co dziesięć dni.

W odpowiedzi otrzymasz:

- długość cyklu rozliczeniowego.
- nazwę pakietu promowania,
- ID pakietu promowania,

Przykładowy request:

```
 curl -X GET \
    'https://api.allegro.pl/sale/offer-promotion-packages' \
    -H 'Authorization: Bearer {token}' \
    -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
 {
    "basePackages": [    // podstawowe opcje promowania
        {
            "id": "emphasized10d",    // ID pakietu promowania
            "name": "Emphasized",    // nazwa pakietu promowania
            "cycleDuration": "PT240H"    // długość cyklu rozliczeniowego
        },
        {
            "id": "emphasized1d",
            "name": "Flexible Emphasized",
            "cycleDuration": "PT24H"
        }
    ],
    "extraPackages": [    // dodatkowa opcja promowania
        {
            "id": "departmentPage",
            "name": "Department page promo",
            "cycleDuration": "PT240H"
        }
    ]
 }
```

#### Jak pobrać opcje promowania dla wielu ofert

Za pomocą [GET /sale/offers/promo-options](https://developer.allegro.pl/documentation/#operation/getPromoOptionsForSellerOffersUsingGET) pobierzesz opcje promowania dla wszystkich ofert zalogowanego sprzedawcy. Domyślnie w odpowiedzi otrzymasz 5000 opcji promowań. Aby dopasować wyniki do swoich potrzeb, użyj filtrów:

- offset - by wskazać miejsce, od którego chcesz pobrać kolejną porcję danych (domyślnie 0).
- limit - liczba wyników, które zwrócimy w odpowiedzi. Domyślna wartość to 5000, maksymalna 5000;

Przykładowy request:

```
curl -X GET \
'https://api.allegro/sale/offers/promo-options' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
{
    "promoOptions": [
{
            "offerId": "7685430123",    // numer oferty
            "marketplaceId": "allegro-pl",    // serwis bazowy
            "basePackage": {    // podstawowe opcje promowania
                "id": "emphasized1d",    // ID pakietu promowania
                "validFrom": "2022-03-21T09:20:50.276Z",    // data, od kiedy pakiet jest aktywny
                "validTo": null,     // data, do kiedy pakiet jest aktywny
                "nextCycleDate": "2022-04-02T09:20:50.276Z"    // data następnego cyklu rozliczeniowego
            },
            "extraPackages": [],    // dodatkowe opcje promowania
            "pendingChanges": null,     // informacje o nowych pakietach promowania, które włączymy po zakończeniu aktualnego okresu rozliczeniowego
            "additionalMarketplaces": []    // serwisy dodatkowe
        },
        {
            "offerId": "7687105138",
            "basePackage": {
                "id": "emphasized1d",
                "validFrom": "2022-03-11T09:21:57Z",
                "validTo": null,
                "nextCycleDate": "2022-04-02T09:21:57Z"
            },
            "extraPackages": [],
            "pendingChanges": null
        }
    ],
    "count": 2,     // liczba zwróconych opcji promowań
    "totalCount": 2    // całkowita liczba opcji promowań
}
```

#### Jak dodać lub zmienić opcje promowania w pojedynczej ofercie

Za pomocą [POST /sale/offers/{offerId}/promo-options-modification](https://developer.allegro.pl/documentation/#operation/modifyOfferPromoOptionsUsingPOST) dodasz, zmienisz lub wyłączysz opcje promowania w pojedynczej ofercie. Jako offerId przekaż numer oferty, której dotyczy modyfikacja. W ofercie może być aktywny tylko jeden z podstawowych pakietów promowania.

Przykładowy request, jak dodać promowanie:

```
 curl -X POST \
    'https://api.allegro.pl/sale/offers/{offerId}/promo-options-modification' \
    -H 'Authorization: Bearer {token}' \
    -H 'Accept: application/vnd.allegro.public.v1+json' \
    -d '{
        "modifications": [
            {
            "modificationType": "CHANGE",    // typ modyfikacji, dostępne wartości to “CHANGE” (dodaj lub zmień), “REMOVE_WITH_END_OF_CYCLE” (usuń z końcem cyklu rozliczeniowego), “REMOVE_NOW” (usuń natychmiast),
             "packageType": "BASE",    // typ pakietu promowania, dostępne wartości to “BASE” (opcje podstawowe) lub “EXTRA” (opcje dodatkowe),
             "packageId": "emphasized10d"    // ID pakietu promowania, który możesz pobrać za pomocą GET /sale/offer-promotion-packages
      }
    ]
  }'
```

Przykładowy response:

```
  {
  "offerId": "13613945976",     // numer oferty
  "marketplaceId": "allegro-pl",    // serwis bazowy
  "basePackage": {    // informacje o aktualnie przypisanym podstawowym pakiecie promowania
    "id": "emphasized10d",    // D pakietu promowania
    "validFrom": "2020-10-20T09:11:41.185Z",    // data, od kiedy pakiet jest aktywny
    "validTo": null,     // data, do kiedy pakiet jest aktywny. Wartość zwracamy tylko, gdy wyłączenie pakietu jest w trakcie.
    "nextCycleDate": "2020-10-30T09:11:41.185Z"    // data następnego cyklu rozliczeniowego
  },
  "extraPackages": [],    // informacje o aktualnie przypisanym dodatkowym pakiecie promowania
  "additionalMarketplaces": []    // serwisy dodatkowe
  }
```

Przykładowy request, jak zmienić promowanie:

```
 curl -X POST \
    'https://api.allegro.pl/sale/offers/{offerId}/promo-options-modification' \
    -H 'Authorization: Bearer {token}' \
    -H 'Accept: application/vnd.allegro.public.v1+json' \
    -d '{
        "modifications": [
            {
               "modificationType": "CHANGE",      
               "packageType": "BASE",        
               "packageId": "emphasized1d"      
            }
        ]
    }'
```

Przykładowy response:

```
 {
  "offerId": "13613945976",    // numer oferty
  "marketplaceId": "allegro-pl",    // serwis bazowy
  "basePackage": {    // informacje o aktualnie przypisanym podstawowym pakiecie promowania
    "id": "emphasized10d",    // ID pakietu promowania
    "validFrom": "2020-10-20T09:11:41.185Z",    // data, od kiedy pakiet jest aktywny
    "validTo": "2020-10-30T09:11:41.185Z",    // data, do kiedy pakiet jest aktywny
    "nextCycleDate": null
  },
   "extraPackages": [],        // informacje o aktualnie przypisanym dodatkowym pakiecie promowania
   "additionalMarketplaces": []    // serwisy dodatkowe
   "pendingChanges": {    // informacje o nowych pakietach promowania, które włączymy po zakończeniu aktualnego okresu rozliczeniowego
    "basePackage": {                        
      "id": "emphasized1d",    // ID pakietu promowania
      "validFrom": "2020-10-30T09:11:41.185Z",    // data, od kiedy pakiet jest aktywny
      "validTo": null,    // data, do kiedy pakiet jest aktywny
      "nextCycleDate": "2020-10-31T09:11:41.185Z"    // data następnego cyklu rozliczeniowego
    }
  }
 }
```

Przykładowy request, jak usunąć promowanie:

```
 curl -X POST \
    'https://api.allegro.pl/sale/offers/{offerId}/promo-options-modification' \
    -H 'Authorization: Bearer {token}' \
    -H 'Accept: application/vnd.allegro.public.v1+json' \
    -d '{
    "modifications": [
        {
             "modificationType": "REMOVE_WITH_END_OF_CYCLE",  
             "packageType": "BASE",        
             "packageId": "emphasized1d"     
        }
    ]
  }'
```

Przykładowy response:

```
  {
    "offerId": "13613945976",    // numer oferty
    "marketplaceId": "allegro-pl",    // serwis bazowy
    "basePackage": {                
        "id": "emphasized1d",                    
        "validFrom": "2020-10-30T09:11:41.185Z",        
        "validTo": "2020-10-31T09:11:41.185Z",            
        "nextCycleDate": null
    },
    "extraPackages": [ ],
    "additionalMarketplaces": []    // serwisy dodatkowe
  }
```

#### Jak pobrać opcje promowania przypisane do oferty

Aktualnie przypisane do oferty pakiety opcji promowania pobierzesz za pomocą [GET /sale/offers/{offerId}/promo-options](https://developer.allegro.pl/documentation/#operation/getOfferPromoOptionsUsingGET). W sekcji pendingChanges zwrócimy informacje o nowych opcjach promowania, które włączymy po zakończeniu aktualnego cyklu rozliczeniowego. Jako offerId przekaż numer oferty, dla której chcesz pobrać aktualne dane.

Przykładowy request

```
    curl -X GET \
    'https://api.allegro/sale/offers/{offerId}/promo-options' \
    -H 'Authorization: Bearer {token}' \
    -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response

```
 {
  "offerId": "13613945976",    // numer oferty
  "marketplaceId": "allegro-pl",     // serwis bazowy
  "basePackage": {    // informacje o aktualnie przypisanym podstawowym pakiecie promowania
    "id": "emphasized10d",    // D pakietu promowania
    "validFrom": "2020-06-05T00:00:01Z",    // data, od kiedy pakiet jest aktywny
    "validTo": "2020-06-15T00:00:00Z",     // data, do kiedy pakiet jest aktywny
    "nextCycleDate": null,    // data następnego cyklu rozliczeniowego
   },
  "extraPackages": [    // informacje o aktualnie przypisanym dodatkowym pakiecie promowania
   {
    "id":"departmentPage",
    "validFrom": "2020-06-10T00:00:01Z",
    "nextCycleDate": "2020-06-10T00:00:01Z",
    "validTo": null,
   }
  ],
  "additionalMarketplaces": [],    // serwisy dodatkowe
  "pendingChanges": [    // informacje o nowych pakietach promowania, które włączymy po zakończeniu aktualnego okresu rozliczeniowego
    "basePackage": {
      "id": "emphasized1d",
      "validFrom": "2020-06-15T00:00:01Z",
      "validTo": null,
      "nextCycleDate": null,
   }
  ]
 }
```

#### Jak dodać lub edytować opcje promowania na wielu ofertach

Za pomocą [PUT /sale/offers/promo-options-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/promoModificationCommandUsingPUT) dodasz lub zmienisz opcje promowania. Jako commandId przekaż wygenerowany we własnym zakresie numer UUID.

Przykładowy request

```
    curl -X PUT \
    'https://api.allegro/sale/offers/promo-options-commands/d8ce32f4-d6fc-4e2d-87ff-3f3e1c78843b' \
    -H 'Authorization: Bearer {token}' \
    -H 'Accept: application/vnd.allegro.public.v1+json' \
    -d '{
    "offerCriteria": [
    {
      "offers": [    // lista ofert, w których chcesz wykonać zmiany
        {
          "id": "12345678"
        }
      ],
      "type": "CONTAINS_OFFERS"
    }
  ],
    "modification": {
        "basePackage": {
        "id": "emphasized10d"
      },
      "extraPackages": [
        {
          "id": "departmentPage"
        }
      ],
      "modificationTime": "END_OF_CYCLE"    // kiedy chcesz wykonać zmianę, dostępne wartości to “NOW” (od razu) oraz “END_OF_CYCLE” (z końcem cyklu, jest to wartość domyślna)
      }
    }'
```

Przykładowy response

```
    {
    "id": "d8ce32f4-d6fc-4e2d-87ff-3f3e1c78843b",
    "taskCount": {
        "failed": 0,
        "success": 0,
        "total": 0
        }
    }
```

Zasób działa asynchronicznie, dlatego w odpowiedzi otrzymasz same zera. Aby sprawdzić status wykonania zadania, użyj [GET /sale/offers/promo-options-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getPromoModificationCommandResultUsingGET). Dzięki temu otrzymasz informację, do ilu ofert prawidłowo przypisaliśmy pakiet promowania i dla ilu zakończyło się to błędem.

#### Jak sprawdzić szczegółowy raport zadania

Aby sprawdzić szczegółowy raport zadania, użyj [GET /sale/offers/promo-options-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getPromoModificationCommandDetailedResultUsingGET). W odpowiedzi zwrócimy:

- informacje o modyfikacjach.
- informację o błędach w przypadku nieudanej próby przypisania pakietu promowania,
- status próby przypisania pakietu promowania,
- datę wykonania danego zadania,
- datę zlecenia przypisania pakietu promowania,
- identyfikatory ofert powiązane z danym zadaniem,

Aby zawęzić wyniki, możesz użyć filtrów, którymi określisz:

- offset - miejsce od którego, chcesz pobrać następną porcję danych.
- limit - liczbę zwróconych wyników. Domyślna wartość to 100, maksymalna 1000;

Przykładowy request

```
    curl -X GET \
    'https://api.allegro/sale/offers/promo-options-commands/d8ce32f4-d6fc-4e2d-87ff-3f3e1c78843b/tasks?offset=0&limit=100' \
    -H 'Authorization: Bearer {token}' \
    -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response

```
 {
  "tasks": [
    {
      "offer": {
        "id": "12345678"    // ID oferty
      },
      "scheduledAt": "2020-04-14T08:43:54Z",    // data zlecenia przypisania pakietu promowania
      "finishedAt": "2020-04-14T08:43:54Z",    // data wykonania zadania
      "status": "FINISHED"    // status wykonania zadania, dostępne wartości to “FINISHED” (zakończone prawidłowo), “IN_PROGRESS” (w trakcie przetwarzania), “ERROR” (wystąpiły błędy)
      "errors": []
    }
   ],
     "modification": {    // informacje o modyfikacjach dla danej oferty
       "basePackage": {"id":"emphasized10d" },    // ID pakietu promowania
       "modificationTime": "END_OF_CYCLE"    //  termin wykonania zmiany, jaki określiłeś w żądaniu
   },
     "additionalMarketplaces": []    // serwisy dodatkowe
  }
```

### Jak zarządzać tłumaczeniami

#### Tłumaczenia ofert

Język bazowy, który jest podstawą do dalszych tłumaczeń, określisz w polu “language”. Język bazowy możesz zmienić wyłącznie, kiedy oferta jest w statusie INACTIVE (jest szkicem).

Ofertę tłumaczymy automatycznie na język angielski/polski oraz na język każdego z serwisów dodatkowych (także za każdym razem, gdy zmienisz tytuł lub opis), jeśli:

- została wystawiona przez konto firmowe.
- kategoria, w której jest wystawiona wystawiona, nie znajduje się na liście kategorii, których nie tłumaczymy automatycznie (Książki i Antykwariat),
- jest w innym języku bazowym niż angielski/polski,
- kraj, do którego możliwa jest wysyłka, jest różny od kraju operacyjnego serwisu (dotyczy wyłącznie tłumaczenia na angielski),
- jest w statusie ACTIVE,

Możesz również przekazać nam własne tłumaczenie, w takim przypadku nie będziemy go automatycznie aktualizować.

Za każdym razem, kiedy tłumaczenie oferty zostanie zaktualizowane, otrzymasz zdarzenie "OFFER_TRANSLATION_UPDATED” w dzienniku ofertowym [GET /sale/offer-events](https://developer.allegro.pl/documentation/#operation/getOfferEvents).

##### Jak pobrać tłumaczenie oferty

Za pomocą [GET /sale/offers/{offerId}/translations](https://developer.allegro.pl/documentation/#operation/getOfferTranslationUsingGET) pobierzesz listę dostępnych tłumaczeń dla wskazanej oferty. Za pomocą parametru language wskaż wartość w formacie [BCP-47](https://tools.ietf.org/rfc/bcp/bcp47), aby pobrać tłumaczenie w wybranym języku. Listę dostępnych wartości dla tego parametru znajdziesz w naszej dokumentacji. Jeśli nie wskażesz wartości w tym polu, zwrócimy wszystkie dostępne tłumaczenia oferty, włącznie z językiem bazowym.

Przykładowy request:

```
 curl -X GET \
 'https://api.allegro.pl/sale/offers/10790622696/translations?language=en-US' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \ 
 -H 'Content-Type: application/vnd.allegro.public.v1+json' \
```

Przykładowy response:

```
 {
  "translations": [        // lista dostępnych tłumaczeń
    {
      "description": {    // informacje o tłumaczeniu opisu oferty
        "translation": {    // tłumaczenie opisu oferty
          "sections": [{
            "items": [{
              "type": "TEXT",
              "content": "<p>English description</p>"
              },
              {
             "type": "IMAGE",
             "url": "https://img.allegrogroup.com/image.jpg"
             }
           ]
         }]
        },
        "type": "AUTO"    // typ tłumaczenia, zwracamy jedną z wartości:  “AUTO” (tłumaczenie automatyczne, wykonane przez Allegro na podstawie języka bazowego oferty), “MANUAL” (tłumaczenie własne dostarczone przez użytkownika), BASE (oryginalna treść oferty w zadeklarowanym języku bazowym)
      },
      "language": "en-US",    // język tłumaczenia
      "title": {    // informacje o tłumaczeniu tytułu
        "translation": "Blue Jeans",    // tłumaczenie tytułu oferty
        "type": "AUTO"    // typ tłumaczenia
      }
    }
  ]
 }
```

##### Jak dodać lub zaktualizować tłumaczenie oferty

Za pomocą [PATCH /sale/offers/{offerId}/translations/{language}](https://developer.allegro.pl/documentation/#operation/updateOfferTranslationUsingPATCH) dodasz lub zaktualizujesz tłumaczenie swojej oferty. Jeśli przekażesz nam własne tłumaczenie, nie będziemy już tłumaczyć oferty automatycznie.

Jako {language} wskaż jeden z dostępnych języków w formacie [BCP-47](https://tools.ietf.org/rfc/bcp/bcp47), które wymieniliśmy w naszej dokumentacji. W przekazywanej strukturze wskaż przynajmniej jeden z elementów, który chcesz przetłumaczyć - “title” (tytuł) lub “description” (opis).

Ważne! Jeśli przekazujesz tłumaczenie opisu oferty, pamiętaj, aby przekazać całą strukturę tego pola - włącznie z obrazkami.

Jeżeli wykonasz próbę aktualizacji tłumaczenia opisu oferty bez faktycznych zmian w strukturze żądania, w odpowiedzi zwrócimy błąd 422 Unprocessable entity. Podobny błąd otrzymasz, jeśli w ofercie doszło już do zakupu lub któryś z użytkowników bierze udział w licytacji.

Przykładowy request:

```
 curl -X PATCH \
 'https://api.allegro.pl/sale/offers/10790622696/translations/en-US' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \ 
 -H 'Content-Type: application/vnd.allegro.public.v1+json' \
 -d '{
 "description": {
   "translation": {
     "sections": [{
       "items": [{
         "type": "TEXT",
         "content": "<p>English description</p>"
        },
        {
        "type": "IMAGE",
        "url": "https://img.allegrogroup.com/image.jpg"
        }
      ]
   }]
 }
 "title": {
    "translation": "Blue Jeans"
  }
 }'
```

Przykładowy response:

```
 Status 200 Update successful 
```

##### Jak usunąć tłumaczenie

Za pomocą [DELETE /sale/offers/{offerId}/translations/{language}](https://developer.allegro.pl/documentation/#operation/deleteManualTranslationUsingDELETE) usuniesz wybrane własne tłumaczenie oferty. Jako {language} wskaż dostępny język tłumaczenia w formacie [BCP-47](https://tools.ietf.org/rfc/bcp/bcp47), a w parametrze element określ, czy chcesz usunąć tłumaczenie pola “title” albo “description”. Jeśli nie przekażesz tego parametru, usuniemy tłumaczenie obu sekcji.

Jeśli usuniesz własne tłumaczenie oferty, to na podstawie aktualnego tytułu i opisu ponownie wygenerujemy automatyczne tłumaczenie dla języka, dla którego usuwasz wskazane elementy (pod warunkiem, że zakwalifikowaliśmy ofertę do automatycznego tłumaczenia na ten język).

Przykładowy request:

```
 curl -X DELETE \
 'https://api.allegro.pl/sale/offers/10790622696/translations/en-US?element=description' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \ 
 -H 'Content-Type: application/vnd.allegro.public.v1+json' \
```

Przykładowy response:

```
 Status 200 OK
```

#### Tłumaczenia usług dodatkowych

##### Jak pobrać tłumaczenie dla danego pakietu usług dodatkowych

Za pomocą [GET /sale/offer-additional-services/groups/{groupId}/translations](https://developer.allegro.pl/documentation/#operation/getAdditionalServiceGroupTranslations) pobierzesz tłumaczenie dla danego pakietu usług dodatkowych.

Skorzystaj z parametru language i wskaż w nim wartość w formacie [BCP-47](https://tools.ietf.org/rfc/bcp/bcp47), aby pobrać tłumaczenie w wybranym języku. Listę dostępnych wartości dla tego parametru znajdziesz w naszej dokumentacji.

Przykładowy request:

```
curl -X GET \
'https://api.allegro.pl/sale/offer-additional-services/groups/fd2b1ee9-3ace-4f9a-b2d8-839980f2a484/translations?language=pl-PL' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \ 
```

Przykładowy response:

```
{
   "translations": [    // lista dostępnych tłumaczeń
       {
           "language": "pl-PL",    // język tłumaczenia
           "additionalServices": {
               "translation": [
                   {
                       "definition": {
                           "id": "CARRY_IN"
                       },
                       "description": "nowy opis usługi dodatkowej"
                   }
               ],
               "type": "MANUAL"    // typ tłumaczenia
           }
       }
   ]
}
```

##### Jak utworzyć lub zmodyfikować tłumaczenie dla danego pakietu i języka

Za pomocą [PATCH /sale/offer-additional-services/groups/{groupId}/translations/{language}](https://developer.allegro.pl/documentation/#operation/updateAdditionalServiceGroupTranslation) utworzysz lub edytujesz tłumaczenie dla danego pakietu usług dodatkowych.

Przykładowy request:

```
curl -X PATCH \
'https://api.allegro.pl/sale/offer-additional-services/groups/fd2b1ee9-3ace-4f9a-b2d8-839980f2a484/translations/en-US' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \ 
 -H 'Content-Type: application/vnd.allegro.public.v1+json' \
-d '{
 "additionalServices": {
   "translation": [
     {
       "definition": {
         "id": "CARRY_IN"
       },
       "description": "New description of the additional service"
     }
   ]
 }
}'
```

Przykładowy response:

```
{
   "language": "en-US",
   "additionalServices": {
       "translation": [
           {
               "definition": {
                   "id": "CARRY_IN"
               },
               "description": "New description of the additional service"
           }
       ],
       "type": "MANUAL"
   }
}
```

##### Jak usunąć tłumaczenie dla danego pakietu i języka

Za pomocą [DELETE /sale/offer-additional-services/groups/{groupId}/translations/{language}](https://developer.allegro.pl/documentation/#operation/deleteAdditionalServiceGroupTranslation) usuniesz tłumaczenie dla danego pakietu i języka.

Przykładowy request:

```
curl -X DELETE \
'https://api.allegro.pl/sale/offer-additional-services/groups/fd2b1ee9-3ace-4f9a-b2d8-839980f2a484/translations/en-US' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \
```

Przykładowy response:

```
Status 204 No Content
```

### Jak zakończyć ofertę

Za pomocą [PUT /sale/offer-publication-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/changePublicationStatusUsingPUT) możesz też zakończyć/wstrzymać wybrane oferty - wystarczy, że w polu action podasz wartość END. W commandId podaj wartość w formacie UUID - wygeneruj go we własnym zakresie.

### Jak wznowić ofertę

Możesz wznowić zakończoną ofertę w formacie BUY_NOW (Kup Teraz) pod tym samym numerem ID. Skorzystaj z [PUT /sale/offer-publication-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/changePublicationStatusUsingPUT) podaj wartość 'ACTIVATE' w polu action i numery ofert, dla których ma być zmieniony status. W commandId podaj wartość w formacie UUID - wygeneruj go we własnym zakresie. Jeśli chcesz zaplanować wznowienie oferty w przyszłości - wystarczy, że w polu scheduleFor ustawisz datę planowanej publikacji oferty. Jeśli wznowisz ofertę zanim minie 30 dni od jej zakończenia, zachowasz popularność proporcjonalnie do czasu wstrzymania oferty. Oznacza to, że jeśli wznowisz ofertę po 20 dniach od jej zakończenia, będzie w niej naliczona popularność z ostatnich 10 dni jej trwania.

Jeśli zakończona oferta ma zerowy stan, to najpierw musisz zmienić liczbę przedmiotów, a dopiero potem ją aktywować.

Przykładowy request

```
  curl -X PUT \
  'https://api.allegro.pl/sale/offer-publication-commands/{commandId}'
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
  -d '{
    "publication": {
        "action": "ACTIVATE",    // wymagane, dostępne są dwie wartości: "ACTIVATE" (aktywowanie danych ofert) i "END" (zakończenie danych ofert)
        "scheduledFor":"2018-03-28T12:00:00.000Z"     // niewymagane, wysyłasz jeśli chcesz zaplanować wystawienie oferty w przyszłości
    },
    "offerCriteria": [
        {
            "offers":    // wymagane, tablica obiektów z numerami identyfikacyjnymi ofert
                {
                    "id": "7276377308"
                }
            ],
            "type": "CONTAINS_OFFERS"    // wymagane, obecnie dostępna jest jedna wartość: CONTAINS_OFFERS (oferty, w których zmienimy status)
        }
    ]
 }'
```

Przykładowy response

```
  {
    "id": "3417d97f-0d32-4747-8a17-1de38f8899de",
    "createdAt": "2019-08-24T14:15:22Z",
    "completedAt": null,
    "taskCount": {
                "total": 0,
                "success": 0,
                "failed": 0
            }
  }
```

### Dodatkowe informacje

#### Limit wystawiania ofert

Możesz wystawić maksymalnie 200 000 ofert na jednym koncie. Limit dotyczy też ofert, w których ustawiłeś datę wystawienia w przyszłości. Jeśli przekroczysz limit i spróbujesz wystawić nową, albo wznowisz zakończoną ofertę - otrzymasz komunikat błędu:

```
  {
    "errors": [
        {
            "code": "PublicationValidationException.MaxActiveOffers",
            "message": "Offer cannot be published - your account has exceeded
            the maximum number 200 000 of active offers",
            "details": null,
            "path": null,
            "userMessage": "Nie można wystawić oferty - Twoje konto przekroczyło
            maksymalną liczbę 200 000 aktywnych ofert"
        }
    ]
  }
```

#### Wielowariantowość

Te same przedmioty w różnych wariantach możesz połączyć ze sobą i stworzyć kompletną ofertę. Skorzystaj z odpowiednich zasobów, które dla ciebie [udostępniliśmy](https://developer.allegro.pl/tutorials/jak-utworzyc-oferte-wielowariantowa-oA6ZYBg5XFo).

#### Klasyfikacja oferty w programie Allegro Smart!

Możesz sprawdzić klasyfikację oferty w programie Allegro Smart! za pomocą jednego z [udostępnionych zasobów](https://developer.allegro.pl/account/#klasyfikacja-oferty).

#### Kalkulator

Możesz obliczyć koszty wystawienia swoich ofert. Wystarczy, że skorzystasz z zasobów, które ci [udostępniliśmy](https://developer.allegro.pl/tutorials/jak-sprawdzic-oplaty-nn9DOL5PASX#kalkulator-oplat).

#### Tabele rozmiarów

Możesz pobrać identyfikatory tabel rozmiarów i ich zawartość za pomocą [udostępnionych zasobów](https://developer.allegro.pl/tutorials/jak-wystawic-oferte-GRaj0q1PMSK#tabele-rozmiarow).

#### Załączniki i tagi

Możesz skorzystać z [zasobów](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#zalaczniki), które przygotowaliśmy do zarządzania załącznikami. Natomiast tagi obsłużysz dedykowanymi [zasobami](https://developer.allegro.pl/documentation/#tag/Offer-tags).

### Najczęstsze błędy

opis błędu / rozwiązanie

Nie odnaleźliśmy produktu dla wskazanego identyfikatora w polu [product.id](http://product.id/). Wyszukaj prawidłowy produkt za pomocą [GET /sale/products](https://developer.allegro.pl/documentation#operation/getSaleProducts) i uwzględnij go w ofercie.

opis błędu / rozwiązanie

Nie udało nam się wyszukać konkretnego produktu i uwzględnić go w ofercie na podstawie wskazanego numeru GTIN oraz parametrów. Uzupełnij brakujące parametry wskazane w "message".

opis błędu / rozwiązanie

Nie udało się utworzyć produktu na podstawie wskazanego numeru GTIN. Usuń pole "product.id" i "product.idType" i spróbuj utworzyć nowy produkt.

opis błędu / rozwiązanie

Nie możesz wystawić oferty produktu wskazanej marki, jest ona przez nas zablokowana. Jeśli chcesz dowiedzieć się więcej szczegółów, skorzystaj z [formularza kontaktowego.](https://allegro.pl/pomoc/kontakt?srsltid=AfmBOorgCsPsNSG7goo1oxsMHAj2VsVHtNNWty5KEGiiARrrlMG8RHfv)

opis błędu / rozwiązanie

Próbujesz odłączyć produkt od oferty - w polu "productSet.product.id" wskazujesz null. Taka operacja nie jest możliwa, produkt musi być uwzględniony w ofercie.

opis błędu / rozwiązanie

Próbujesz edytować ofertę przez konto zwykłe, co nie jest możliwe za pośrednictwem API, lub modyfikujesz ofertę, która nie należy do Ciebie.

opis błędu / rozwiązanie

Posiadasz już 5 ofert danego produktu, nie możesz utworzyć kolejnej lub edytować aktualnej. Więcej informacji na ten temat znajdziesz [w newsie](https://allegro.pl/pomoc/aktualnosci/od-16-pazdziernika-polaczysz-maksymalnie-5-ofert-z-tym-samym-produktem-z-katalogu-eKaE250LPCq#:~:text=2023%2C%2008%3A29-,Od%2016%20pa%C5%BAdziernika%20po%C5%82%C4%85czysz%20maksymalnie%205%20ofert%20z%20tym%20samym,5%20ofert%20ze%20stanem%20Nowy.).

opis błędu / rozwiązanie

Nie możesz mieć więcej niż 30 000 aktywnych ofert B2B. Zakończ istniejącą ofertę dla biznesu przed wystawieniem nowej.

opis błędu / rozwiązanie

Nie możesz wystawiać ofert w tej kategorii. Aby otrzymać więcej szczegółów, skontaktuj się przez [formularz kontaktowy](https://allegro.pl/pomoc/kontakt?srsltid=AfmBOorgCsPsNSG7goo1oxsMHAj2VsVHtNNWty5KEGiiARrrlMG8RHfv).

opis błędu / rozwiązanie

Wysyłasz w zapytaniu nadmiarowe pola, które nie są opisane w dokumentacji. Szczegółowe informacje znajdziesz w polu "metadata". Usuń niepotrzebne pola.

opis błędu / rozwiązanie

Nie odnaleźliśmy oferty wskazanej w żądaniu, najprawdopodobniej została zarchiwizowana. Oferty archiwizujemy 60 dni po zakończeniu.

opis błędu / rozwiązanie

Poprzednia edycja oferty jest nadal przetwarzana, spróbuj powtórzyć request.

opis błędu / rozwiązanie

W przesyłanym żądaniu brakuje wymaganych parametrów. Upewnij się, że w sekcjach product.parameters i parameters przesyłasz wszystkie parametry oznaczone jako required w odpowiedzi [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2).

opis błędu / rozwiązanie

Na podstawie przekazanych danych wykryliśmy istniejący produkt w naszym Katalogu i próbujemy uwzględnić go ofercie. Jest to jednak niemożliwe ze względu na rozbieżność między wartością parametru wskazaną przez sprzedawcę, a wartością w katalogu. W takiej sytuacji możesz poprawić wartość parametru w swoim żądaniu lub - jeśli jesteś pewien, że Twoja wartość jest prawidłowa - zgłosić sugestię zmiany danych w produkcie. ID odnalezionego produktu znajdziesz w polu "metadata".

opis błędu / rozwiązanie

W żądaniu uwzględniono parametr, który nie występuje w danej kategorii, usuń go. Listę dostępnych parametrów pobierzesz za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2).

opis błędu / rozwiązanie

Podano nieistniejący identyfikator wartości słownikowej dla parametru wskazanego w "message". Sprawdź dostępne wartości za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2).

opis błędu / rozwiązanie

Błąd walidacji parametrów zależnych. Wystąpi , gdy np. dla parametru zależnego od innego parametru wybrałeś niedozwoloną wartość, np. dla parametru "Stan" wybrano "Nowy", ale w parametrze "Stan opakowania" wybrano "Brak opakowania". Więcej na temat parametrów zależnych przeczytasz w [naszym artykule](https://developer.allegro.pl/news/wprowadzamy-zmiany-w-obsludze-parametrow-zaleznych-yPOELGb2gTM).

opis błędu / rozwiązanie

W parametrze słownikowym przekazano identyfikator wartości, która nie znajduje się w zbiorze dostępnych wartości. Sprawdź dostępne wartości za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2).

opis błędu / rozwiązanie

W parametrze słownikowym przekazano identyfikator wartości, która nie znajduje się w zbiorze dostępnych wartości. Sprawdź dostępne wartości za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2).

opis błędu / rozwiązanie

W parametrze słownikowym przekazano dwa razy tą samą wartość, usuń jedną z nich.

opis błędu / rozwiązanie

Wartość, którą przesyłasz w danym parametrze nie jest liczbą. Upewnij się, że wysyłasz ją w prawidłowym formacie.

opis błędu / rozwiązanie

Prefiks przekazanego EAN (GTIN) wskazuje, że jest to Numer Ograniczonej Dystrybucji - RCN i nie może być wykorzystany na Allegro. Skontaktuj się z dystrybutorem, wydawcą lub producentem i uzyskaj poprawny numer EAN (GTIN). Więcej na ten temat przeczytasz w artykule [dla sprzedających](https://help.allegro.com/sell/pl/a/parametry-w-allegro-aMZKj37Vauq?marketplaceId=allegro-pl#czym-jest-ean-gtin).

opis błędu / rozwiązanie

W parametrze GTIN użyto nieprawidłowego prefiksu. GS1 nie nadaje numerów EAN (GTIN), które zaczynają się od wskazanej wartości. Skontaktuj się z dystrybutorem, wydawcą lub producentem i uzyskaj poprawny numer EAN (GTIN). Więcej szczegółów znajdziesz [na stronie dla sprzedających](https://help.allegro.com/sell/pl/a/parametry-w-allegro-aMZKj37Vauq?marketplaceId=allegro-pl#czym-jest-ean-gtin).

opis błędu / rozwiązanie

W parametrze GTIN przekazano nieprawidłową wartość. Upewnij się, że jest ona zgodna z wymogami, które opisaliśmy na [stronie dla sprzedających](https://help.allegro.com/sell/pl/a/parametry-w-allegro-aMZKj37Vauq?marketplaceId=allegro-pl#czym-jest-ean-gtin).

opis błędu / rozwiązanie

W parametrze GTIN przekazano niedopuszalny znak. Upewnij się, że wartość jest zgodna z wymogami, które opisaliśmy na stronie [dla sprzedających](https://help.allegro.com/sell/pl/a/parametry-w-allegro-aMZKj37Vauq?marketplaceId=allegro-pl#czym-jest-ean-gtin).

opis błędu / rozwiązanie

Przekazano zbyt długą wartość parametru GTIN. Dopuszczalna długość to 8, 10, 12, 13 lub 14 znaków.

opis błędu / rozwiązanie

Podany identyfikator wartości słownikowej w polu "valuesIds" nie jest spójny z wartością w "values". Upewnij się za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2), jakie są prawidłowe wartości dla danego parametru.

opis błędu / rozwiązanie

W strukturze wskazano ID parametru słownikowego, jednak nie przekazano dla niego żadnej wartości - uzupełnij ją w polu "valuesIds" lub "values". Przykłady znajdziesz w [naszym poradniku.](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#parametry-ofertowe)

opis błędu / rozwiązanie

W strukturze wskazano ID parametru słownikowego, jednak nie przekazano dla niego żadnej wartości lub wskazano ja błędnie - uzupełnij ją w polu "valuesIds" lub "values". Przykłady znajdziesz w [naszym poradniku](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#parametry-ofertowe).

opis błędu / rozwiązanie

Przekazano nieistniejącą wartość słownikową dla parametru wskazanego w "message". Sprawdź dostępne wartości za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2).

opis błędu / rozwiązanie

Przekazano zbyt wysoką wartość w parametrze zakresowym, w polu "rangeValue.to". Zakres wartości, jaki możesz wprowadzisz, sprawdzisz za pomocą [GET /sale/categories/{categoryID}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2), w polu "restrictions".

opis błędu / rozwiązanie

Przekazano zbyt długo wartość w parametrze typu string, w polu "values". Maksymalne długości, jakie możesz wprowadzisz, sprawdzisz za pomocą [GET /sale/categories/{categoryID}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2), w polu "restrictions".

opis błędu / rozwiązanie

Przekazano niedozwolony znak w parametrze typu string, np. niedozwolony znak unicode.

opis błędu / rozwiązanie

Parametr opisujący produkt przekazujesz w sekcji ofertowej ("parameters") zamiast w produktowej ("productSet.product.parameters") lub odwrotnie. Za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2) i pola "options.describesProducts" sprawdź, czy parameter jest produktowy (true ) lub ofertowy (false).

opis błędu / rozwiązanie

Jeden z parametrów przekazałeś więcej niż raz, usuń nadmiarowy parametr.

opis błędu / rozwiązanie

Dla parametru zakresowego nie podano dwóch wymaganych wartości. Zapoznaj się z przykładową strukturą [w naszym poradniku](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#parametry-ofertowe).

opis błędu / rozwiązanie

W parametrze zakresowym, w polu "rangeValue", przekazano wartość, która nie jest liczbą.

opis błędu / rozwiązanie

Błędnie przekazano wartość dla parametru zakresowego. Nie podano dolnej lub górnej granicy. Przykłady prawidłowo uzupełnionej sekcji znajdziesz w naszym poradniku.

opis błędu / rozwiązanie

W parametrze z wartością liczbową przekazano wartość, która nie jest całkowita.

opis błędu / rozwiązanie

Przekazano [własną wartość](https://developer.allegro.pl/news/sprawdz-czy-dla-parametru-z-wartoscia-niejednoznaczna-mozesz-dodac-wlasna-wartosc-ZM9L1KoYmFe) w polu "values" (taką, która nie istnieje w zbiorze dostępnych wartości), mimo że dany parametr nie umożliwia takiej możliwości. Wybierz jedną z dostępnych wartości.

opis błędu / rozwiązanie

Na podstawie przekazanych danych wykryliśmy istniejący produkt w naszym Katalogu i próbujemy uwzględnić go ofercie. Jest to jednak niemożliwe ze względu na rozbieżność między kategorią wskazaną przez sprzedawcę, a kategorią w katalogu. W takiej sytuacji możesz poprawić kategorię w swoim żądaniu lub - jeśli jesteś pewien, że Twoja wartość jest prawidłowa - zgłosić sugestię zmiany danych w produkcie.

opis błędu / rozwiązanie

Kategoria, w której próbujesz utworzyć produkt, nie istnieje. Zaktulizuj drzewo kategorii po swojej stronie za pomocą [GET /sale/categories](https://developer.allegro.pl/documentation#operation/getCategoriesUsingGET).

opis błędu / rozwiązanie

Na podstawie przekazanych danych wykryliśmy istniejący produkt w naszym Katalogu i próbujemy uwzględnić go ofercie. Jest to jednak niemożliwe ze względu na rozbieżność między danymi wskazanymi przez sprzedawcę, a danymi w katalogu. W takiej sytuacji możesz poprawić dane w swoim żądaniu lub - jeśli jesteś pewien, że Twoje wartości są prawidłowe - zgłosić sugestię zmiany danych w produkcie.

opis błędu / rozwiązanie

Przekazano błędny numer [GTIN](https://help.allegro.com/sell/pl/a/parametry-w-allegro-aMZKj37Vauq?marketplaceId=allegro-pl#czym-jest-ean-gtin). Wskaż prawidłowy numer, który istnieje w bazie GS1.

opis błędu / rozwiązanie

Aktualnie nie posiadamy produktu w wersji językowej wskazanej w polu "language" w ofercie.

opis błędu / rozwiązanie

Wskazany produkt posiada specyfikacje techniczną TecDoc, przypisz ją do oferty. Możesz to zrobić za pomocą [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation#operation/editProductOffers), przekazując w body requesty pole productSet.product.id wraz z identyfikatorem produktu. Automatycznie uwzględnimy dane z produktu w ofercie.

opis błędu / rozwiązanie

Wskazana sekcja "Pasuje do" jest nieprawidłowa dla danego produktu, użyj produktowej sekcji "Pasuje do". Zaktualizuj dane produktowe w ofercie. Możesz to zrobić za pomocą [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation#operation/editProductOffers), przekazując w body requestu pole productSet.product.id wraz z identyfikatorem produktu. Automatycznie uwzględnimy dane z produktu w ofercie.

opis błędu / rozwiązanie

Próbujesz w ofercie użyć [produktu tymczasowego](https://developer.allegro.pl/news/w-wybranych-kategoriach-bedziemy-tworzyc-produkty-tymczasowe-nn9Y12dbqHM), który jest przypisany do innej oferty. Skorzystaj z innego produktu z katalogu lub utwórz nowy.

opis błędu / rozwiązanie

Przekroczono maksymalny dopuszczalny rozmiar tytułu oferty (75 znaków, przy założeniu, że niektóre litery i symbole liczone są jako więcej niż 1 znak).

opis błędu / rozwiązanie

Przekroczono maksymalny dopuszczalny rozmiar pojedynczego słowa w tytule oferty (30 znaków)

opis błędu / rozwiązanie

W tytule produktu lub oferty przekazujesz niedozwolony znak, usuń go.

opis błędu / rozwiązanie

Zmiana została przez nas zablokowana, ponieważ, np. wysłano w identycznym momencie taką samą operację albo próbujesz wystawić produkt chronionej marki - więcej na ten temat przeczytasz w artykule [dla sprzedających](https://help.allegro.com/sell/pl/a/czym-sa-warunki-ochrony-marek-i-dlaczego-warto-je-znac-LR0OEab6vU9).

opis błędu / rozwiązanie

Błąd powiązany z naruszeniem zasad np. dla tytułu lub treści zawartych w opisie. Zwróć uwagę na dokładną treść zwróconą w "messages".

opis błędu / rozwiązanie

Nie znaleźliśmy warunków zwrotów, które moglibyśmy automatycznie dodać do oferty lub wskazujesz nam ID lub nazwę warunków, które nie istnieją. [Dodaj warunki zwrotów](https://salescenter.allegro.com/returns-terms?) o nazwie "default" lub [rozszerz swój request](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#jak-ustawic-wybrane-warunki-zwrotow) o pole returnPolicy.id lub returnPolicy.name i wskaż ID lub nazwę warunków zwrotów. Więcej szczegółów znajdziesz [w tym fragmencie poradnika](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#warunki-reklamacji-i-zwrotow).

opis błędu / rozwiązanie

Nie znaleźliśmy warunków reklamacji, które moglibyśmy automatycznie dodać do oferty lub wskazujesz nam ID lub nazwę warunków, które nie istnieją. Dodaj warunki reklamacji o nazwie "default" lub rozszerz swój request o pole impliedWarranty.id lub impliedWarranty.name i wskaż ID lub nazwę warunków reklamacji. Więcej szczegółów znajdziesz [w tym fragmencie poradnika](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#warunki-reklamacji-i-zwrotow).

opis błędu / rozwiązanie

W polu "afterSalesServices" próbujesz użyć warunków (np. reklamacji lub zwrotów) innego sprzedawcy. Dostępne warunki reklamacji pobierzesz za pomocą [GET /after-sales-service-conditions/implied-warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET), a zwrotów - przez [GET /after-sales-service-conditions/return-policies](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET).

opis błędu / rozwiązanie

Nie znaleźliśmy warunków (zwrotów i reklamacji), które moglibyśmy automatycznie dodać do oferty. Dodaj warunki o nazwie "default" lub rozszerz swój request o pola returnPolicy.id /returnPolicy.name oraz impliedWarranty.id / impliedWarranty.name . Więcej szczegółów znajdziesz w tym [fragmencie poradnika.](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#warunki-reklamacji-i-zwrotow)

opis błędu / rozwiązanie

Nie znaleźliśmy cennika dostaw, który moglibyśmy automatycznie dodać do oferty lub wskazujesz nam ID lub nazwę cennika, który nie istnieje. Dodaj cennik dostawy o nazwie "default" lub rozszerz swój request o pole deivery.shippingRates.id.id lub "delivery.shippingRates.name" i wskaż ID lub nazwę cennika dostawy. Więcej szczegółów znajdziesz [w tym fragmencie poradnika](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#lokalizacja-i-cenniki).

opis błędu / rozwiązanie

W polu "delivery.shippingRates" przekazano id lub nazwę cennika dostawy, który nalezy do innego sprzedawcy. Dostępne cenniki dostawy pobierzesz za pomocą [GET /sale/shipping-rates](https://developer.allegro.pl/documentation#operation/getListOfShippingRatestUsingGET).

opis błędu / rozwiązanie

Nie możesz w tym przypadku wybrać ogólnej, niejednoznacznej kategorii, takiej jak np. "Inne". Wybierz inną, bardziej specyficzną kategorię.

opis błędu / rozwiązanie

Nie udało się pobrać zdjęć z danych oferty. Upewnij się, że linki przekazane w sekcji "images" są poprawne i spróbuj ponownie.

opis błędu / rozwiązanie

Przekroczono limit zdjęć w galerii, maksymalnie w ofercie możesz uwzględnić 16 zdjęć (wliczajć w to zdjęcia z produktu). Więcej o zasadach dla zdjęc przeczytasz [w naszym poradniku](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#wlasne-zdjecia-i-opis-oferty).

opis błędu / rozwiązanie

Produkt nie posiada zdjęć, musisz uwzględnić przynajmniej jedno.

opis błędu / rozwiązanie

Wystąpił problem z pobraniem zdjęć - adres URL lub format pliku jest nieprawidłowy.

opis błędu / rozwiązanie

Upłynął limit czasu na pobranie obrazka.

opis błędu / rozwiązanie

Wystąpił problem z pobraniem obrazka z serwera. Spróbuj powtórzyć request. Jeśli problem nadal będzie występować, załóż wątek na naszym [forum](https://github.com/allegro/allegro-api) w celu weryfikacji problemu.

opis błędu / rozwiązanie

Wystąpił problem z pobraniem obrazka z serwera. Spróbuj powtórzyć request. Jeśli problem nadal będzie występować, załóż wątek na naszym [forum](https://github.com/allegro/allegro-api) w celu weryfikacji problemu.

opis błędu / rozwiązanie

Wystąpił problem z pobraniem obrazka z serwera. Spróbuj powtórzyć request. Jeśli problem nadal będzie występować, załóż wątek na naszym [forum](https://github.com/allegro/allegro-api) w celu weryfikacji problemu.

opis błędu / rozwiązanie

Obrazek z żądania nie istnieje pod wskazaną ścieżką. Upewnij się, że adres jest prawidłowy.

opis błędu / rozwiązanie

Obrazek z żądania nie istnieje pod wskazaną ścieżką. Upewnij się, że adres jest prawidłowy.

opis błędu / rozwiązanie

Ustawienia dla stawki VAT, które wprowadzono w polu "taxSettings", nie są wspierane w danej kategorii. Dostępne opcje pobierzesz za pomocą [GET /sale/tax-settings](https://developer.allegro.pl/documentation#tag/Tax-settings).

opis błędu / rozwiązanie

Podaj poprawną cenę w polu "sellingMode.price.amount". Upewnij się, że cena jest liczbą z zakresu od 1 do 1000000000. Zalecany format ceny: 0.00.

opis błędu / rozwiązanie

W ofercie brakuje ceny, uzupełnij ją w polu "sellingMode.price".

opis błędu / rozwiązanie

Błąd walidacji danych w ofercie, najczęściej dotyczy braku lub błędnej ceny w ofercie. Upewnij się, że tę wartość przesyłasz poprawnie.

opis błędu / rozwiązanie

Próbujesz zmienić w ofercie liczbę sztuk na mniejszą niż jeden. Ustaw odpowiednią wartość w polu "stock.available".

opis błędu / rozwiązanie

Przekazano ujemną liczby sztuk. Musi ona być równa 0 lub większa - popraw wartość w polu "stock.available".

| error code | opis błędu / rozwiązanie |
| --- | --- |
| "ProductNotFoundException" |
| "DuplicateDetectionMissingParametersException" |
| "MatchingProductForDataNotFoundException" |
| "brandBlock" |
| "RemoveProductException" |
| "OfferAccessDeniedException" |
| "offerCounter" |
| "B2B_OFFER_LIMIT_EXCEEDED" |
| "ConstraintViolationException.CategorySellingRestrictions" |
| "UnknownJSONProperty" |
| "OfferNotFoundException" |
| "OfferConflictException" |
| "MissingRequiredParameters" |
| "PARAMETER_MISMATCH" |
| "ParameterIdNotFoundException" |
| "DictionaryParameterIdNotFound" |
| "ConstraintViolationException.DependencyValidator" |
| "InvalidDictionaryParameterValueId" |
| "NonExistingValueInDictionaryParameter" |
| "DuplicatedValuesInDictionaryParameter" |
| "NonNumericValueInNumberParameter" |
| "InvalidPrefixRestrictedCirculationNumbersInGtinParameter" |
| "ConstraintViolationException.PrefixNotExistsInGtinParameter" |
| "ConstraintViolationException.WrongChecksumInGtinParameter" |
| "ConstraintViolationException.InvalidCharacterInGtinParameter" |
| "NotStandardLengthInGtinParameter" |
| "InvalidDictionaryParameter" |
| "ConstraintViolationException.NoValueInDictionaryParameter" |
| "ImproperlyAssignedDictionaryParameter" |
| "DictionaryParameterValueNotFound" |
| "TooHighRangeToValueInRangeParameter" |
| "ConstraintViolationException.TooLongValueInStringParameter" |
| "IllegalCharactersInStringParameter" |
| "ParameterCategoryException" |
| "ConstraintViolationException.NoDuplicateIds" |
| "ConstraintViolationException.NoValuesInRangeParameter" |
| "ConstraintViolationException.NonNumericValueInRangeParameter" |
| "ConstraintViolationException.AtLeastOneBoundry" |
| "ConstraintViolationException.InvalidValueTypeInNumberParameter" |
| "OfferCustomParametersException" |
| "CATEGORY_MISMATCH" |
| "CATEGORY_NOT_EXISTS" |
| "ProductConstraintViolationException.DataIntegrity" |
| "ConstraintViolationException.GtinNotExistsInGtinParameter" |
| "ProductLanguageVersionUnavailableException" |
| "ConstraintViolationException.ValidTecdocSpecification" |
| "ConstraintViolationException.ValidCompatibilityTable" |
| "ConstraintViolationException.ValidTemporaryProduct" |
| "ConstraintViolationException.StringLength" |
| "ConstraintViolationException.MaxWordLength" |
| "ConstraintViolationException.CharacterNotAllowed" |
| "OFFER_SERVICE_ERROR" |
| "ConstraintViolationException.OfferValidation" |
| "ReturnPolicyNotFoundException" |
| "ImpliedWarrantyNotFoundException" |
| "AfterSalesServiceConditionsOwnedBySeller" |
| "AfterSalesServiceConditionsRequiredByCompany" |
| "ShippingRatesNotFoundException" |
| "SHIPPING_RATES_ACCESS_DENIED" |
| "IllegalOfferUpdateException.IllegalChangeCategoryId" |
| "OfferImagesNotAvailableException" |
| "GallerySizeException" |
| "ConstraintViolationException.GallerySize" |
| "DownloadError.BadRequest" |
| "UploadImageRequestTimeoutException" |
| "DownloadError.InternalServerError" |
| "DownloadError.TooManyRequests" |
| "DownloadError.BadGateway" |
| "DownloadError.NotFound" |
| "OfferImagesNotFoundException" |
| "SETTING_NOT_SUPPORTED_IN_CATEGORY" |
| "ConstraintViolationException.Price" |
| "IllegalOfferUpdateException.PriceMustBeSet" |
| "VALIDATION_FAILED" |
| "AvailableStockMustEqualToOneOrBeGreaterThanOne" |
| "AvailableStockMustEqualToZeroOrBeGreaterThanZero" |

### FAQ

Przy próbie aktywacji / wznowienia oferty otrzymuję błąd “You cannot schedule activating an offer in the past”. Co on oznacza?

W polu scheduledFor przekazujesz datę z przeszłości. Aby wyeliminować ten błąd, podaj datę z przyszłości lub pozostaw to pole puste. Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/GRaj0q1PMSK#publikacja-oferty).

Ile ofert maksymalnie mogę aktywować lub zakończyć za pomocą PUT /sale/offer-publication-commands/{commandId}?

Maksymalnie możesz aktywować lub zakończyć 1000 ofert.

Gdy pobieram ofertę, otrzymuję błąd 404 Not Found. Co on oznacza?

Oferta, którą próbujesz pobrać została:

- nigdy nie istniała. W takim przypadku musisz utworzyć nową ofertę.
- usunięta - jeśli szkic oferty nie był edytowany lub oferta nie była aktywowana w ciągu 60 dni,
- zarchiwizowana - oferty przenosimy do archiwum po 60 dniach od zakończenia,

Gdy pobieram ofertę, otrzymuję błąd 403 Forbidden. Co on oznacza?

Upewnij się, że jesteś zautoryzowany jako sprzedawca, do którego należy dana oferta. Możesz pobierać tylko swoje oferty. Rozkoduj swój token za pomocą jednego z darmowych narzędzi i zweryfikuj wartość w polu user_name.

Gdy próbuję zmienić dane w ofetach, np. cenę za pomocą PUT /sale/offer-price-change-commands/{commandId}, w odpowiedzi otrzymuję same zera. Czy to prawidłowe zachowanie?

Tak, wszystkie [zasoby do edycji wielu ofert jednocześnie](https://developer.allegro.pl/tutorials/7GzB2L37ase#edycja-wielu-ofert-jednoczesnie) działają asynchronicznie, dlatego aby sprawdzić szczegóły status operacji, użyj [GET /sale/offer-price-change-commands/{commandId}/tasks](https://developer.allegro.pl/documentation#operation/getPriceModificationCommandTasksStatusesUsingGET).

Czy w zasobach /sale/product-offers mogę pobierać szczegóły ofert z konta powiązanego?

Tak, możesz pobierać szczegóły ofert z konta powiązanego - wystarczy, że w nagłówku x-representative-of przekażesz identyfikator konta powiązanego.

Gdy próbuję aktywować oferty za pomocą PUT /sale/offer-publication-commands/{commandId}, w odpowiedzi otrzymuję same zera. Czy to prawidłowe zachowanie?

Tak, dzieje się tak ponieważ ten zasób działa asynchronicznie. Aby sprawdzić szczegółowy status realizacji zadania, użyj [GET /sale/offer-publication-commands/{commandId}/tasks](https://developer.allegro.pl/documentation#operation/getPublicationTasksUsingGET).

Czy, aby wprowadzić zmiany w ofercie muszę za każdym razem ją pobierać i wysyłać wszystkie dane, mimo że chcę zmienić tylko jedno pole?

Nie, w takim przypadku skorzystaj z [PATCH /sale/product-offers](https://developer.allegro.pl/documentation/#operation/editProductOffers) i w strukturze requestu przekaż tylko to pole, które chcesz zmodyfikować. Więcej na temat tego procesu znajdziesz w [naszym poradniku](https://developer.allegro.pl/tutorials/jak-zarzadzac-ofertami-7GzB2L37ase#edycja-pojedynczej-oferty).

Gdy próbuję aktywować oferty za pomocą [PUT /sale/offer-publication-commands/{commandId}](/documentation/#operation/changePublicationStatusUsingPUT), w odpowiedzi otrzymuję same zera. Czy to prawidłowe zachowanie?

Tak, dzieje się tak ponieważ ten zasób działa asynchronicznie. Aby sprawdzić szczegółowy status realizacji zadania, użyj [GET /sale/offer-publication-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getPublicationTasksUsingGET).

### Lista zasobów

Pełną dokumentację zasobów w postaci pliku swagger.yaml znajdziesz [tu](https://developer.allegro.pl/swagger.yaml).

Lista zasobów podstawowych opisanych w poradniku:

- [PUT /sale/offer-publication-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/changePublicationStatusUsingPUT)- zakończ lub wznów ofertę
- [PUT /sale/offer-modification-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/modificationCommandUsingPUT)- zmień grupowo np. cenniki dostaw
- [PUT /sale/offer-quantity-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/quantityModificationCommandUsingPUT)- zmień grupowo liczbę przedmiotów w ofertach
- [PUT /sale/offer-price-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/priceModificationCommandUsingPUT)- zmień grupowo cenę w ofertach
- [PATCH sale/product-offers/{offerId}](https://developer.allegro.pl/documentation#tag/Offer-management/operation/editProductOffers)- edytuj dane pole w ofercie
- [GET sale/product-offers/{offerId}](https://developer.allegro.pl/documentation#tag/User's-offer-information/operation/getProductOffer)- pobierz szczegółowe dane oferty
- [GET /sale/offers](https://developer.allegro.pl/documentation/#operation/searchOffersUsingGET)- pobierz listę ofert
- [GET /sale/offer-events](https://developer.allegro.pl/documentation/#operation/getOfferEvents)- pobierz dziennik zdarzeń w ofertach

Lista zasobów wspierających opisanych w poradniku:

- [DELETE /sale/offer-additional-services/groups/{groupId}/translations/{language}](https://developer.allegro.pl/documentation/#operation/deleteAdditionalServiceGroupTranslation)- usuń tłumaczenie dla danego pakietu i języka
- [PATCH /sale/offer-additional-services/groups/{groupId}/translations/{language}](https://developer.allegro.pl/documentation/#operation/updateAdditionalServiceGroupTranslation)- utwórz lub edytuj tłumaczenie dla danego pakietu usług dodatkowych
- [GET /sale/offer-additional-services/groups/{groupId}/translations](https://developer.allegro.pl/documentation/#operation/getAdditionalServiceGroupTranslations)- pobierz tłumaczenie dla danego pakietu usług dodatkowych
- [DELETE /sale/offers/{offerId}/translations/{language}](https://developer.allegro.pl/documentation/#operation/deleteManualTranslationUsingDELETE)- usuń wybrane własne tłumaczenie oferty
- [PATCH /sale/offers/{offerId}/translations/{language}](https://developer.allegro.pl/documentation/#operation/updateOfferTranslationUsingPATCH)- dodaj lub zaktualizuj tłumaczenie oferty
- [GET /sale/offers/{offerId}/translations](https://developer.allegro.pl/documentation/#operation/getOfferTranslationUsingGET)- pobierz listę dostępnych tłumaczeń dla wskazanej oferty
- [GET /sale/offers/promo-options-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getPromoModificationCommandDetailedResultUsingGET)- pobierz szczegółowy raport edycji opcji promowania na wielu ofertach
- [GET /sale/offers/promo-options-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getPromoModificationCommandResultUsingGET)- pobierz raport edycji opcji promowania na wielu ofertach
- [PUT /sale/offers/promo-options-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/promoModificationCommandUsingPUT)- dodaj lub zmień opcje promowania na wielu ofertach
- [GET /sale/offers/{offerId}/promo-options](https://developer.allegro.pl/documentation/#operation/getOfferPromoOptionsUsingGET)- pobierz opcje promowania przypisane do oferty
- [POST /sale/offers/{offerId}/promo-options-modification](https://developer.allegro.pl/documentation/#operation/modifyOfferPromoOptionsUsingPOST)- dodaj, edytuj lub wyłącz opcje promowania na wskazanej ofercie
- [GET /sale/offers/promo-options](https://developer.allegro.pl/documentation/#operation/getPromoOptionsForSellerOffersUsingGET)- pobierz opcje promowania dla wszystkich ofert
- [GET /sale/offer-promotion-packages](https://developer.allegro.pl/documentation/#operation/getAvailableOfferPromotionPackages)- pobierz listę dostępnych opcji promowania
- [GET /sale/offer-additional-services/groups/{groupId}](https://developer.allegro.pl/documentation/#operation/getAdditionalServicesGroupUsingGET)- pobierz wybraną grupę usług dodatkowych
- [GET /sale/offer-additional-services/groups](https://developer.allegro.pl/documentation/#operation/getListOfAdditionalServicesGroupsUsingGET)- pobierz listę grup z usługami dodatkowymi
- [PUT /sale/offer-additional-services/groups/{groupId}](https://developer.allegro.pl/documentation/#operation/modifyAdditionalServicesGroupUsingPUT)- edytuj wybraną grupę usług dodatkowych
- [POST /sale/offer-additional-services/groups](https://developer.allegro.pl/documentation/#operation/createAdditionalServicesGroupUsingPOST)- utwórz nową grupę usług dodatkowych
- [GET /sale/offer-additional-services/categories](https://developer.allegro.pl/documentation/#operation/getListOfAdditionalServicesDefinitionsCategoriesUsingGET)- pobierz listę usług dodatkowych
- [PUT /after-sales-service-conditions/attachments/{attachmentId}](https://developer.allegro.pl/documentation/#operation/uploadAfterSalesServiceConditionsAttachmentUsingPUT)- prześlij załącznik dla gwarancji
- [POST /after-sales-service-conditions/attachments](https://developer.allegro.pl/documentation/#operation/createAfterSalesServiceConditionsAttachmentUsingPOST)- utwórz obiekt załącznika dla gwarancji
- [PUT /after-sales-service-conditions/warranties/{warrantyId}](https://developer.allegro.pl/documentation/#operation/updateAfterSalesServiceWarrantyUsingPUT)- edytuj informacje o gwarancji
- [GET /after-sales-service-conditions/warranties/{warrantyId}](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceWarrantyUsingGET)- pobierz szczegółowe informacje o gwarancji
- [GET /after-sales-service-conditions/warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET_2)- pobierz informacje o gwarancjach przypisanych do konta
- [POST /after-sales-service-conditions/warranties](https://developer.allegro.pl/documentation/#operation/createAfterSalesServiceWarrantyUsingPOST)- dodaj nowe informacje o gwarancji
- [PUT /after-sales-service-conditions/implied-warranties/{impliedWarrantyId}](https://developer.allegro.pl/documentation/#operation/updateAfterSalesServiceImpliedWarrantyUsingPUT)- edytuj warunki reklamacji
- [GET /after-sales-service-conditions/implied-warranties/{impliedWarrantyId}](https://developer.allegro.pl/#operation/getAfterSalesServiceImpliedWarrantyUsingGET)- pobierz szczegóły warunków reklamacji
- [GET /after-sales-service-conditions/implied-warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET)- pobierz warunki reklamacji przypisane do konta
- [POST /after-sales-service-conditions/implied-warranties](https://developer.allegro.pl/documentation/#operation/createAfterSalesServiceImpliedWarrantyUsingPOST)- dodaj nowe warunki reklamacji
- [DELETE /after-sales-service-conditions/return-policies/{returnPolicyId}](https://developer.allegro.pl/documentation#operation/deleteAfterSalesServiceReturnPolicyUsingDELETE)- usuń wskazane warunki zwrotów
- [PUT /after-sales-service-conditions/return-policies/{returnPolicyId}](https://developer.allegro.pl/documentation/#operation/updateAfterSalesServiceReturnPolicyUsingPUT)- edytuj wskazane warunki zwrotów
- [GET /after-sales-service-conditions/return-policies/{returnPolicyId}](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceReturnPolicyUsingGET)- pobierz szczegóły warunków zwrotów
- [GET /after-sales-service-conditions/return-policies](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET_1)- pobierz warunki zwrotów przypisane do konta
- [POST /after-sales-service-conditions/return-policies](https://developer.allegro.pl/documentation/#operation/createAfterSalesServiceReturnPolicyUsingPOST)- dodaj nowe warunki zwrotów
- [GET /sale/category-parameters-scheduled-changes](https://developer.allegro.pl/documentation/#operation/getCategoryParametersScheduledChangesUsingGET_1)- sprawdź zaplanowane zmiany w parametrach
- [GET /sale/offers/unfilled-parameters](https://developer.allegro.pl/documentation/#operation/getOffersUnfilledParametersUsingGET_1)- sprawdź nieuzupełnione parametry w ofertach
- [GET /sale/category-events](https://developer.allegro.pl/documentation/#operation/getCategoryEventsUsingGET_1)- pobierz zmiany w kategoriach z ostatnich 3 miesięcy
- [GET /sale/price-automation/offers/{offerId}/rules](https://developer.allegro.pl/documentation#operation/getPriceAutomationRulesForOfferUsingGET)- pobierz informacje o regule cenowej przypisanej do oferty
- [GET /sale/offer-price-automation-commands/{commandId}/tasks](https://developer.allegro.pl/documentation#operation/getofferPriceAutomationModificationCommandTasksStatusesUsingGET)- pobierz szczegółowy raport przypisania reguły cenowej do ofert
- [GET /sale/offer-price-automation-commands/{commandId}](https://developer.allegro.pl/documentation#operation/getofferPriceAutomationModificationCommandStatusUsingGET)- pobierz raport przypisania reguły cenowej do ofert
- [POST /sale/offer-price-automation-commands](https://developer.allegro.pl/documentation#operation/offerAutomaticPricingModificationCommandUsingPOST)- przypisz regułę cenową do ofert
- [DELETE /sale/price-automation/{ruleId}](https://developer.allegro.pl/documentation#operation/deleteAutomaticPricingRuleUsingDelete)- usuń daną regułę cenową
- [PUT /sale/price-automation/{ruleId}](https://developer.allegro.pl/documentation#operation/updateAutomaticPricingRuleUsingPut)- edytuj daną regułę cenową
- [GET /sale/price-automation/rules](https://developer.allegro.pl/documentation#operation/getAutomaticPricingRulesUsingGET)- pobierz dostępne reguły cenowe
- [POST /sale/price-automation/rules](https://developer.allegro.pl/documentation#operation/createAutomaticPricingRulesUsingPost)- utwórz nową regułę cenową
- [GET /sale/offer-modification-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getTasksUsingGET)- pobierz szczegółowy raport z grupowej edycji ofert
- [GET /sale/offer-modification-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getGeneralReportUsingGET)- pobierz raport z grupowej edycji oferty
- [GET /sale/offer-quantity-change-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getQuantityModificationCommandTasksStatusesUsingGET)- pobierz szczegółowy raport z grupowej zmiany liczby przedmiotów
- [GET /sale/offer-quantity-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getQuantityModificationCommandStatusUsingGET)- pobierz raport z grupowej zmiany liczby przedmiotów
- [GET /sale/offer-price-change-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getPriceModificationCommandTasksStatusesUsingGET)- pobierz szczegółowy raport z grupowej zmiany ceny
- [GET /sale/offer-price-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/getPriceModificationCommandStatusUsingGET)- pobierz raport z grupowej zmiany ceny

### Limity

Limit

150 tys. ofert na godzinę i 9 tys. na minutę

Limit

250 tys. ofert na godzinę i 9 tys. na minutę

Limit

250 tys. ofert na godzinę i 9 tys. na minutę

Limit

250 tys. ofert na godzinę i 9 tys. na minutę

| Zasób | Limit |
| --- | --- |
| [PUT /sale/offer-price-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/priceModificationCommandUsingPUT) |
| [PUT /sale/offer-quantity-change-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/quantityModificationCommandUsingPUT) |
| [PUT /sale/offer-modification-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/modificationCommandUsingPUT) |
| [PUT /sale/offer-publication-commands/{commandId}](https://developer.allegro.pl/documentation/#operation/changePublicationStatusUsingPUT) |

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