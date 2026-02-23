Wystawianie oferty produktu - Allegro Developer Portal - baza wiedzy o Allegro REST API

Ogólna struktura i założenia

Jak utworzyć ofertę powiązaną z produktem

Jak przekazać własne wartości w żądaniu

Jak utworzyć zestaw produktowy

Katalog Produktów

Obsługa błędów

FAQ

Lista zasobów

# Wystawianie oferty produktu

Opis procesów, dzięki którym dowiesz się, jak zarządzać ofertą i produktem, m.in. jak wystawić ofertę powiązaną z produktem, jak utworzyć produkt, który nie istnieje w naszej bazie, jak utworzyć zestaw produktowy.

##### Czego się dowiesz?

- Jak odszukać produkt w Katalogu Produktów.
- Na co zwrócić uwagę podczas wystawiania oferty oraz jakie dane możesz uzupełnić oraz nadpisać.
- Jak wystawić ofertę produktu, którego nie ma w Katalogu Produktów.
- Jak wystawić ofertę produktu na podstawie danych z Katalogu Produktów.
- Jak definiujemy produkt oraz ofertę produktu.

---

### Ogólna struktura i założenia

```
{
  "productSet": [
    {
      "product": {
        "name": "iPhone 5s",
        "category": {
          "id": "257931"
        },
        "id": "5902719471797",
        "idType": "GTIN",
        "parameters": [
          {
            "id": "string",
            "name": "string",
            "rangeValue": {
              "from": "string",
              "to": "string"
            },
            "values": [
              "string"
            ],
            "valuesIds": [
              "string"
            ]
          }
        ],
        "images": [
          "string"
        ]
      },
      "quantity": {
        "value": 1
      },
      "responsiblePerson": {
        "id": "string",
        "name": "string"
      }
    }
  ],
  "b2b": {
    "buyableOnlyByBusiness": false
  },
  "attachments": [
    {
      "id": "string"
    }
  ],
  "fundraisingCampaign": {
    "id": "string",
    "name": "string"
  },
  "additionalServices": {
    "id": "string",
    "name": "string"
  },
  "stock": {
    "available": 99,
    "unit": "UNIT"
  },
  "delivery": {
    "handlingTime": "PT24H",
    "shippingRates": null,
    "additionalInfo": "string",
    "shipmentDate": "2019-08-24T14:15:22Z"
  },
  "publication": {
    "duration": "PT24H",
    "endingAt": "2031-01-04T11:01:59Z",
    "startingAt": "2031-01-04T11:01:59Z",
    "status": "INACTIVE",
    "endedBy": "USER",
    "republish": false,
    "marketplaces": {}
  },
  "additionalMarketplaces": {
    "allegro-cz": {
      "sellingMode": {
        "price": {
          "amount": "233.01",
          "currency": "CZK"
        }
      }
    }
  },
  "compatibilityList": {
    "items": [
      {
        "type": "TEXT",
        "text": "CITROËN C6 (TD_) 2005/09-2011/12 2.7 HDi 204KM/150kW"
      }
    ]
  },
  "language": "pl-PL",
  "category": {
    "id": "257931"
  },
  "parameters": [
    {
      "id": "string",
      "name": "string",
      "rangeValue": {
        "from": "string",
        "to": "string"
      },
      "values": [
        "string"
      ],
      "valuesIds": [
        "string"
      ]
    }
  ],
  "afterSalesServices": {
    "impliedWarranty": {
      "id": "09f0b4cc-7880-11e9-8f9e-2a86e4085a59",
      "name": "string"
    },
    "returnPolicy": {
      "id": "09f0b4cc-7880-11e9-8f9e-2a86e4085a59",
      "name": "string"
    },
    "warranty": {
      "id": "09f0b4cc-7880-11e9-8f9e-2a86e4085a59",
      "name": "string"
    }
  },
  "sizeTable": {
    "id": "string",
    "name": "string"
  },
  "contact": {
    "id": "string",
    "name": "string"
  },
  "discounts": {
    "wholesalePriceList": {
      "id": "string",
      "name": "string"
    }
  },
  "name": "string",
  "payments": {
    "invoice": "VAT"
  },
  "sellingMode": {
    "format": "BUY_NOW",
    "price": {
      "amount": "123.45",
      "currency": "PLN"
    },
    "minimalPrice": {
      "amount": "123.45",
      "currency": "PLN"
    },
    "startingPrice": {
      "amount": "123.45",
      "currency": "PLN"
    }
  },
  "location": {
    "city": "string",
    "countryCode": "PL",
    "postCode": "00-999",
    "province": "string"
  },
  "images": [
    "string"
  ],
  "description": {
    "sections": [
      {
        "items": [
          {
            "type": "string"
          }
        ]
      }
    ]
  },
  "external": {
    "id": "AH-129834"
  },
  "tax": {
    "id": "ae727432-8b72-4bfe-b732-6f163a2bf32a",
    "rate": "23.00",
    "subject": "GOODS",
    "exemption": "MONEY_EQUIVALENT",
    "percentage": "23.00"
  },
  "taxSettings": {
    "rates": [
      {
        "rate": "23.00",
        "countryCode": "PL"
      }
    ],
    "subject": "GOODS",
    "exemption": "MONEY_EQUIVALENT"
  },
  "messageToSellerSettings": {
    "mode": "OPTIONAL",
    "hint": "string"
  }
}

```

zamknij

Przykładowa struktura danych

W ramach Allegro sprzedający wystawia ofertę sprzedaży, która powiązana jest z produktem (lub zestawem produktów) z naszego Katalogu Produktów. W katalogu tym gromadzimy dane o produktach (takie jak parametry, zdjęcia i opisy). Sprzedający podczas wystawiania oferty może zarówno skorzystać z istniejącego w Katalogu produktu, jak i utworzyć zupełnie nowy produkt.

##### Dokumentacja

Do utworzenia oferty służy endpoint [POST /sale/product-offers](https://developer.allegro.pl/documentation#operation/createProductOffers). W [dokumentacji](https://developer.allegro.pl/documentation#operation/createProductOffers) znajdziesz dokładne opis poszczególnych pól, przyjrzyjmy się natomiast ogólnej strukturze danych.

---

#### Produkt

Produkt to przedmiot, który sprzedający wystawia na sprzedaż w ofercie. Posiada on zbiór cech, które łącznie jednoznacznie go identyfikują, jak np. parametry. Zestaw tych cech definiujemy dla kategorii, w której dany produkt jest utworzony.

Produkt definiujemy w strukturze productSet[].product. Zwróć także uwagę, że może być to także zestaw produktów w jednej ofercie - stąd tablica productSet[].

##### Identyfikacja produktów

GTIN (EAN) jest jedną z głównych cech określających produkt, jednakże nie wystarczy on do jednoznacznej identyfikacji produktu. Może zdarzyć się, że jeden produkt będzie posiadał wiele GTIN. Wiele produktów może mieć ten sam GTIN. Dlatego ważna jest także identyfikacja pozostałych cech produktu.

---

#### Oferta

Oferta zawiera informacje zarówno o produkcie, który wystawia sprzedający, ale także uwzględnia indywidualne informacje, zależne od danego sprzedającego, takie jak:

- cennik dostawy.
- opcje faktury
- czas wysyłki
- czas trwania
- warunki zwrotów i reklamacji
- format sprzedaży (np. Kup Teraz)
- liczba dostępnych sztuk
- cena

Parametry oferty przechowywane są poza tablicą productSet[].

##### Oferta, a produkt

Tym właśnie oferta różni się od produktu. Podczas, gdy produkt posiada własny zbiór cech, na podstawie których odróżniamy go od innego produktu, oferta zawiera dodatkowe dane, które wpływają na ostateczną decyzję klienta o zakupie. Tym samym może istnieć wiele ofert tego samego produktu (wystawionych przez jednego lub różnych sprzedawców).

---

#### Kategorie oraz parametry

Dzięki kategoriom możemy pogrupować produkty tego samego rodzaju i odpowiednio zaprezentować je kupującym. Na podstawie kategorii rozpoznasz cechy (parametry), które uzupełnisz w danej kategorii.

Dostępne kategorie pobierzesz za pomocą:

- [GET /sale/categories/{categoryId}](https://developer.allegro.pl/documentation#operation/getCategoryUsingGET_1).
- [GET /sale/categories](https://developer.allegro.pl/documentation#operation/getCategoriesUsingGET)

Dodatkowo w zidentyfikowaniu odpowiedniej kategorii dla danej nazwy produktu pomoże Ci [GET /sale/matching-categories](https://developer.allegro.pl/documentation#operation/categorySuggestionUsingGET).

Struktura kategorii ma formę drzewa, a ofertę produktu możesz utworzyć w tzw. liściu, czyli w kategorii najniższego rzędu - oznaczymy taką kategorię flagą "leaf": true.

---

1. Jeżeli zidentyfikujesz już odpowiednią kategorię, możesz pobrać zestaw parametrów wspieranych dla danej kategorii: [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2).

Uzupełniając w ofercie parametry, możesz posługiwać się zarówno nazwami parametrów oraz wartości, jak i ich identyfikatorami.

---

### Jak utworzyć ofertę powiązaną z produktem

Ofertę utworzysz za pomocą [POST /sale/product-offers](https://developer.allegro.pl/documentation/#operation/createProductOffers).

Rozróżniamy dwa główne warianty tworzenia oferty z przypisanym produktem:

Gdy masz pewność, że produkt istnieje już w Katalogu Produktów Allegro.

```
import requests
import json

def create_offer_from_product(url, access_token):
  try:
    payload = json.dumps({
      "productSet": [
        {
          "product": {
            "id": "5902719471797",
            "idType": "GTIN"
          }
        }
      ],
      "sellingMode": {
        "price": {
          "amount": "220.85",
          "currency": "PLN"
        }
      },
      "stock": {
        "available": 10
      }
    })

    headers = {
      'Accept': 'application/vnd.allegro.public.v1+json',
      'Content-Type': 'application/vnd.allegro.public.v1+json',
      'Accept-Language': 'pl-PL',
      'Authorization': 'Bearer ' + access_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

def main():
  access_token = ""  # Acces Token sprzedającego. Uzyskasz go w procesie autoryacji, który opisaliśmy w poradniku:
  # https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR
  url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers"  # url endpointu. Korzystamy ze środowiska testowego, stąd dodatkowo domena "allegrosandbox.pl"
  response = create_offer_from_product(url, access_token)
  print(response.status_code)
  print(response.text)


if __name__ == "__main__":
  main()
```

zamknij

Przykładowy fragment kodu - Python

W strukturze żądania przekaż identyfikator produktu (lub GTIN) oraz cenę i liczbę sztuk. To, jak przeszukiwać Katalog Produktów za pomocą [GET /sale/products](https://developer.allegro.pl/documentation/#operation/getSaleProducts), opisujemy w [dalszej części poradnika](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#jak-znalezc-produkt).

```
curl -X POST
  'https://api.allegro.pl/sale/product-offers'
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
  -d '{
  "productSet": 
        [{
        "product":
            {
            "id": "5902719471797",   // numer GTIN, MPN lub ID produktu
            "idType": "GTIN"         // typ wartości w polu "product.id". 
                                     // Dla GTIN wskaż "GTIN",dla numerów 
                                     // katalogowych nadanych przez producenta - "MPN".
                                     // Jeśli wskazujesz UUID produktu, pozostaw pole puste.
            }
        }],
  "sellingMode": {
    "price": {
      "amount": "220.85",            // cena
      "currency": "PLN"
    }
  },
  "stock": {
    "available": 10                  // liczba sztuk
  }
}'
```

Dane produktów w niektórych przypadkach mogą być niekompletne, np. w sytuacji, gdy nie ma on uzupełnionych wszystkich wymaganych do wystawienia w tym momencie parametrów.

W takiej sytuacji odpowiemy kodem 422, z komunikatem błędu wskazującym brakujące dane:

```
{
   "errors":[
      {
         "code":"ConstraintViolationException.MissingRequiredParameters",
         "message":"Missing required parameters: 209298, 356",
         "details":"ConstraintViolationException.MissingRequiredParameters",
         "path":"parameters",
         "userMessage":"Uzupełnij parametry obowiązkowe: Skład zestawu, Pojemność.",
         "metadata":{
          }
      }
   ]
}
```

Aby uzupełnić brakujące parametry obowiązkowe, przekaż je w tablicy productSet.product.parameters[]. ID parametru wraz z dostępnymi wartościami sprawdzisz za pomocą [GET /sale/categories/{categoryID}/parameters](https://developer.allegro.pl/documentation/#operation/getFlatParametersUsingGET_2).

Gdy chcesz utworzyć nowy produkt lub nie masz pewności, że produkt istnieje w Katalogu Produktów.

```
import requests
import json

def create_offer(url, access_token):
  try:
    payload = json.dumps({
      "productSet": [
        {
          "product": {
            "name": "Produkt testowy",
            "category": {
              "id": "165"
            },
            "parameters": [
              {
                "name": "EAN",
                "values": [
                  "0744861045021"
                ]
              },
              {
                "id": "224017",
                "values": [
                  "test 1587459230"
                ]
              },
              {
                "id": "202749",
                "values": [
                  "5.9"
                ]
              },
              {
                "id": "202869",
                "values": [
                  "512 GB"
                ]
              },
              {
                "id": "202829",
                "valuesIds": [
                  "202829_1"
                ]
              },
              {
                "id": "202685",
                "valuesIds": [
                  "202685_212929"
                ]
              },
              {
                "id": "127448",
                "valuesIds": [
                  "127448_2"
                ]
              },
              {
                "id": "202865",
                "valuesIds": [
                  "202865_214109"
                ]
              },
              {
                "id": "4388",
                "valuesIds": [
                  "4388_1"
                ]
              },
              {
                "id": "202717",
                "values": [
                  100
                ]
              },
              {
                "id": "219",
                "values": [
                  "Bluetooth"
                ]
              },
              {
                "id": "202821",
                "values": [
                  "Dual SIM"
                ]
              },
              {
                "name": "Marka telefonu",
                "valuesIds": [
                  "246705_598617"
                ]
              },
              {
                "name": "Model telefonu",
                "values": [
                  "Armor 24"
                ]
              },
              {
                "name": "Transmisja danych",
                "values": [
                  "5G"
                ]
              },
              {
                "name": "Średnica obiektywu",
                "values": [
                  "8"
                ]
              }
            ],
            "images": [
              "https://assets.allegrostatic.com/opbox/allegro.pl/homepage/Main%20Page/6lJEwSSohvBIIWNlJUU9sx-w1200-h1200.png"
            ]
          }
        }
      ],
      "parameters": [
        {
          "id": "11323",
          "valuesIds": [
            "11323_2"
          ]
        }
      ],
      "images": [
        "https://assets.allegrostatic.com/opbox/allegro.pl/homepage/Main%20Page/6lJEwSSohvBIIWNlJUU9sx-w1200-h1200.png"
      ],
      "sellingMode": {
        "price": {
          "amount": "12.43",
          "currency": "PLN"
        }
      },
      "stock": {
        "available": 10
      }
    })

    headers = {
      'Accept': 'application/vnd.allegro.public.v1+json',
      'Content-Type': 'application/vnd.allegro.public.v1+json',
      'Accept-Language': 'pl-PL',
      'Authorization': 'Bearer ' + access_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

def main():
  access_token = ""  # Acces Token sprzedającego. Uzyskasz go w procesie autoryacji, który opisaliśmy w poradniku:
  # https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR
  url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers"  # url endpointu. Korzystamy ze środowiska testowego, stąd dodatkowo domena "allegrosandbox.pl"
  response = create_offer(url, access_token)
  print(response.status_code)
  print(response.text)


if __name__ == "__main__":
  main()
```

zamknij

Przykładowy fragment kodu - Python

W strukturze żądania w obiekcie product przekaż komplet danych, które opisują sprzedawany produkt. Zestaw parametrów wspieranych dla danej kategorii pobierz za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2). Równocześnie nie przekazuj żadnej wartości w polu product.id. Request uzupełnij o cenę produktu i liczbę sztuk.

```
curl -X POST
     'https://api.allegro.pl/sale/product-offers'
      -H 'Authorization: Bearer {token}'
      -H 'Accept: application/vnd.allegro.public.v1+json'
      -H 'Content-Type: application/vnd.allegro.public.v1+json'
    -d '{
    "productSet": [{
        "product": {
            "name": "Produkt testowy",
            "category": {
                "id": "89060"
            },
            "parameters": [{
                    "name": "EAN",
                    "values": [
                        "0744861045021"
                    ]
                },
                {
                    "id": "237218",
                    "values": [
                        "Testowy tytuł"
                    ]
                }
            ],
            "images": [
                "https://...adres-pierwszego-obrazka.jpeg"
            ]
        }
    }],
    "sellingMode": {
        "price": {
            "amount": "220.85",
            "currency": "PLN"
        }
    },
    "stock": {
        "available": 10
    }
}'
```

Jeśli na podstawie przekazanych danych rozpoznamy, że produkt istnieje w naszym Katalogu, to uwzględnimy jego dane w wystawionej ofercie. Będą to:

- tekstowe informacje o bezpieczeństwie
- dane producenta
- specyfikacja techniczna TecDoc
- sekcja pasuje do
- numery GTIN
- opis produktu (jeśli nie przekażesz własnego)
- zdjęcia
- kategoria i parametry

Może zdarzyć się sytuacja, że rozpoznamy produkt, jednak kategoria lub część przekazanych wartości parametrów nie jest zgodna z zapisanymi w naszym Katalogu Produktów - zwrócimy wtedy odpowiedź z kodem 422.

```
{
   "errors": [
       {
           "code": "PARAMETER_MISMATCH",
           "message": "The provided parameter 'Wysokość produktu'(223329) value (202.00) does not match 
                     the existing parameter value (22.00)",
           "details": null,
           "path": "productSet[0].product.parameters",
           "userMessage": "The specified product exists. The specified parameter `Wysokość produktu` with 
                     the value `202.00` does not match the product parameter `22.00`.",
           "metadata": {
               "productId": "8b6270a8-06c6-4ad7-a9c2-7443a79ea4ab"
           }
       }
   ]
}
```

W takiej sytuacji skoryguj te wartości. W polu metadata wskazujemy id rozpoznanego produktu. Możesz go wykorzystać do utworzenia oferty z produktem zgodnie z procesem opisanym w punkcie nr 1.

Zastanów się także nad możliwością wyświetlenia danych produktu użykownikowi końcowemu aplikacji. Czynnik ludzi także może mieć znaczenie przy odpowiednim doborze produktu.

---

Jeżeli masz pewność, że przekazane wartości są prawidłowe, możesz zasugerować zmianę w produkcie za pomocą [POST /sale/products/{productId}/change-proposals](https://developer.allegro.pl/documentation#operation/productChangeProposal).

##### Jaki rezultat oczekiwać?

Niezależnie od wybranej ścieżki - w serwisie pojawi się aktywna oferta sprzedaży wskazanego produktu, nie musisz wywoływać osobnej komendy publikacji. Pozostałych informacji wymaganych do wystawienia oferty nie musisz nam przesyłać - uzupełnimy je wtedy wartościami domyślnymi, które znajdziesz w poniższej tabeli. [W dalszej części przedstawiamy](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#jak-przekazac-wlasne-wartosci-w-zadaniu) także, jak konstruować żądanie, gdy chcesz przesłać inne dane niż wartości domyślne.

---

##### Wartości domyślne

Wartość

Oferta zostanie natychmiast aktywowana

Wartość

Kup teraz

Wartość

Sztuki

Wartość

Dane z ustawień [konta Allegro](https://allegro.pl/moje-allegro/moje-konto/dane-konta/)(Twój adres)

Wartość

Faktura VAT

Wartość

24 godziny

Wartość

Do wyczerpania przedmiotów

Wartość

Wartość ustawimy na podstawie domyślnego języka serwisu bazowego użytkownika.

Wartość

Jeżeli posiadasz jeden cennik dostawy, to przypiszemy go do oferty. W przypadku większej liczby, użyjemy cennika o nazwie default. Jeżeli nie posiadasz cennika o takiej nazwie, zwrócimy błąd 422.

Wartość

Jeżeli posiadasz konto firma i po jednej opcji dla tych pól, to przypiszemy ją do oferty. W przypadku większej liczby, użyjemy wariantu o nazwie default. Jeżeli nie posiadasz wariantu o takiej nazwie, zwrócimy błąd 422. Dla kont zwykłych nie podstawimy żadnej wartości.

| Pole | Wartość |
| --- | --- |
| Status publikacji |
| Format sprzedaży |
| Typ jednostek |
| Wysyłka z |
| Opcje faktury |
| Czas wysyłki |
| Czas trwania |
| Język oferty |
| [Cennik dostawy](https://allegro.pl/moje-allegro/sprzedaz/ustawienia-dostawy) |
| [Warunki reklamacji](https://allegro.pl/moje-allegro/sprzedaz/warunki-reklamacji) i [Warunki zwrotów](https://allegro.pl/moje-allegro/sprzedaz/warunki-zwrotow) |

W następnych punktach przejdziemy krok po kroku przez dwa przykłady obu podejść do wystawiania oferty z produktem.

---

#### Gdy masz pewność, że produkt istnieje już w Katalogu Produktów Allegro

W tym wariancie, posługując się [środowiskiem Sandbox](https://developer.allegro.pl/tutorials/pierwsze-kroki-MRwYEoOq0im#poznaj-srodowisko-testowe-sandbox), spróbujemy utworzyć ofertę w najprostszy sposób - gdy mamy pewność, że dany produkt istnieje w Katalogu Produktów oraz nie nadpisując wartości domyślnych.

Upewnij się, że na koncie testowym zdefiniowano [domyślny cennik dostawy](https://allegro.pl.allegrosandbox.pl/moje-allegro/sprzedaz/ustawienia-dostawy) oraz [warunki reklamacji](https://allegro.pl.allegrosandbox.pl/moje-allegro/sprzedaz/warunki-reklamacji) i [zwrotów](https://allegro.pl.allegrosandbox.pl/moje-allegro/sprzedaz/warunki-zwrotow).

Przeszukanie Katalogu Produktów

```
 curl -X GET \ 
  'https://api.allegro.pl.allegrosandbox.pl/sale/products?phrase=888462600712&language=pl-PL&mode=GTIN \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

W pierwszej kolejności, za pomocą [GET /sale/products](https://developer.allegro.pl/documentation#operation/getSaleProducts), wyszukaj w Katalogu interesujący Cię przedmiot.

Zwrócimy listę pasujących dla danej frazy produktów wraz z podstawowymi informacjami na ich temat.

```
{
 "products": [
  {
   "id": "5272069b-0759-4283-8ba7-7f05b416f1d9",        // identyfikator produktu - użyj go w ofercie,
                                                        by powiązać ją z produktem
   "name": "Smartfon Apple iPhone 6S srebrny 128 GB",   // nazwa produktu
   "category": {
    "id": "253002",                                     // kategoria produktu
    "path": [                                           // ścieżka kategorii głównej wskazanej 
                                                        w “category.id”
            {
                "id": "954b95b6-43cf-4104-8354-dea4d9b10ddf",
                "name": "Allegro"
            },
            {
                "id": "42540aec-367a-4e5e-b411-17c09b08e41f",
                "name": "Elektronika"
            },
            {
                "id": "4",
                "name": "Telefony i Akcesoria"
            },
            {
                "id": "165",
                "name": "Smartfony i telefony komórkowe"
            },
            {
                "id": "48978",
                "name": "Apple"
            },
            {
                "id": "253002",
                "name": "iPhone 6S"
            }
        ],
    "similar": [
            {
                "id": "316188",
                "path": [                                // ścieżka kategorii podobnej wskazanej 
                                                         w “category.similar.id”
                    {
                        "id": "954b95b6-43cf-4104-8354-dea4d9b10ddf",
                        "name": "Allegro"
                    },
                    {
                        "id": "42540aec-367a-4e5e-b411-17c09b08e41f",
                        "name": "Elektronika"
                    },
                    {
                        "id": "4",
                        "name": "Telefony i Akcesoria"
                    },
                    {
                        "id": "165",
                        "name": "Smartfony i telefony komórkowe"
                    },
                    {
                        "id": "48978",
                        "name": "Apple"
                    },
                    {
                        "id": "316188",
                        "name": "iPhone 12"
                    }
                ]
   },
   "parameters": [                                      // parametry produktu
    {
     "id": "224017",                                    // identyfikator parametru
     "name": "Kod producenta",                          -- nazwa parametru
     "valuesLabels": [                                  // etykieta wartości parametru
      "MKQU2PM/A"
     ],
     "values": [
      "MKQU2PM/A"                                       // wartość parametru - dla typu string
     ],
     "unit": null,                                      // jednostka wartości parametru. Jeśli
                                                        dany parametr nie ma jednostki,
                                                        zwracamy wartość null
     "options": {
      "identifiesProduct": true                         // czy parametr identyfikuje produkt.
                                                                               // Wartości parametrów oznaczonych 
                                                                                                                                                 //jako true nie nie możesz nadpisać
     }                                                  
    },                                                  
    {
     "id": "127448",                                    // identyfikator parametru
     "name": "Kolor",                                   // nazwa parametru
     "valuesLabels": [                                  // etykieta wartości parametru
      "srebrny"
     ],
     "valuesIds": [                                     // identyfikator wartości parametru,
      "127448_8"                                        dla typu słownikowego
     ],
     "unit": null,                                      // jednostka wartości parametru. Jeśli
                                                        dany parametr nie ma jednostki,
                                                        zwracamy wartość null
     "options": {
         "identifiesProduct": true
     }
    },
    {
     "id": "202733",                                    // identyfikator parametru
     "name": "Funkcje aparatu",                         // nazwa parametru
     "valuesLabels": [                                  // etykiety wartości parametrów
      "HDR",
      "autofocus",
      "lampa błyskowa",
      "panorama",
      "samowyzwalacz",
      "wykrywanie twarzy",
      "zdjęcia seryjne"
     ],
     "valuesIds": [                                     // identyfikatory wartości parametru,
      "202733_1024",                                    dla typu słownikowego wielowartościowego
      "202733_2",
      "202733_1",
      "202733_4",
      "202733_128",
      "202733_32",
      "202733_64"
     ],
     "unit": null,                                      // jednostka wartości parametru. Jeśli
                                                        dany parametr nie ma jednostki,
                                                        zwracamy wartość null
     "options": {
         "identifiesProduct": false
     }
    },
    {
    "id": "225693",                                     // identyfikator parametru
    "name": "EAN",                                      // nazwa parametru
    "valuesLabels": [
        "888462600712"                                  // etykieta wartości parametru
    ],
    "values": [
        "888462600712"                                  // wartość parametru
    ],
    "unit": null,
    "options": {
        "identifiesProduct": true,
        "isGTIN": true                                  // czy  parametr jest 
                                                      GTIN-em. Jeśli parametr ma wiele
                                                    wartości, przekaż tylko jedną z nich.

    },
  ...
   ],
   "images": [                                          // zdjęcia produktu
    {
     "url": "https://a.allegroimg.com/original/00e0c9/1d7c95614fd6a7c713b075d0251a/
     Smartfon-Apple-iPhone-6S-srebrny-128-GB"
    }   
   ],
   "publication": {
           "status": "LISTED"         // status produktu. "PROPOSED" zwracamy dla 
                                       nowych propozycji produktów i produktów z katalogu, 
                                       które nie zostały przez nas sprawdzone, "LISTED" dla 
                                       produktów z katalogu, które zostały przez nas sprawdzone, 
                                       np. zweryfikowaliśmy, że podany numer GTIN znajduje się w oficjalnej bazie GS1
            },
   "aiCoCreatedContent": {               // informacja o tym, czy określona część produktu 
                                            (zwrócona w polu „paths”) została wygenerowana przez AI
        "paths": []
            },
    "trustedContent": {    // elementy danych produktów, które są zaufane
        "paths": [
            "images",
            "description"
        ]
    }
     }]}
```

zamknij

Przykładowa lista produktów

##### Katalog produktów

W [dalszej części poradnika](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#jak-znalezc-produkt) szczegółowo opisujemy, jakie udostępniamy możliwości przeszukiwania Katalogu Produktów.

---

Pobierz pełne dane produktu

```
 curl -X GET \
  'https://api.allegro.pl.allegrosandbox.pl/sale/products/b2b61e23-b580-4471-b653-6ed25fd179f7' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

Po wybraniu produktu możesz pobrać szczegółowe informacje na jego temat.

Zwrócimy jeszcze bogatszy zestaw danych na temat produktu.

```
{
 "id": "634238b1-4385-4de7-9c00-dfa49fce16ab",       // identyfikator produktu - użyj go w ofercie,
                                                     by powiązać ją z produktem
 "name": "Harry Potter i Książę Półkrwi",            // nazwa produktu
 "category": {
  "id": "91447",                                     // kategoria produktu
  "path": [      // ścieżka kategorii głównej wskazanej 
                                                        w “category.id”
            {
                "id": "954b95b6-43cf-4104-8354-dea4d9b10ddf",
                "name": "Allegro"
            },
            {
                "id": "38d588fd-7e9c-4c42-a4ae-6831775eca45",
                "name": "Kultura i rozrywka"
            },
            {
                "id": "7",
                "name": "Książki i Komiksy"
            },
            {
                "id": "260379",
                "name": "Książki dla młodzieży"
            }
        ],
  "similar": [
            {
                "id": "66794",
                "path": [     // ścieżka kategorii podobnej wskazanej 
                                                         w “category.similar.id”
                    {
                        "id": "954b95b6-43cf-4104-8354-dea4d9b10ddf",
                        "name": "Allegro"
                    },
                    {
                        "id": "38d588fd-7e9c-4c42-a4ae-6831775eca45",
                        "name": "Kultura i rozrywka"
                    },
                    {
                        "id": "7",
                        "name": "Książki i Komiksy"
                    },
                    {
                        "id": "66794",
                        "name": "Książki do nauki języka obcego"
                    }
                ]
                        }
                ]
      },
  "parameters": [                                    // parametry produktu
  {
  "id": "245669",                                    // parametr GTIN
  "name": "ISBN",
  "valuesLabels": [
     "9788380082434"
             ],
  "values": [
     "9788380082434"
             ],
  "unit": null,
  "options": {
     "identifiesProduct": true,
     "isGTIN": true
  }
  },
  {
   "id": "7773",
   "name": "Okładka",
   "valuesLabels": [
    "twarda"
   ],
   "valuesIds": [
    "7773_3"
   ],
   "unit": null,                                    // jednostka wartości parametru. Jeśli
                                                    dany parametr nie ma jednostki,
                                                    zwracamy wartość null
   "options": {
    "identifiesProduct": true
   }
  },
 ...
 ],
 "images": [                                        // zdjęcia produktu
  {
   "url": "https://e.allegroimg.com/original/05239b/a708a8864b2bb2c9b23e450bd98e/
   Harry-Potter-i-Ksiaze-Polkrwi-J-K-Rowling-a708a8864b2bb2c9b23e450bd98e"
  },
  {
   "url": "https://5.allegroimg.com/original/00cc55/670c94c04db19158b020d827c715/
   Harry-Potter-i-Ksiaze-Polkrwi-J-K-Rowling"
  }
 ],
 "offerRequirements": {                             // jakie wymagania musi spełniać oferta,
  "id": null                                        by można ją było powiązać z danym produktem np. Stan = Nowy
  "parameters": [                                   
   {
    "id": "11323",
    "name": "Stan",
    "valuesLabels": [
     "Nowy"
    ],
    "valuesIds": [
     "11323_1"
    ],
    "options": {
     "identifiesProduct": false
    }
   }
  ]
 },
 "compatibilityList": {
  "id": "d04e8a0c-40a1-4c53-8902-ffee7261845e-cf5b236d0f72d0abc0418669fe6569d73432b49250032a21f044696eed7e7d70-2",
                                                    // identyfikator sekcji Pasuje do
  "type": "PRODUCT_BASED",                          // typ sekcji Pasuje do
  "items": [                                        // tekstowa reprezentacja sekcji Pasuje do
   {
    "text": "ALFA ROMEO 147 (937_) 1.6 16V T.SPARK (937.AXA1A, 937.AXB1A, 937.BXB1A) 2001/01-2010/03120KM/88kW"
   },
 ...   
   {
    "text": "SKODA RAPID Spaceback (NH1) 1.2 TSI 2012/07-105KM/77kW"
   }
  ]
  },
  "tecdocSpecification": {
  "id": "e3725f4b-1b4b-4e39-ad7f-331a2c858a7f",     // identyfikator specyfikacji technicznej TecDoc
  "items": [                                        // tekstowa reprezentacja specyfikacji technicznej TecDoc
   {
    "name": "Wysokość [mm]",
    "values": [
     "51"
    ]
   },
 ...   
   {
    "name": "Wersja TecDoc",
    "values": [
     "TecDoc 0619"
     ]
    }
   ]
  },
   "publication": {
           "status": "LISTED"         // status produktu. "PROPOSED" zwracamy dla 
                                       nowych propozycji produktów i produktów z katalogu, 
                                       które nie zostały przez nas sprawdzone, "LISTED" dla 
                                       produktów z katalogu, które zostały przez nas sprawdzone, 
                                       np. zweryfikowaliśmy, że podany numer GTIN znajduje się w oficjalnej bazie GS1
            },
   "aiCoCreatedContent": {               // informacja o tym, czy określona część produktu 
                                            (zwrócona w polu „paths”) została wygenerowana przez AI
        "paths": []
            },
"trustedContent": {    // elementy danych produktów, które są zaufane
        "paths": [
            "images"
        ]
    }
 }
```

zamknij

Szczegóły produktu

Utwórz ofertę z wybranym produktem

```
  curl -X POST
  'https://api.allegro.pl.allegrosandbox.pl/sale/product-offers'
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
  -d '{
  "productSet": [{
    "product": {
      "id": "5902719471797",        
      "idType": "GTIN"
    }}],
    "sellingMode": {
      "price": {
        "amount": "220.85",    
        "currency": "PLN"
      }
    },
    "stock": {
      "available": 10               
    }  
}'
```

Po wybraniu produktu i upewnieniu się, że jest prawidłowy, skorzystaj z niego, wykonując żądanie [POST /sale/product-offers](https://developer.allegro.pl/documentation#operation/createProductOffers).

##### Fragment kodu - Python

```
import requests
import json

def create_offer_from_product(url, access_token):
  try:
    payload = json.dumps({
      "productSet": [
        {
          "product": {
            "id": "5902719471797",
            "idType": "GTIN"
          }
        }
      ],
      "sellingMode": {
        "price": {
          "amount": "220.85",
          "currency": "PLN"
        }
      },
      "stock": {
        "available": 10
      }
    })

    headers = {
      'Accept': 'application/vnd.allegro.public.v1+json',
      'Content-Type': 'application/vnd.allegro.public.v1+json',
      'Accept-Language': 'pl-PL',
      'Authorization': 'Bearer ' + access_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

def main():
  access_token = ""  # Acces Token sprzedającego. Uzyskasz go w procesie autoryacji, który opisaliśmy w poradniku:
  # https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR
  url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers"  # url endpointu. Korzystamy ze środowiska testowego, stąd dodatkowo domena "allegrosandbox.pl"
  response = create_offer_from_product(url, access_token)
  print(response.status_code)
  print(response.text)


if __name__ == "__main__":
  main()
```

---

#### Gdy chcesz utworzyć nowy produkt lub nie masz pewności, że produkt istnieje w Katalogu Produktów

W tym wariancie posługując się [środowiskiem Sandbox](https://developer.allegro.pl/tutorials/pierwsze-kroki-MRwYEoOq0im#poznaj-srodowisko-testowe-sandbox) spróbujemy utworzyć ofertę dla nieco bardziej skomplikowanego przypadku - gdy chcesz utworzyć nowy produkt lub nie masz pewności, że produkt istnieje w Katalogu Produktów.

Upewnij się, że na koncie testowym [zdefiniowano domyślny](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#wartosci-domyslne) [cennik dostawy](https://allegro.pl.allegrosandbox.pl/moje-allegro/sprzedaz/ustawienia-dostawy) oraz [warunki reklamacji](https://allegro.plallegrosandbox.pl/moje-allegro/sprzedaz/warunki-reklamacji) i [zwrotów](https://allegro.pl.allegrosandbox.pl/moje-allegro/sprzedaz/warunki-zwrotow).

W requeście musisz podać komplet informacji o produkcie. Przekazane dane posłużą do zgłoszenia propozycji produktu. Zweryfikujemy je, a zaakceptowane przez nas dane produktu będą dostępne na platformie. Część danych może być weryfikowana automatycznie, część po pewnym czasie.

Przygotuj następujące dane, by zaproponować produkt:

- opis produktu.
- zdjęcia
- parametry i wartości parametrów
- kategorię
- sugerowaną nazwę produktu

Uzupełnij kategorię i parametry

```
"productSet": [{
    "product": {
    "category":{
            "id":"165"
        },
                "parameters": [
                    {
                        "name": "EAN",
                        "values": [
                            "0744861045021"
                        ]
                    },
                    {
                        "id": "224017",
                        "values": [
                            "test 1587459230"
                        ]
                    },
                    {
                        "id": "202749",
                        "values": [
                            "5.9"
                        ]
                    },
                    {
                        "id": "202869",
                        "values": [
                            "512 GB"
                        ]
                    },
                    {
                        "id": "202829",
                        "valuesIds": [
                            "202829_1"
                        ]
                    },
                    {
                        "id": "202685",
                        "valuesIds": [
                            "202685_212929"
                        ]
                    },
                    {
                        "id": "127448",
                        "valuesIds": [
                            "127448_2"
                        ]
                    },
                    {
                        "id": "202865",
                        "valuesIds": [
                            "202865_214109"
                        ]
                    },
                    {
                        "id": "4388",
                        "valuesIds": [
                            "4388_1"
                        ]
                    },
                    {
                        "id": "202717",
                        "values": [
                            100
                        ]
                    },
                    {
                        "id": "219",
                        "values": [
                            "Bluetooth"
                        ]
                    },
                    {
                        "id": "202821",
                        "values": [
                            "Dual SIM"
                        ]
                    },
                    {
                        "name": "Marka telefonu",
                        "valuesIds": [
                            "246705_598617"
                        ]
                    },
                    {
                        "name": "Model telefonu",
                        "values": [
                            "Armor 24"
                        ]
                    },
                    {
                        "name": "Transmisja danych",
                        "values": [
                            "5G"
                        ]
                    },
                    {
                        "name": "Średnica obiektywu",
                        "values": [
                            "8"
                        ]
                    }
     ...
  ]
 }}]
 ...
```

zamknij

Przykładowe sposoby przekazywania parametrów i ich wartości

Dostępne kategorie pobierzesz za pomocą:

- [GET /sale/categories/{categoryId}](https://developer.allegro.pl/documentation#operation/getCategoryUsingGET_1).
- [GET /sale/categories](https://developer.allegro.pl/documentation#operation/getCategoriesUsingGET)

Wywołując [GET /sale/categories](https://developer.allegro.pl/documentation#operation/getCategoriesUsingGET), otrzymasz listę kategorii głównych. Gdy odpytasz [GET /sale/categories?parent.id={categoryId}](https://developer.allegro.pl/documentation#operation/getCategoriesUsingGET), wykorzystując ID jednej z kategorii głównych, zwrócimy listę podkategorii. Nawigując w ten sposób po drzewie kategorii, możesz znaleźć odpowiednią kategorię. Ofertę możesz utworzyć w tzw. liściu, czyli w kategorii najniższego rzędu - oznaczonej flagą "leaf": true.

Gdy już zmapujesz odpowiednią kategorię, skorzystaj z [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2) aby pobrać dostępne w niej parametry. W polu requiredForProduct znajdziesz informację, czy dany parametr jest wymagany, gdy tworzysz nowy produkt.

Zamiast identyfikatorów parametrów możesz użyć ich nazw. Dla parametrów:

- zakresowych (typu range) w polu values możesz przekazać dwie wartości, które będą odpowiadać “from” i “to”.
- słownikowych (typu dictionary) w polu values możesz także przekazać samą nazwę

Przekaż GTIN jako parametr

```
 "productSet": [{
    "product": {
    ...
    "parameters": [
    {
         "name": "EAN",
         "values": [
             "0744861045021"
         ]
     },
     ...
  ]}}]
  …
```

Przekaż numer GTIN jako parametr w sekcji parameters.

Za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation#operation/getFlatParametersUsingGET_2) sprawdź, czy w danej kategorii musisz przekazać numer EAN, ISBN lub ISSN, gdy chcesz dodać produkt. Świadczy o tym wartość true w polu requiredForProduct parametru GTIN.

Dodaj zdjęcia produktu

```
 "productSet": [{
     "product": {
     ...
         "images": [
            "https://...zewnetrzny-adres-pierwszego-obrazka.jpeg",
            "https://...zewnetrzny-adres-drugiego-obrazka.jpeg"
        ]
     ...    
```

W sekcji images dodaj obrazki, które prezentują produkt. Zdjęcia mogą pochodzić z zewnętrznych serwerów.

Każda oferta musi mieć minimum 1 zdjęcie, maksymalna ich liczba to 16. Więcej o obowiązujących zasadach dotyczących zdjęć [przeczytasz w Pomocy dla sprzedających](https://help.allegro.com/sell/pl/a/zasady-dla-zdjec-w-galerii-i-w-opisie-8dvWz3eo4T5?marketplaceId=allegro-pl).

Uzupełnij pozostałe dane

```
curl -X POST
'https://api.allegro.pl.allegrosandbox.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
    "productSet": [
        {
            "product": {
                "name": "Produkt testowy",
                "category": {
                    "id": "165"
                },
                "parameters": [
                    {
                        "name": "EAN",
                        "values": [
                            "0744861045021"
                        ]
                    },
                    {
                        "id": "224017",
                        "values": [
                            "test 1587459230"
                        ]
                    },
                    {
                        "id": "202749",
                        "values": [
                            "5.9"
                        ]
                    },
                    {
                        "id": "202869",
                        "values": [
                            "512 GB"
                        ]
                    },
                    {
                        "id": "202829",
                        "valuesIds": [
                            "202829_1"
                        ]
                    },
                    {
                        "id": "202685",
                        "valuesIds": [
                            "202685_212929"
                        ]
                    },
                    {
                        "id": "127448",
                        "valuesIds": [
                            "127448_2"
                        ]
                    },
                    {
                        "id": "202865",
                        "valuesIds": [
                            "202865_214109"
                        ]
                    },
                    {
                        "id": "4388",
                        "valuesIds": [
                            "4388_1"
                        ]
                    },
                    {
                        "id": "202717",
                        "values": [
                            100
                        ]
                    },
                    {
                        "id": "219",
                        "values": [
                            "Bluetooth"
                        ]
                    },
                    {
                        "id": "202821",
                        "values": [
                            "Dual SIM"
                        ]
                    },
                    {
                        "name": "Marka telefonu",
                        "valuesIds": [
                            "246705_598617"
                        ]
                    },
                    {
                        "name": "Model telefonu",
                        "values": [
                            "Armor 24"
                        ]
                    },
                    {
                        "name": "Transmisja danych",
                        "values": [
                            "5G"
                        ]
                    },
                    {
                        "name": "Średnica obiektywu",
                        "values": [
                            "8"
                        ]
                    }
                ],
                "images": [
    "https://assets.allegrostatic.com/opbox/allegro.pl/homepage/Main%20Page/6lJEwSSohvBIIWNlJUU9sx-w1200-h1200.png"
                ]
            }
        }
    ],
    "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "images": [
        "https://assets.allegrostatic.com/opbox/allegro.pl/homepage/Main%20Page/6lJEwSSohvBIIWNlJUU9sx-w1200-h1200.png"
    ],
    "sellingMode": {
        "price": {
            "amount": "12.43",
            "currency": "PLN"
        }
    },
    "stock": {
        "available": 10
    }
}
'
```

Aby wystawić ofertę, to oprócz podstawowych danych opisujących produkt, musisz również uzupełnić cenę, liczbę sztuk oraz parametry ofertowe (jeżeli są wymagane).

##### Fragment kodu - Python

```
import requests
import json

def create_offer(url, access_token):
  try:
    payload = json.dumps({
      "productSet": [
        {
          "product": {
            "name": "Produkt testowy",
            "category": {
              "id": "165"
            },
            "parameters": [
              {
                "name": "EAN",
                "values": [
                  "0744861045021"
                ]
              },
              {
                "id": "224017",
                "values": [
                  "test 1587459230"
                ]
              },
              {
                "id": "202749",
                "values": [
                  "5.9"
                ]
              },
              {
                "id": "202869",
                "values": [
                  "512 GB"
                ]
              },
              {
                "id": "202829",
                "valuesIds": [
                  "202829_1"
                ]
              },
              {
                "id": "202685",
                "valuesIds": [
                  "202685_212929"
                ]
              },
              {
                "id": "127448",
                "valuesIds": [
                  "127448_2"
                ]
              },
              {
                "id": "202865",
                "valuesIds": [
                  "202865_214109"
                ]
              },
              {
                "id": "4388",
                "valuesIds": [
                  "4388_1"
                ]
              },
              {
                "id": "202717",
                "values": [
                  100
                ]
              },
              {
                "id": "219",
                "values": [
                  "Bluetooth"
                ]
              },
              {
                "id": "202821",
                "values": [
                  "Dual SIM"
                ]
              },
              {
                "name": "Marka telefonu",
                "valuesIds": [
                  "246705_598617"
                ]
              },
              {
                "name": "Model telefonu",
                "values": [
                  "Armor 24"
                ]
              },
              {
                "name": "Transmisja danych",
                "values": [
                  "5G"
                ]
              },
              {
                "name": "Średnica obiektywu",
                "values": [
                  "8"
                ]
              }
            ],
            "images": [
              "https://assets.allegrostatic.com/opbox/allegro.pl/homepage/Main%20Page/6lJEwSSohvBIIWNlJUU9sx-w1200-h1200.png"
            ]
          }
        }
      ],
      "parameters": [
        {
          "id": "11323",
          "valuesIds": [
            "11323_2"
          ]
        }
      ],
      "images": [
        "https://assets.allegrostatic.com/opbox/allegro.pl/homepage/Main%20Page/6lJEwSSohvBIIWNlJUU9sx-w1200-h1200.png"
      ],
      "sellingMode": {
        "price": {
          "amount": "12.43",
          "currency": "PLN"
        }
      },
      "stock": {
        "available": 10
      }
    })

    headers = {
      'Accept': 'application/vnd.allegro.public.v1+json',
      'Content-Type': 'application/vnd.allegro.public.v1+json',
      'Accept-Language': 'pl-PL',
      'Authorization': 'Bearer ' + access_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

def main():
  access_token = ""  # Acces Token sprzedającego. Uzyskasz go w procesie autoryacji, który opisaliśmy w poradniku:
  # https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR
  url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers"  # url endpointu. Korzystamy ze środowiska testowego, stąd dodatkowo domena "allegrosandbox.pl"
  response = create_offer(url, access_token)
  print(response.status_code)
  print(response.text)


if __name__ == "__main__":
  main()
```

---

#### Asynchroniczne procesowanie

Gdy wyślesz prawidłowy, zupełny request, możesz spodziewać się jednego z dwóch statusów:

- 202 Accepted - ze względu na dłuższy czas wykonania operacji zadanie przeprowadzimy asynchronicznie.
- 201 Created - ofertę utworzymy od razu

###### Status 201 Created:

```
HTTP/1.1 201 Created
{
    "name": "Ulefone Power telefon",
    "productSet": [
        {
            "product": {
                "id": "2f771572-8302-4c09-b304-391f039e3195",
                "publication": {
                    "status": "LISTED"
                },
                "parameters": [
                    {
                        "id": "246705",
                        "name": "Marka telefonu",
                        "values": [
                            "Ulefone"
                        ],
                        "valuesIds": [
                            "246705_598617"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "225693",
                        "name": "EAN (GTIN)",
                        "values": [
                            "0744861045021",
                            "744861045021"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202869",
                        "name": "Wbudowana pamięć",
                        "values": [
                            "512 GB"
                        ],
                        "valuesIds": [
                            "202869_214181"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202865",
                        "name": "Pamięć RAM",
                        "values": [
                            "16 GB"
                        ],
                        "valuesIds": [
                            "202865_214109"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "236462",
                        "name": "Średnica obiektywu",
                        "values": [
                            "8.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "224017",
                        "name": "Kod producenta",
                        "values": [
                            "test 1587459230"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202749",
                        "name": "Przekątna ekranu",
                        "values": [
                            "5.90"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202829",
                        "name": "Funkcje w telefonach komórkowych",
                        "values": [
                            "kalkulator"
                        ],
                        "valuesIds": [
                            "202829_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202685",
                        "name": "Typ",
                        "values": [
                            "Smartfon"
                        ],
                        "valuesIds": [
                            "202685_212929"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "127448",
                        "name": "Kolor",
                        "values": [
                            "biały"
                        ],
                        "valuesIds": [
                            "127448_2"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "4388",
                        "name": "System operacyjny",
                        "values": [
                            "Android"
                        ],
                        "valuesIds": [
                            "4388_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202717",
                        "name": "Pojemność akumulatora",
                        "values": [
                            "100"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "219",
                        "name": "Komunikacja",
                        "values": [
                            "Bluetooth"
                        ],
                        "valuesIds": [
                            "219_2"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202821",
                        "name": "Opcje SIM",
                        "values": [
                            "Dual SIM"
                        ],
                        "valuesIds": [
                            "202821_213909"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "246737",
                        "name": "Model telefonu",
                        "values": [
                            "Armor 24"
                        ],
                        "valuesIds": [
                            "246737_1785892"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "217",
                        "name": "Transmisja danych",
                        "values": [
                            "5G"
                        ],
                        "valuesIds": [
                            "217_2048"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202741",
                        "name": "Materiał",
                        "values": [
                            "aluminium"
                        ],
                        "valuesIds": [
                            "202741_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "227381",
                        "name": "Szerokość",
                        "values": [
                            "99.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "227357",
                        "name": "Wysokość",
                        "values": [
                            "11.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "245581",
                        "name": "Głębokość",
                        "values": [
                            "11.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202705",
                        "name": "Waga",
                        "values": [
                            "11.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "17448",
                        "name": "Waga produktu z opakowaniem jednostkowym",
                        "values": [
                            "11.000"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202745",
                        "name": "Rodzaj wyświetlacza",
                        "values": [
                            "LCD IPS"
                        ],
                        "valuesIds": [
                            "202745_213201"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202873",
                        "name": "Ekran dotykowy",
                        "values": [
                            "tak"
                        ],
                        "valuesIds": [
                            "202873_214265"
                        ],
                        "rangeValue": null
                    }
                ],
                "isAiCoCreated": false
            },
            "quantity": {
                "value": 1
            },
            "responsiblePerson": null
        }
    ],
    "parameters": [
        {
            "id": "11323",
            "name": "Stan",
            "values": [
                "Używany"
            ],
            "valuesIds": [
                "11323_2"
            ],
            "rangeValue": null
        }
    ],
    "images": [
        "https://a.allegroimg.allegrosandbox.pl/original/11ecc5/3c986dc84419b206015a2e6f1c65"
    ],
    "afterSalesServices": {
        "impliedWarranty": {
            "id": "f86078a6-9f42-4b76-9696-1e5c0646a60a"
        },
        "returnPolicy": {
            "id": "f54ba3c2-9710-4108-b275-28ee9be2b7b7"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "VAT"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": "12.43",
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 10,
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
        "handlingTime": "PT24H",
        "additionalInfo": null,
        "shipmentDate": null
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Produkt testowy</p><p>Cechy produktu:</p><ul><li> Typ:Smartfon</li> <li> Kolor: biały</li> <li> Przekątna ekranu: 5,9</li> <li> Rodzaj wyświetlacza: </li> <li> Wbudowana pamięć: 512 GB</li> <li> Pamięć RAM: 16 GB},{</li> </ul><p> </p>"
                    }
                ]
            }
        ]
    },
    "external": null,
    "category": {
        "id": "165"
    },
    "tax": null,
    "taxSettings": null,
    "sizeTable": null,
    "discounts": {
        "wholesalePriceList": null
    },
    "contact": null,
    "fundraisingCampaign": null,
    "messageToSellerSettings": null,
    "attachments": [],
    "b2b": {
        "buyableOnlyByBusiness": false
    },
    "additionalServices": null,
    "compatibilityList": null,
    "additionalMarketplaces": {
        "allegro-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-sk": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-business-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-hu": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        }
    },
    "id": "7770274320",
    "language": "pl-PL",
    "publication": {
        "status": "INACTIVE",
        "duration": null,
        "endedBy": null,
        "endingAt": null,
        "startingAt": null,
        "republish": false,
        "marketplaces": {
            "base": {
                "id": "allegro-pl"
            },
            "additional": []
        }
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2024-06-30T08:16:36.128Z"
    },
    "createdAt": "2024-06-30T08:16:36.000Z",
    "updatedAt": "2024-06-30T08:16:36.142Z"
}
```

zamknij

Przykładowy response ze statusem 201

W odpowiedzi od razu przekażemy dane oferty. Utworzymy ją w sposób synchroniczny - oferta została już przetworzona.

###### Status 202 Accepted:

```
HTTP/1.1 202 Accepted
 location: https://api.allegro.pl/sale/product-offers/9531382307/operations/eadb2e97-9850-4c51-bd27-68888b6d7d5d
 retry-after: 5
 {
    "name": "Ulefone Power telefon",
    "productSet": [
        {
            "product": {
                "id": "2f771572-8302-4c09-b304-391f039e3195",
                "publication": {
                    "status": "LISTED"
                },
                "parameters": [
                    {
                        "id": "246705",
                        "name": "Marka telefonu",
                        "values": [
                            "Ulefone"
                        ],
                        "valuesIds": [
                            "246705_598617"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "225693",
                        "name": "EAN (GTIN)",
                        "values": [
                            "0744861045021",
                            "744861045021"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202869",
                        "name": "Wbudowana pamięć",
                        "values": [
                            "512 GB"
                        ],
                        "valuesIds": [
                            "202869_214181"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202865",
                        "name": "Pamięć RAM",
                        "values": [
                            "16 GB"
                        ],
                        "valuesIds": [
                            "202865_214109"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "236462",
                        "name": "Średnica obiektywu",
                        "values": [
                            "8.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "224017",
                        "name": "Kod producenta",
                        "values": [
                            "test 1587459230"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202749",
                        "name": "Przekątna ekranu",
                        "values": [
                            "5.90"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202829",
                        "name": "Funkcje w telefonach komórkowych",
                        "values": [
                            "kalkulator"
                        ],
                        "valuesIds": [
                            "202829_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202685",
                        "name": "Typ",
                        "values": [
                            "Smartfon"
                        ],
                        "valuesIds": [
                            "202685_212929"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "127448",
                        "name": "Kolor",
                        "values": [
                            "biały"
                        ],
                        "valuesIds": [
                            "127448_2"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "4388",
                        "name": "System operacyjny",
                        "values": [
                            "Android"
                        ],
                        "valuesIds": [
                            "4388_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202717",
                        "name": "Pojemność akumulatora",
                        "values": [
                            "100"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "219",
                        "name": "Komunikacja",
                        "values": [
                            "Bluetooth"
                        ],
                        "valuesIds": [
                            "219_2"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202821",
                        "name": "Opcje SIM",
                        "values": [
                            "Dual SIM"
                        ],
                        "valuesIds": [
                            "202821_213909"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "246737",
                        "name": "Model telefonu",
                        "values": [
                            "Armor 24"
                        ],
                        "valuesIds": [
                            "246737_1785892"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "217",
                        "name": "Transmisja danych",
                        "values": [
                            "5G"
                        ],
                        "valuesIds": [
                            "217_2048"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202741",
                        "name": "Materiał",
                        "values": [
                            "aluminium"
                        ],
                        "valuesIds": [
                            "202741_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "227381",
                        "name": "Szerokość",
                        "values": [
                            "99.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "227357",
                        "name": "Wysokość",
                        "values": [
                            "11.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "245581",
                        "name": "Głębokość",
                        "values": [
                            "11.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202705",
                        "name": "Waga",
                        "values": [
                            "11.00"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "17448",
                        "name": "Waga produktu z opakowaniem jednostkowym",
                        "values": [
                            "11.000"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202745",
                        "name": "Rodzaj wyświetlacza",
                        "values": [
                            "LCD IPS"
                        ],
                        "valuesIds": [
                            "202745_213201"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202873",
                        "name": "Ekran dotykowy",
                        "values": [
                            "tak"
                        ],
                        "valuesIds": [
                            "202873_214265"
                        ],
                        "rangeValue": null
                    }
                ],
                "isAiCoCreated": false
            },
            "quantity": {
                "value": 1
            },
            "responsiblePerson": null
        }
    ],
    "parameters": [
        {
            "id": "11323",
            "name": "Stan",
            "values": [
                "Używany"
            ],
            "valuesIds": [
                "11323_2"
            ],
            "rangeValue": null
        }
    ],
    "images": [
        "https://a.allegroimg.allegrosandbox.pl/original/11ecc5/3c986dc84419b206015a2e6f1c65"
    ],
    "afterSalesServices": {
        "impliedWarranty": {
            "id": "f86078a6-9f42-4b76-9696-1e5c0646a60a"
        },
        "returnPolicy": {
            "id": "f54ba3c2-9710-4108-b275-28ee9be2b7b7"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "VAT"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": "12.43",
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 10,
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
        "handlingTime": "PT24H",
        "additionalInfo": null,
        "shipmentDate": null
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Produkt testowy</p><p>Cechy produktu:</p><ul><li> Typ:Smartfon</li> <li> Kolor: biały</li> <li> Przekątna ekranu: 5,9</li> <li> Rodzaj wyświetlacza: </li> <li> Wbudowana pamięć: 512 GB</li> <li> Pamięć RAM: 16 GB},{</li> </ul><p> </p>"
                    }
                ]
            }
        ]
    },
    "external": null,
    "category": {
        "id": "165"
    },
    "tax": null,
    "taxSettings": null,
    "sizeTable": null,
    "discounts": {
        "wholesalePriceList": null
    },
    "contact": null,
    "fundraisingCampaign": null,
    "messageToSellerSettings": null,
    "attachments": [],
    "b2b": {
        "buyableOnlyByBusiness": false
    },
    "additionalServices": null,
    "compatibilityList": null,
    "additionalMarketplaces": {
        "allegro-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-sk": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-business-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-hu": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        }
    },
    "id": "7770273738",
    "language": "pl-PL",
    "publication": {
        "status": "INACTIVE",
        "duration": null,
        "endedBy": null,
        "endingAt": null,
        "startingAt": null,
        "republish": false,
        "marketplaces": {
            "base": {
                "id": "allegro-pl"
            },
            "additional": []
        }
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2024-06-30T08:11:36.862Z"
    },
    "createdAt": "2024-06-30T08:11:36.000Z",
    "updatedAt": "2024-06-30T08:11:36.925Z"
}
```

zamknij

Przykładowy response ze statusem 202

Żądanie jest przetwarzane asynchronicznie. W odpowiedzi otrzymasz dane oferty z aktualnym jej stanem - nieuwzględniającym zmian, które wciąż są procesowane.

Aby sprawdzić status publikacji, skorzystaj z adresu otrzymanego w nagłówku Location - jest to odnośnik do zasobu, który należy odpytywać, aby sprawdzić status wykonania żądania. Z kolei w nagłówku retry-after przekazujemy informację, po jakim czasie (w sekundach) możesz ponownie odpytać zasób.

Skorzystaj z metody GET oraz otrzymanego adresu w Location ([GET /sale/product-offers/{offerId}/operations/{operationId}](https://developer.allegro.pl/documentation#operation/getProductOfferProcessingStatus)). Do czasu zakończenia operacji w odpowiedzi na to żądanie wyślemy status 202 Accepted.

Przykładowy request:

```
curl -X GET \ 
  'https://api.allegro.pl/sale/product-offers/9531382307/7770273738/eadb2e97-9850-4c51-bd27-68888b6d7d5d'
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
{
 HTTP/1.1 202 Accepted
 location: https://api.allegro.pl/sale/product-offers/7770273738/operations/eadb2e97-9850-4c51-bd27-68888b6d7d5d
 retry-after: 5
  {
  "offer": {
    "id": "7770273738"
  },
  "operation": {
    "id": "ef5dd966-d370-44f7-bb30-3631e3511536",
    "status": "IN_PROGRESS",
    "startedAt": "2024-06-30T08:11:36.000Z"
  }
 }
```

Gdy zakończymy przetwarzać operację, w odpowiedzi na żądanie [GET /sale/product-offers/{offerId}/operations/{operationId}](https://developer.allegro.pl/documentation#operation/getProductOfferProcessingStatus) wyślemy status HTTP 303 See Other, a w nagłówku Location przekażemy odnośnik kierujący do zasobu z danymi oferty.

Przykładowy request:

```
  curl -X GET
  'https://api.allegro.pl/sale/product-offers/7770273738/operations/eadb2e97-9850-4c51-bd27-68888b6d7d5d'
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
  HTTP/1.1: 303 See other
  location: https://api.allegro.pl/sale/product-offers/7770273738
```

Możesz teraz skorzystać z metody GET oraz otrzymanego odnośnika w nagłówku Location, aby uzyskać aktualne dane oferty. Utworzysz dzięki temu żądanie w następującej formie: [GET /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation#operation/getProductOffer).

Przykładowy request:

```
  curl -X GET
  'https://api.allegro.pl/sale/product-offers/7770273738'
  -H 'Authorization: Bearer {token}'
  -H 'Accept: application/vnd.allegro.public.v1+json'
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
```

```
{
    "name": "Ulefone Power telefon",
    "productSet": [
        {
            "product": {
                "id": "2f771572-8302-4c09-b304-391f039e3195",
                "publication": {
                    "status": "LISTED"
                },
                "parameters": [
                    {
                        "id": "246705",
                        "name": "Marka telefonu",
                        "values": [
                            "Ulefone"
                        ],
                        "valuesIds": [
                            "246705_598617"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202869",
                        "name": "Wbudowana pamięć",
                        "values": [
                            "512 GB"
                        ],
                        "valuesIds": [
                            "202869_214181"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202865",
                        "name": "Pamięć RAM",
                        "values": [
                            "16 GB"
                        ],
                        "valuesIds": [
                            "202865_214109"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "236462",
                        "name": "Średnica obiektywu",
                        "values": [
                            "8"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "224017",
                        "name": "Kod producenta",
                        "values": [
                            "test 1587459230"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202749",
                        "name": "Przekątna ekranu",
                        "values": [
                            "5.9"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202829",
                        "name": "Funkcje w telefonach komórkowych",
                        "values": [
                            "kalkulator"
                        ],
                        "valuesIds": [
                            "202829_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202685",
                        "name": "Typ",
                        "values": [
                            "Smartfon"
                        ],
                        "valuesIds": [
                            "202685_212929"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "127448",
                        "name": "Kolor",
                        "values": [
                            "biały"
                        ],
                        "valuesIds": [
                            "127448_2"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "4388",
                        "name": "System operacyjny",
                        "values": [
                            "Android"
                        ],
                        "valuesIds": [
                            "4388_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202717",
                        "name": "Pojemność akumulatora",
                        "values": [
                            "100"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "219",
                        "name": "Komunikacja",
                        "values": [
                            "Bluetooth"
                        ],
                        "valuesIds": [
                            "219_2"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202821",
                        "name": "Opcje SIM",
                        "values": [
                            "Dual SIM"
                        ],
                        "valuesIds": [
                            "202821_213909"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "246737",
                        "name": "Model telefonu",
                        "values": [
                            "Armor 24"
                        ],
                        "valuesIds": [
                            "246737_1785892"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "217",
                        "name": "Transmisja danych",
                        "values": [
                            "5G"
                        ],
                        "valuesIds": [
                            "217_2048"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202741",
                        "name": "Materiał",
                        "values": [
                            "aluminium"
                        ],
                        "valuesIds": [
                            "202741_1"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "227381",
                        "name": "Szerokość",
                        "values": [
                            "99"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "227357",
                        "name": "Wysokość",
                        "values": [
                            "11"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "245581",
                        "name": "Głębokość",
                        "values": [
                            "11"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202705",
                        "name": "Waga",
                        "values": [
                            "11"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "17448",
                        "name": "Waga produktu z opakowaniem jednostkowym",
                        "values": [
                            "11"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    },
                    {
                        "id": "202745",
                        "name": "Rodzaj wyświetlacza",
                        "values": [
                            "LCD IPS"
                        ],
                        "valuesIds": [
                            "202745_213201"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "202873",
                        "name": "Ekran dotykowy",
                        "values": [
                            "tak"
                        ],
                        "valuesIds": [
                            "202873_214265"
                        ],
                        "rangeValue": null
                    },
                    {
                        "id": "225693",
                        "name": "EAN (GTIN)",
                        "values": [
                            "0744861045021"
                        ],
                        "valuesIds": null,
                        "rangeValue": null
                    }
                ],
                "isAiCoCreated": false
            },
            "quantity": {
                "value": 1
            },
            "responsiblePerson": null
        }
    ],
    "parameters": [
        {
            "id": "11323",
            "name": "Stan",
            "values": [
                "Używany"
            ],
            "valuesIds": [
                "11323_2"
            ],
            "rangeValue": null
        }
    ],
    "images": [
        "https://a.allegroimg.allegrosandbox.pl/original/11ecc5/3c986dc84419b206015a2e6f1c65"
    ],
    "afterSalesServices": {
        "impliedWarranty": {
            "id": "f86078a6-9f42-4b76-9696-1e5c0646a60a"
        },
        "returnPolicy": {
            "id": "f54ba3c2-9710-4108-b275-28ee9be2b7b7"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "VAT"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": "12.43",
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 10,
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
        "handlingTime": "PT24H",
        "additionalInfo": null,
        "shipmentDate": null
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Produkt testowy</p><p>Cechy produktu:</p><ul><li> Typ:Smartfon</li> <li> Kolor: biały</li> <li> Przekątna ekranu: 5,9</li> <li> Rodzaj wyświetlacza: </li> <li> Wbudowana pamięć: 512 GB</li> <li> Pamięć RAM: 16 GB},{</li> </ul><p> </p>"
                    }
                ]
            }
        ]
    },
    "external": null,
    "category": {
        "id": "165"
    },
    "tax": null,
    "taxSettings": null,
    "sizeTable": null,
    "discounts": {
        "wholesalePriceList": null
    },
    "contact": null,
    "fundraisingCampaign": null,
    "messageToSellerSettings": null,
    "attachments": [],
    "b2b": null,
    "additionalServices": null,
    "compatibilityList": null,
    "additionalMarketplaces": {
        "allegro-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-sk": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-business-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        },
        "allegro-hu": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        }
    },
    "id": "7770273738",
    "language": "pl-PL",
    "publication": {
        "status": "ACTIVE",
        "duration": null,
        "endedBy": null,
        "endingAt": null,
        "startingAt": null,
        "republish": false,
        "marketplaces": {
            "base": {
                "id": "allegro-pl"
            },
            "additional": []
        }
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2024-06-30T08:11:36.862Z"
    },
    "createdAt": "2024-06-30T08:11:36.000Z",
    "updatedAt": "2024-06-30T08:11:41.714Z"
}
```

zamknij

Przykładowy response z aktywowaną ofertą

Aktywacja oferty może potrwać do dwóch godzin. W [tym artykule](https://help.allegro.com/pl/sell/a/w-jaki-sposob-sprawdzamy-oferty-ktore-wystawiasz-lub-wznawiasz-E7kGAnRAjhj) sprawdzisz, jakie dokładnie informacje weryfikujemy przed publikacją.

Znacznie przyśpieszysz czas publikacji, jeśli połączysz ofertę z produktem, który został już przez nas sprawdzony - jest w statusie “LISTED”. W [tym artykule](https://developer.allegro.pl/news/wyszukiwanie-i-tworzenie-produktow-wprowadzilismy-zmiany-zwiazane-ze-statusem-produktow-g0lbz9V6ds4) znajdziesz więcej informacji na ten temat.

#### Warianty testowe produktów

Lista wariantów produktów na Sandbox, które ułatwią Ci przeprowadzić różne testy dla różnych sytuacji, które możesz napotkać podczas wystawiania oferty z produktem:

- Produkt, którego podpięcie powoduje błąd parametrów własnych, jeżeli ich nie przekażesz (kod błędu OfferCustomParametersException): 5222c367-c86d-44d7-8840-c1adec7d4178.
- Produkt bez wypełnionego parametru wymaganego: df7e4db9-0dc6-4708-af86-84360469a152.
- 2 produkty z takimi samym numerem EAN: d7187e51-36cc-4999-861e-a4336aa165f0, 17ef2e7a-a759-42e9-84c2-93bf1a578ba6.
- Produkt bez uzupełnionego EAN: 8ff859fc-09fa-44f9-bada-0366126cb556.

### Jak przekazać własne wartości w żądaniu

Możesz rozszerzyć swój request, nadpisując wartości domyślne lub przekazując dodatkowe, niewymagane dane.

Przypomnijmy, że struktura żądania dzieli się na dwie części:

produktową - w której przekazujesz:

numer GTIN lub id produktu, jeżeli chcesz powiązać ofertę z produktem, który znajduje się w naszym Katalogu

komplet informacji o produkcie, jeżeli chcesz powiązać ofertę z produktem, którego nie ma w naszym Katalogu. Są to dane, które identyfikują określony produkt.

ofertową - dane, które określają warunki w konkretnej ofercie, np. cena, liczba sztuk, lokalizacja, informacje o fakturze, etc. Wartości związane z ofertą możesz nadpisać, a także dodać nowe. W dalszej części poradnika znajdziesz opis, jak to wykonać.

#### Tytuł oferty

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
  "productSet": [{
    "product": {
        "id": "5902719471797",
        "idType": "GTIN"
  }}],
  "name": "Mój własny tytuł",
  "sellingMode": {
    "price": {
      "amount": "220.85",
      "currency": "PLN"
    }
  },
  "stock": {
    "available": 1
  }
}'
```

zamknij

Przykładowy request z własnym tytułem

Do oferty automatycznie przypiszemy tytuł powiązany z nazwą produktu. Jeśli chcesz nadać swój własny, rozszerz request o pole name:

```
  ...
  "name": "Mój własny tytuł"
  ...  
```

Dla tytułu dopuszczamy maksymalnie 75 znaków oraz minimum 12 znaków ze spacjami i 3 słowa (3 ciągi znaków oddzielone spcjami). Listę liter, cyfr i znaków specjalnych jakie pozwalamy wprowadzić w tytule oferty znajdziecie poniżej.

```
Litery: 'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','w','v','x','y','z',
'ä','ö','ü','ø','ò','ß','0','á','č','ě','í','ř','š','ů','ú','ý','ž','œ','æ','à','â','ç','é','è','ê','ë','î',
'ï','ô','û','ù','ü','ÿ','€','×','ą','ć','ę','ł','ń','ó','ś','ź','ż','µ','⌀',

Cyfry: '0','1','2','3','4','5','6','7','8','9',

Znaki specjalne:'!','@','[',']','#','$','%','^','&','*','{','}','(',')','.',',','/','\\','|','?',' ',';','~','²','³',
'`','\'','’','´','\"','”','"','„','“','″','<','>','_','\t',':','-','=','+','0','…','–','°','°'
```

Niektóre litery jak i znaki specjalne są zamieniane na [encje](https://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references#Character_entity_references_in_HTML), dlatego zajmują więcej niż jeden znak. Przykładowo znak & jest encjonowany jako &amp; dlatego zajmuje 5 miejsc w tytule.

---

#### Parametry ofertowe

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/categories/{catId}/parameters'
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Accept-Language: pl-PL' \
  -H 'Authorization: Bearer {token}' \
```

```
  {
    "parameters": [                         // lista dostępnych parametrów dla
                                            wskazanej kategorii
    {
        "id": "11323",                      // unikalny identyfikator danego parametru
        "name": "Stan",                     // nazwa parametru
        "type": “dictionary”,               // typ parametru, obecnie mamy dostępne wartości:
                                            dictionary (słownik wyboru, może być jednokrotnego,
                                            bądź wielokrotnego wyboru, w zależności od wartości
                                            w polu multipleChoices), integer (liczba całkowita),
                                            float (liczby zmiennoprzecinkowe), string (możesz dodać
                                            jedną lub wiele wartości)
        "required":true,                    // informacja, czy dany parametr jest obowiązkowy,
                                            dostępne są dwie wartości: true (tak) i false (nie)
        "unit": null,
        "requiredForProduct": true          // czy musisz przekazać wartość dla tego
                                            parametru , gdy tworzysz nowy produkt,
        "requiredIf": null,                 // informacje o zależnej wymagalności parametru
        "displayedIf": null,                // informacje o zależnym wyświetlaniu parametru
        "options": {
            "variantsAllowed": false,
            "variantsEqual": false
            "ambiguousValueId": "216917_41" // id wartości niejednoznacznej, np.
                                            "inna", "pozostałe", etc.
            "dependsOnParameterId": null    // id parametru, od którego zależne są
                                            dostępne wartości tego parametru
            "describesProduct": true,       // czy parametr opisuje produkt
            "customValuesEnabled": false    // czy w danym parametrze możesz dodać własną wartość
                                            dla parametru z wartością niejednoznaczną
        },
        "dictionary": [
            {
                "id": "11323_1",
                "value": "Nowy",
                "dependsOnValueIds": []
            },
            {
                "id": "11323_2",
                "value": "Używany",
                "dependsOnValueIds": []
            }
        ],
        "restrictions": {
        "multipleChoices": false            // parametr z możliwym wyborem jednej lub
                                            wielu wartości, dostępne są dwie wartości:
                                            true (tak) i false (nie)
        }
    },
    {
        "id": "211966",
        "name": "Zakres regulacji wysokości koszenia (cm)",
        "type": "float",
        "required": false,
        "unit": null,
        "requiredForProduct": true,
        "restrictions": {
            "min": 0,
            "max": 1000,
            "range": true,                  // parametr zakresowy, należy podać
                                            minimalną i maksymalną wartość.
            "precision": 2
        }
    },
    {
        "id": "17448",
        "name": "waga (z opakowaniem)",
        "type": "float",
        "required":false,
        "restrictions": {
            "min": 5,
            "max": 10,
            "range": true,                  // parametr zakresowy. Sekcje range
                                            min i max oznaczają minalną i maksymalna
                                            wartość danego parametru.
            "precision": 3                  // określa z jaką dokładnością możemy podać
                                            wartość danego parametru. W tym przypadku
                                            możemy podać wartość z dokładnością do
                                            3 miejsc po przecinku
        }
    },
    {
        "id": "216917",
        "name": "Załączone wyposażenie",
        "type": "string",
        "required": false,
        "unit": null,
        "requiredForProduct": false,
        "options": {
            "variantsAllowed": false,
            "variantsEqual": false
            "ambiguousValueId": "216917_41" -- id wartości niejednoznacznej, np.
                                            "inna", "pozostałe", etc.
            "dependsOnParameterId": null,
            "describesProduct": true,
            "customValuesEnabled": false
        },
        "restrictions": {
            "minLength": 1,
            "maxLength": 40,
            "allowedNumberOfValues": 10     // informacja o tym, ile wartości możesz
                                            podać w danym parametrze
        }
    }
    ]
  }
```

zamknij

Przykładowy response dla parametrów

Za pomocą [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation/#operation/getFlatParametersUsingGET_2) pobierzesz parametry dostępne w danej kategorii. W odpowiedzi zwrócimy parametry, które możesz ustawić dla kategorii wskazanej jako categoryId.

##### Dbaj o aktualizację danych

Parametry pobieraj, sprawdzaj i aktualizuj, w szczególności te słownikowe, bo mogą zmieniać się ich wartości.

---

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
  "productSet": [{
    "product": {
        "id": "5902719471797",
        "idType": "GTIN"
   }}],
  "name": "Mój własny tytuł",
  "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
  "sellingMode": {
    "price": {
      "amount": "220.85",
      "currency": "PLN"
    }
  },
  "stock": {
    "available": 1
  }
}'
```

zamknij

Przykładowy request z uzupełnionym parametrem ofertowym

Parametry ofertowe są związane z indywidualną ofertą, np. stan, data ważności, etc., a nie z cechą konkretnego produktu. Informację o tym, które parametry są ofertowe, a które produktowe, znajdziesz w polu options.describesProduct:

- false - parametr ofertowy.
- true - parametr produktowy

Poniżej znajdziesz przykłady prawidłowo uzupełnionych struktur przykładowych parametrów, w zależności od ich typu:

dla parametrów słownikowych (wybór jednego lub wielu wartości z wielu):

```
  {
      "id": "209878",
      "valuesIds": [
      "209878_2",
      "209878_1"
      ],
      "values": [],
      "rangeValue": null
  }
```

dla parametrów zakresowych:

```
  {
      "id": "212570",
      "valuesIds": [],
      "values": [],
      "rangeValue": {
          "from": "80",
          "to": "100"
       }
  }
```

dla parametrów, w których samodzielnie uzupełniasz ich wartość:

```
  {
      "id": "216325",
      "valuesIds": [],
      "values": [
          "zielony",
          "żółty",
          "czerwony"
      ],
      "rangeValue": null
  }
```

Jeżeli chcesz zdefiniować np. stan produktu w ofercie jako używany, rozszerz swój request o poniższą strukturę:

```
  ...
    "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ]
  ...    
```

Zamiast identyfikatorów możesz skorzystać z nazw parametrów i ich wartości:

```
  ...
    "parameters": [
            "name": "Stan",
         {
           "values": [
                "Używany"
            ]
        }
    ]
  ...    
```

#### Czas trwania i wznowienie oferty

```
 curl -X POST
 'https://api.allegro.pl/sale/product-offers'
 -H 'Authorization: Bearer {token}'
 -H 'Accept: application/vnd.allegro.public.v1+json'
 -H 'Content-Type: application/vnd.allegro.public.v1+json'
 -d '{
   "productSet": [{
      "product": {
        "id": "5902719471797",
        "idType": "GTIN"
   }}],
   "name": "Mój własny tytuł",
   "parameters": [
         {
             "id": "11323",
             "valuesIds": [
                 "11323_2"
             ]
         }
     ],
   "sellingMode": {
     "price": {
       "amount": "220.85",
       "currency": "PLN"
     }
   },
   "stock": {
     "available": 1
   },
   "publication": {
     "duration": "P30D",
     "republish": true
   }
 }'
```

zamknij

Przykładowy request z ustawieniem czasu trwania

Jeżeli chcesz ustawić czas trwania oferty inny niż do wyczerpania zapasów, rozszerz swój request o pole publication.duration i wskaż jedną z dostępnych wartości czasu trwania oferty:

```
  ...
  "publication": {
    "duration": "P30D"
    ...
  },
  ...  
```

Dostępne wartości to:

- P30D (30 dni).
- P20D (20 dni)
- P10D (10 dni)
- P7D (7 dni)
- P5D (5 dni)
- P3D (3 dni)
- null (do wyczerpania zapasów),

Czas trwania możesz podać też w godzinach, np.: P72H (3 dni).

Aby oferta została automatycznie wznowiona po zakończeniu, przekaż wartość true w polu publication.republish. Pamiętaj, że możesz automatycznie wznowić ofertę i licytację:

ofertę wznowimy ze stałą początkową liczbą przedmiotów niezależnie od tego, ile przedmiotów sprzedasz

licytację wznowimy tylko, gdy nie zakończyła się sprzedażą.

#### Wystawienie oferty w przyszłości

```
 curl -X POST
 'https://api.allegro.pl/sale/product-offers'
 -H 'Authorization: Bearer {token}'
 -H 'Accept: application/vnd.allegro.public.v1+json'
 -H 'Content-Type: application/vnd.allegro.public.v1+json'
 -d '{
   "productSet": [{
        "product": {
            "id": "5902719471797",
            "idType": "GTIN"
   }}],
   "name": "Mój własny tytuł",
   "parameters": [
         {
             "id": "11323",
             "valuesIds": [
                 "11323_2"
             ]
         }
     ],
   "sellingMode": {
     "price": {
       "amount": "220.85",
       "currency": "PLN"
     }
   },
   "stock": {
     "available": 1
   },
   "publication": {
     "duration": "P30D",
     "startingAt ": "2021-01-20T08:56:00Z"
   }
 }'
```

zamknij

Przykładowy request z rozpoczęciem oferty w przyszłości

Jeśli chcesz zaplanować wystawienie oferty w przyszłości, rozszerz swój request o pole publication.startingAt i wskaż datę aktywacji:

```
  ...
  "publication": {
    "startingAt": "2021-01-20T08:56:00Z"
    ...
  },
  ...    
```

#### Lokalizacja i cenniki

##### Jak ustawić własny adres, z którego wysyłany jest przedmiot

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
  "productSet": [{
        "product": {
            "id": "5902719471797",
            "idType": "GTIN"
  }}],
  "name": "Mój własny tytuł",
  "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
  "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
   },
  "sellingMode": {
    "price": {
      "amount": "220.85",
      "currency": "PLN"
    }
  },
  "stock": {
    "available": 1
  }
}'
```

zamknij

Przykładowy request ze zmienioną lokalizacją

Jeżeli wysyłasz przedmioty z innego adresu, niż przypisany do twojego konta - przekaż odpowiednie wartości w poniższy sposób:

```
  ...
  "location": {
    "countryCode": "PL",
    "province": "LUBUSKIE",
    "city": "Gorzów Wielkopolski",
    "postCode": "66-400"
   }
  ...    
```

Listę dozwolonych wartości w polu location.province znajdziesz w [naszej dokumentacji](https://developer.allegro.pl/documentation/#operation/createOfferUsingPOST).

Jeśli chcesz zmienić adres przypisany do konta, skorzystaj z [naszej strony internetowej](https://allegro.pl/moje-allegro/moje-konto/dane-konta/zmien-dane-firmy).

##### Jak przypisać do oferty wybrany cennik dostawy

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
  "productSet": [{
    "product": {
        "id": "5902719471797",
        "idType": "GTIN"
  }}],
  "name": "Mój własny tytuł",
  "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "delivery": {
        "shippingRates": {
                "id": "c446793c-33f0-407f-b0ed-1aeec6090a7a"
    }
  },
  "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
   },
  "sellingMode": {
    "price": {
      "amount": "220.85",
      "currency": "PLN"
    }
  },
  "stock": {
    "available": 1
  }
}'
```

zamknij

Przykładowy request ze zmienionym cennikiem dostawy

Możesz ustawić dowolny cennik dostawy. Przykładowo - jeżeli posiadasz cennik o nazwie małe gabaryty i chcesz go użyć w ofercie, wystarczy, że rozszerzysz request o dodatkowe pole z:

nazwą cennika:

```
...
"delivery": {
  "shippingRates": {
      "name": "małe gabaryty"
  }
},
...    
```

lub identyfikatorem cennika:

```
...
"delivery": {
  "shippingRates": {
      "id": "c446793c-33f0-407f-b0ed-1aeec6090a7a"
  }
}
...    
```

Nazwę i ID swoich cenników sprawdzisz za pomocą [GET /sale/shipping-rates](https://developer.allegro.pl/documentation/#operation/getListOfShippingRatestUsingGET).

##### Jak przypisać do oferty wybrany cennik hurtowy

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
 -H 'Authorization: Bearer {token}'
 -H 'Accept: application/vnd.allegro.public.v1+json'
 -H 'Content-Type: application/vnd.allegro.public.v1+json'
 -d '{
    "productSet": [
        {
            "product": {
                "id": "5902719471797",
                "idType": "GTIN"
            }
        }
    ],
    "name": "Mój własny tytuł",
    "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
    },
    "sellingMode": {
        "price": {
            "amount": "220.85",
            "currency": "PLN"
        }
    },
    "stock": {
        "available": 1
    },
    "publication": {
        "duration": "P30D",
        "startingAt ": "2021-01-20T08:56:00Z"
    },
    "discounts": {
        "wholesalePriceList": {
            "id": "5637592a-0a24-4771-b527-d89b2767d821"
        }
    }
}'
```

zamknij

Przykładowy request ze zmienionym cennikiem hurtowym

Jeśli chcesz zaoferować rabat dla transakcji B2B (firma - firma), rozszerz swój request o pole discounts.wholesalePriceList.id, w którym podaj [wcześniej utworzony cennik hurtowy](https://developer.allegro.pl/tutorials/jak-zarzadzac-rabatami-promocjami-yPya2mj6zUP#cenniki-hurtowe) jako:

ID:

```
...
 “discounts”: {
     “wholesalePriceList”: {
         “id”: “5637592a-0a24-4771-b527-d89b2767d821”
     }
 },
...
```

lub nazwę:

```
...
 “discounts”: {
     “wholesalePriceList”: {
         “name”: “testowy cennik hurtowy”
     }
 },
...
```

#### Czas wysyłki

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
  "productSet": [{
        "product": {
            "id": "5902719471797",
            "idType": "GTIN"
  }}],
  "name": "Mój własny tytuł",
  "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
    },
        "handlingTime": "PT48H"
  },
  "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
   },
  "sellingMode": {
    "price": {
      "amount": "220.85",
      "currency": "PLN"
    }
  },
  "stock": {
    "available": 1
  }
}'
```

zamknij

Przykładowy request z innym czasem wysyłki

Aby wystawić przedmiot z czasem wysyłki innym niż 24H, ustaw w polu handlingTime w sekcji delivery wartość w formacie ISO 8601. Dostępne wartości to: PT0S (natychmiast), PT24H (24 godziny), P2D (2 dni), P3D (3 dni), P4D (4 dni), P5D (5 dni), P7D (7 dni), P10D (10 dni), P14D (14 dni), P21D (21 dni), P30D (30 dni), P60D (60 dni). Można również podać te wartości w godzinach, np. PT72H (3 dni).

Przykładowo, jeżeli chcesz ustawić czas wysyłki na 2 dni, prześlij w polu handlingTime wartość PT48H lub P2D:

```
  ...
  "delivery": {
    "handlingTime": "PT48H"
  }
  ...    
```

#### Dodatkowe informacje o dostawie

Rozszerz swój request o sekcję delivery z polem additionalInfo, aby uwzględnić w ofercie dodatkowe informacje o dostawie:

```
  ...
  "delivery": {
        "additionalInfo": "Dodatkowe informacje o dostawie"
   }
  ...     
```

#### Warunki reklamacji i zwrotów

##### Jak ustawić wybrane warunki reklamacji

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
  "productSet": [{
        "product": {
            "id": "5902719471797",
            "idType": "GTIN"
  }}],
  "name": "Mój własny tytuł",
  "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
        },
        "handlingTime": "PT48H",
        "additionalInfo": "Dodatkowe informacje o dostawie"
  },
  "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
   },
  "sellingMode": {
    "price": {
      "amount": "220.85",
      "currency": "PLN"
    }
  },
      "afterSalesServices": {
          "impliedWarranty": {
                  "name": "zabawki"
        }
    },
  "stock": {
    "available": 1
  }
}'
```

zamknij

Przykładowy request ze zmienioną reklamacją

Jeśli chcesz ustawić inne warunki reklamacji niż domyślne, użyj ich nazwy lub ID . Przykładowo, jeżeli posiadasz warunki reklamacji o nazwie zabawki, których ID to 913174eb-35ed-48df-b3b9-b9eb66b1b7a4 i chcesz użyć ich w ofercie, wystarczy, że rozszerzysz request o dodatkowe pole, w którym przekażesz:

nazwę warunków reklamacji:

```
...
"impliedWarranty": {
  "name": "zabawki"
}
...    
```

lub identyfikator warunków reklamacji:

```
...
"impliedWarranty": {
  "id": "913174eb-35ed-48df-b3b9-b9eb66b1b7a4"
}
...    
```

Nazwę oraz ID warunków reklamacji otrzymasz za pomocą [GET /after-sales-service-conditions/implied-warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET).

##### Jak ustawić wybrane warunki zwrotów

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
  "productSet": [{
        "product": {
            "id": "5902719471797",
              "idType": "GTIN"
  }}],
  "name": "Mój własny tytuł",
  "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
       },
        "handlingTime": "PT48H",
        "additionalInfo": "Dodatkowe informacje o dostawie"
  },
  "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
   },
  "sellingMode": {
    "price": {
      "amount": "220.85",
      "currency": "PLN"
    }
  },
      "afterSalesServices": {
        "impliedWarranty": {
            "name": "zabawki"
        },
        "returnPolicy": {
             "name": "30 dni"
        }
    },
  "stock": {
    "available": 1
  }
}'
```

zamknij

Przykładowy request ze zmienionymi warunkami zwrotów

Jeśli chcesz ustawić inne warunki zwrotów niż domyślne, użyj ich nazwy lub ID. Przykładowo - jeśli posiadasz warunki zwrotów o nazwie 30 dni o ID a375a08e-86ee-48a4-baf7-fabe01fe2631, to przekaż:

nazwę warunków zwrotu:

```
...
"returnPolicy": {
  "name": "30 dni"
}
...    
```

lub identyfikator warunków zwrotów:

```
...
"returnPolicy": {
  "id": "a375a08e-86ee-48a4-baf7-fabe01fe2631"
}
...    
```

Nazwę oraz ID warunków zwrotów otrzymasz za pomocą [GET /after-sales-service-conditions/return-policies](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceReturnPolicyUsingGET).

Warunkami reklamacji i zwrotów możesz zarządzać za pomocą dedykowanych zasobów. Więcej infromacji znajdziesz w naszych poradnikach:

- [jak zarządzać warunkami zwrotów](https://developer.allegro.pl/tutorials/jak-zarzadzac-ofertami-7GzB2L37ase#jak-zarzadzac-warunkami-zwrotow).
- [jak zarządzać warunkami reklamacji](https://developer.allegro.pl/tutorials/jak-zarzadzac-ofertami-7GzB2L37ase#jak-zarzadzac-warunkami-reklamacji),

#### Tabela rozmiarów

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
  "productSet": [{
        "product": {
            "id": "5902719471797",
            "idType": "GTIN"
  }}],
  "name": "Mój własny tytuł",
  "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "delivery": {
      "shippingRates": {
          "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
        },
      "handlingTime": "PT48H",
    "additionalInfo": "Dodatkowe informacje o dostawie"
  },
  "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
   },
  "sellingMode": {
    "price": {
      "amount": "220.85",
      "currency": "PLN"
    }
  },
      "afterSalesServices": {
        "impliedWarranty": {
            "name": "zabawki"
        },
        "returnPolicy": {
      "name": "30 dni"
  }
    },
  "stock": {
    "available": 1
  },
  "sizeTable": {
    "name": “Przykładowa tabela rozmiarów”
  }
}'
```

zamknij

Przykładowy request ze zdefiniowaną tabelą rozmiarów

Rozszerz swój request o sekcję sizeTable, aby dodać do oferty tabelę rozmiarów. Wystarczy, że w żądaniu przekażesz:

nazwę tabeli rozmiarów:

```
...
"sizeTable": {
  "name": “Przykładowa tabela rozmiarów”
}
...
```

lub identyfikator tabeli rozmiarów:

```
...
"sizeTable": {
  "id": “5727b598-6608-4bd3-b198-f165b011bb69”
}
...
```

Nazwy i identyfikatory swoich tabel rozmiarów sprawdzisz za pomocą [GET /sale/size-tables](https://developer.allegro.pl/documentation/#operation/getTablesUsingGET).

Tabelami rozmiarów możesz zarządzać za pomocą [dedykowanych zasobów](https://developer.allegro.pl/documentation/#tag/Size-tables).

#### Opcje faktury i stawki VAT

##### Jak zmienić opcje faktury

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
    "productSet": [{
       "product": {
          "id": "5902719471797",
      "idType": "GTIN"
    }}],
    "name": "Mój własny tytuł",
    "parameters": [{
        "id": "11323",
        "valuesIds": [
            "11323_2"
        ]
    }],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
        },
        "handlingTime": "PT48H",
        "additionalInfo": "Dodatkowe informacje o dostawie"
    },
    "sellingMode": {
        "price": {
            "amount": "220.85",
            "currency": "PLN"
        }
    },
    "afterSalesServices": {
        "impliedWarranty": {
            "name": "zabawki"
        },
        "returnPolicy": {
            "name": "30 dni"
        }
    },
    "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
    },
    "payments": {
        "invoice": "NO_INVOICE"
    },
    "stock": {
        "available": 1
    }
}'
```

zamknij

Przykładowy request ze zmianą dla faktury

Jeżeli nie wystawiasz faktury VAT, lub wystawiasz inną jej formę, możesz ustawić ją za pomocą pola payments.invoice:

```
  ...
  "payments": {
    "invoice": "NO_INVOICE"
  }
  ...    
```

Obecnie dostępne są 4 wartości:

- NO_INVOICE (nie wystawiam faktury).
- WITHOUT_VAT (faktura bez VAT)
- VAT_MARGIN (faktura VAT marża)
- VAT (faktura VAT)

##### Jak ustawić stawkę VAT na fakturze

```
curl -X POST 
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json' \
-H 'Content-Type: application/vnd.allegro.public.v1+json' \
-d '{
    "productSet": [
        {
            "product": {
                "id": "5902719471797",
                "idType": "GTIN"
            }
        }
    ],
    "name": "Mój własny tytuł",
    "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
        },
        "handlingTime": "PT48H",
        "additionalInfo": "Dodatkowe informacje o dostawie"
    },
    "sellingMode": {
        "price": {
            "amount": "220.85",
            "currency": "PLN"
        }
    },
    "afterSalesServices": {
        "impliedWarranty": {
            "name": "zabawki"
        },
        "returnPolicy": {
            "name": "30 dni"
        }
    },
    "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
    },
    "taxSettings": {
        "subject": "GOODS",
        "exemption": "MONEY_EQUIVALENT",
        "rates": [
            {
                "rate": "23.00",
                "countryCode": "PL"
            }
        ]
    },
    "publication": {
        "status": "ACTIVE"
    },
    "stock": {
        "available": 1
    }
}'
```

zamknij

Przykładowy request z zadeklarowaną stawką VAT

W ofercie możesz wskazać konkretną stawkę VAT, niezależnie od ustawionej opcji faktury.

Dostępne ustawienia i identyfikatory stawek VAT w danej kategorii sprawdzisz za pomocą [GET /sale/tax-settings?category.id={categoryId}](https://developer.allegro.pl/documentation/#operation/getTaxSettingsForCategory). W odpowiedzi zwrócimy stawki VAT dla wszystkich dostępnych krajów dostawy. Jeśli chcesz wyfiltrować wyniki, skorzystaj z opcjonalnego parametru “countryCode”, np. GET /sale/tax-settings?category.id=315261&countryCode=CZ

W poszczególnych kategoriach dostępne ustawienia VAT mogą się różnić. Dlatego sprawdzaj, jakie stawki VAT są dla danej kategorii dostępne.

---

Aby ustawić wybraną stawkę przekaż odpowiednią kombinację wartości pól taxSettings.subject, taxSettings.exemption oraz taxSetings.rates:

```
  ...
  "taxSettings": {
    "subject": "GOODS",
    "exemption": "MONEY_EQUIVALENT",
        "rates": [
        {
        "rate": "23.00", 
        "countryCode": "PL" 
         }
    ]
  }
  ...
```

#### Szkic oferty

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
    "productSet": [{
       "product": {
          "id": "5902719471797"
    }}],
    "name": "Mój własny tytuł",
    "parameters": [{
        "id": "11323",
        "valuesIds": [
            "11323_2"
        ]
    }],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
        },
        "handlingTime": "PT48H",
        "additionalInfo": "Dodatkowe informacje o dostawie"
    },
    "sellingMode": {
        "price": {
            "amount": "220.85",
            "currency": "PLN"
        }
    },
    "afterSalesServices": {
        "impliedWarranty": {
            "name": "zabawki"
        },
        "returnPolicy": {
            "name": "30 dni"
        }
    },
    "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
    },
    "payments": {
        "invoice": "NO_INVOICE"
    },
    "publication": {
        "status": "INACTIVE"
  },
    "stock": {
        "available": 1
    }
}'
```

zamknij

Przykładowy request z utworzeniem draftu

Jeżeli nie chcesz, aby oferta była aktywna po wysłanym żądaniu, rozszerz swój request o sekcję publication z polem status. Przekaż w nim wartość “INACTIVE”:

```
  ...
  "publication": {
    "status": "INACTIVE"
  }
  ...    
```

Maksymalnie możesz utworzyć 20 000 draftów. Po przekroczeniu limitu nie będziesz mógł utworzyć nowego draftu. Otrzymasz komunikat - “You cannot create new drafts - your account has exceeded the maximum number 20 000 of drafts.” Usuń niepotrzebne za pomocą [DELETE /sale/offers/{offerId}](https://developer.allegro.pl/documentation/#operation/deleteOfferUsingDELETE).

Draft oferty przechowujemy do 120 dni. Po tym okresie usuniemy taki draft. Jeśli go edytujesz, wydłużymy jego ważność o kolejne 120 dni.

---

#### Własne zdjęcia i opis oferty

##### Jak dodać własne zdjęcia do oferty

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
    "productSet": [{
       "product": {
          "id": "5902719471797"
    }}],
    "name": "Mój własny tytuł",
    "parameters": [{
        "id": "11323",
        "valuesIds": [
            "11323_2"
        ]
    }],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
        },
        "handlingTime": "PT48H",
        "additionalInfo": "Dodatkowe informacje o dostawie"
    },
    "sellingMode": {
        "price": {
            "amount": "220.85",
            "currency": "PLN"
        }
    },
    "afterSalesServices": {
        "impliedWarranty": {
            "name": "zabawki"
        },
        "returnPolicy": {
            "name": "30 dni"
        }
    },
    "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
    },
    "payments": {
        "invoice": "NO_INVOICE"
    },
    "publication": {
        "status": "INACTIVE"
  },
  "images": [
    "https://...zewnetrzny-adres-pierwszego-obrazka.jpeg",
    "https://...zewnetrzny-adres-drugiego-obrazka.jpeg"
  ],
    "stock": {
        "available": 1
    }
}'
```

zamknij

Przykładowy request ze zdjęciami

Do oferty automatycznie dołączymy zdjęcia produktu. Możesz także dodać swoje własne, które przedstawiają konkretny egzemplarz produktu. Aby załączyć do oferty własne zdjęcia, rozszerz swój request o sekcję images:

```
  ...
  "images": [
    "https://...zewnetrzny-adres-pierwszego-obrazka.jpeg",
    "https://...zewnetrzny-adres-drugiego-obrazka.jpeg"
  ]
  ...    
```

Jeśli chcesz w ofercie zaprezentować wyłącznie własne zdjęcia, bez obrazków, które pochodzą z naszego Katalogu, przekaż w polu product.images pustą tablicę:

```
  {
    "productSet": [
         {
                        "product": {
                            "id": "990de42f-8a68-4f0c-aedb-060141ffd8e3",
                            "images": []
                        }
        }],
    ...
    "images": [
            "https://...zewnetrzny-adres-pierwszego-obrazka.jpeg",
            "https://...zewnetrzny-adres-drugiego-obrazka.jpeg"
    ]
    ...
  }   
```

Jeśli nie przekażesz swojego [własnego opisu dla oferty](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#wlasne-zdjecia-i-opis-oferty), a produkt:

- rozpoznany przez nas na podstawie przekazanych danych (gdy nie podasz product.id)
- wskazany przez product.id lub

w naszym Katalogu go posiada i zawarte są w nim zdjęcia, to wraz z opisem do oferty przypiszemy zdjęcia produktu - nawet jeśli w sekcji product.images przekażesz pustą tablicę. Jeśli zatem chcesz, aby w ofercie były wyłącznie twoje zdjęcia, dodaj swój własny opis.

---

Zdjęcia mogą pochodzić z zewnętrznych serwerów, nie musisz ich wcześniej wysyłać na serwer Allegro. Każda oferta musi mieć minimum 1 zdjęcie. Maksymalna liczba zdjęć to 16.

---

Zdjęcia są cache’owane przez 7 dni - gdy wyślesz kolejne żądanie z tym samym, zewnętrznym adresem URL, zdjęcia możemy pobrać z wewnętrznego cache Allegro, zamiast bezpośrednio z zewnętrznego serwera.

Jeżeli chcesz, aby czas cache’owania był krótszy, serwer powinien wysłać nagłówek Cache-Control z odpowiednią wartością parametru max-age.

Jeżeli nie chcesz, abyśmy cache’owali zdjęcia, serwer powinien wysłać nagłówek Cache-Control z parametrem Private, No-Cache lub No-Store.

---

##### Jak dodać opis oferty

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
    "productSet": [{
       "product": {
          "id": "5902719471797"
    }}],
    "name": "Mój własny tytuł",
    "parameters": [{
        "id": "11323",
        "valuesIds": [
            "11323_2"
        ]
    }],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
        },
        "handlingTime": "PT48H",
        "additionalInfo": "Dodatkowe informacje o dostawie"
    },
    "sellingMode": {
        "price": {
            "amount": "220.85",
            "currency": "PLN"
        }
    },
    "afterSalesServices": {
        "impliedWarranty": {
            "name": "zabawki"
        },
        "returnPolicy": {
            "name": "30 dni"
        }
    },
    "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
    },
    "payments": {
        "invoice": "NO_INVOICE"
    },
    "publication": {
        "status": "INACTIVE"
    },
    "images": [
        "https://...zewnetrzny-adres-pierwszego-obrazka.jpeg",
        "https://...zewnetrzny-adres-drugiego-obrazka.jpeg"
    ],
    "description": {
        "sections": [{
            "items": [{
                "type": "TEXT",
                "content": "<p>Przykładowy opis oferty</p>"
            }]
        }]
    },
    "stock": {
        "available": 1
    }
}'
```

zamknij

Przykładowy request z własnym opisem

Do oferty możesz dodać swój własny opis. Przy jego braku do oferty automatycznie przypiszemy opis z produktu, który wskazałeś w żądaniu.

Aby dodać opis dodatkowy, rozszerz request o sekcję description:

```
  ...
  "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Przykładowy opis oferty</p>"
                    }
                ]
            }
        ]
    }
  ...    
```

Szczegółowe informacje o zasadach dla ofert znajdziesz na [stronie dla sprzedających](https://allegro.pl/pomoc/dla-sprzedajacych/abc-sprzedazy/jakie-sa-zasady-dotyczace-wystawiania-i-opisu-qzdAg29ZAIV).

Najważniejsze informacje

możesz korzystać tylko z określonych znaczników HTML:

- b - pogrubienie.
- li - element listy
- ol - wylistowanie
- ul - wypunktowanie
- p - akapit
- h2 - podtytuł
- h1 - tytuł

Jeśli chcesz ułatwić sobie pracę nad opisami ofert i produktów, skorzystaj z naszej publicznej biblioteki JavaScript - [convert-description](https://github.com/allegro/convert-description/), która konwertuje opis produktu i oferty w HTML do formatu wspieranego przez [Allegro REST API](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA). Udostępniamy także [live-demo](https://allegro.github.io/convert-description/) konwertera opisów.

Sugerujemy, by pierwszy opis przygotować przez formularz wystawiania. Skorzystaj z wszystkich rodzajów sekcji i opcji formatowania i pobierz ofertę za pomocą [GET /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/getProductOffer). W ten sposób najłatwiej dowiesz się jak poprawnie przygotować opis.

Jak wygląda struktura opisu

Sekcje (sections)

Opis oferty składa się z przynajmniej jednej sekcji, które umieszczasz w tablicy sections. Opis może mieć max. 100 sekcji.

```
    {
        "sections": [
            { section1 },
            { section2 },
             ...
            ]
    }
```

Elementy opisu (item)

Sekcje grupują elementy opisu (item) w widok kolumnowy:

jedna kolumna, która zajmuje całą szerokość ekranu

```
  {
       "items" : [
       { item1 }
       ]
  }
```

dwie kolumny, z których każda zajmuje połowę ekranu

```
  {
       "items" : [
       { item1 }
       { item2 }
       ]
  }
```

- nie możesz utworzyć sekcji z większą liczbą kolumn.
- w tekście enkoduj znaki specjalne, np.`/` wyślij w formie enkodowanej:`&#8725;`.

Typy treści w opisie

Tekst

```
    {
      "type": "TEXT",
      "content": "<p>opis tekstowy</p>"
    }
```

Możesz tu użyć określonych znaczników HTML:

- b - pogrubienie.
- li - element listy
- ol - wylistowanie
- ul - wypunktowanie
- p - akapit
- h2 - podtytuł
- h1 - tytuł

Najważniejsze zasady

Treści musisz umieścić w znacznikach HTML. W znacznikach HTML używaj tylko małych liter.

Poprawnie

```
{
  "type": "TEXT",
  "content": "<p>opis tekstowy</p>"
}
```

Niepoprawnie

```
{
  "type": "TEXT",
  "content": "opis tekstowy"
}
```

Nie możesz dodatkowo formatować tagów h1 i h2.

Poprawnie

```
{
   "type": "TEXT",
   "content": "<h1>Tytuł sekcji</h1>"
}
```

Niepoprawnie

```
{
  "type": "TEXT",
  "content": "<h1><b>Tytuł sekcji<b></h1>"
}
```

Możesz użyć pogrubienia < b > < /b > w znacznikach:

- < ol > < /ol > - lista numerowana
- < ul > < /ul > - lista wypunktowana
- < p > < /p > - akapit

Możesz użyć znacznika akapitu < p > < /p > w znacznikach:

- < ol > < /ol > - lista numerowana
- < ul > < /ul > - lista wypunktowana

Przykład, jak poprawnie łączyć znaczniki HTML:

```
    <h1>Lorem ipsum dolor sit amet, consectetur adipiscing elit</h1>
    <p><b>Aliquam vitae nisi ac lectus gravida rhoncus</b>. Vivamus egestas, orci quis
    fermentum sollicitudin, leo urna pellentesque quam, ut mattis risus nisl sed dolor.</p>
    <ul>
        <li><b>Nulla eu justo ut velit pellentesque porta.</b></li>
        <li>Pellentesque eget arcu id ligula consequat fermentum at nec velit. Maecenas vitae nunc
        non ante aliquet facilisis nec id leo.</li>
        <li>Sed vitae metus vel lorem iaculis rhoncus.</li> <li>Nullam nec felis felis.</li>
    </ul>
    <ol>
        <li><p><b>In eget vulputate purus</b></p></li>
        <li><p>Integer a pharetra odio.</p></li>
        <li><p>Vestibulum ut vestibulum diam.</p></li>
        <li><p>Phasellus quis tempor ipsum, at tincidunt nibh.</p></li>
        <li><p>Nulla sollicitudin, libero sit amet fermentum iaculis.</p></li>
    </ol>
```

Zdjęcie

```
    {
      "type": "IMAGE",
      "url": "https://...zewnetrzny-adres--obrazka.jpeg"
    }
```

Przykładowa struktura opisu

```
        {
            "sections": [{
            "items": [{
                "type": "TEXT",
                "content": "<p>tekstowy opis przedmiotu</p>"
            }]
        }, {
            "items": [{
                "type": "IMAGE",
                "url": "https://...zewnetrzny-adres-obrazka.jpeg"
            }]
        }, {
            "items": [{
                "type": "TEXT",
                "content": "<p>tekstowy opis przedmiotu</p>"
            }, {
                "type": "IMAGE",
                "url": "https://...zewnetrzny-adres-obrazka.jpeg"
            }]
        }, {
            "items": [{
                "type": "IMAGE",
                "url": "https://...zewnetrzny-adres-obrazka.jpeg"
            }, {
                "type": "IMAGE",
                "url": "https://...zewnetrzny-adres-obrazka.jpeg"
            }]
        }]
    }
```

#### Sygnatura

```
curl -X POST
'https://api.allegro.pl/sale/product-offers'
-H 'Authorization: Bearer {token}'
-H 'Accept: application/vnd.allegro.public.v1+json'
-H 'Content-Type: application/vnd.allegro.public.v1+json'
-d '{
    "productSet": [
        {
            "product": {
                "id": "5902719471797"
            }
        }
    ],
    "name": "Mój własny tytuł",
    "parameters": [
        {
            "id": "11323",
            "valuesIds": [
                "11323_2"
            ]
        }
    ],
    "delivery": {
        "shippingRates": {
            "id": "862347c4-b2b0-42d4-b84a-1db01509a69d"
        },
        "handlingTime": "PT48H",
        "additionalInfo": "Dodatkowe informacje o dostawie"
    },
    "sellingMode": {
        "price": {
            "amount": "220.85",
            "currency": "PLN"
        }
    },
    "afterSalesServices": {
        "impliedWarranty": {
            "name": "zabawki"
        },
        "returnPolicy": {
            "name": "30 dni"
        }
    },
    "location": {
        "countryCode": "PL",
        "province": "LUBUSKIE",
        "city": "Gorzów Wielkopolski",
        "postCode": "66-400"
    },
    "payments": {
        "invoice": "NO_INVOICE"
    },
    "publication": {
        "status": "INACTIVE"
    },
    "images": [
        "https://...zewnetrzny-adres-pierwszego-obrazka.jpeg",
        "https://...zewnetrzny-adres-drugiego-obrazka.jpeg"
    ],
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Przykładowy opis oferty</p>"
                    }
                ]
            }
        ]
    },
    "stock": {
        "available": 1
    },
    "external": {
        "id": "5AA43-2020"
    }
}'
```

zamknij

Przykładowy request z uzupełnioną sygnaturą

Sygnatura to zewnętrzny identyfikator, który nadaje sprzedający, np. aby powiązać ofertę z produktem w swoim magazynie. Możesz wprowadzić tutaj dowolny ciąg znaków. Jeśli chcesz dodać do oferty własną sygnaturę przedmiotu, rozszerz swój request o dodatkowe pole external.id:

```
  ...
  "external": {
        "id": “5AA43-2020”
   }
  ...  
```

#### Ważne informacje dla sprzedającego

W ofercie, w obiekcie "messageToSellerSettings" możesz określić, czy kupujący ma wprowadzić “Ważną wiadomości dla sprzedającego” w zamówieniu w formularzu dostawy i płatności. Wyświetlimy ją w polu "messageToSeller" po pobraniu zamówienia poprzez:

- [GET /order/checkout-forms/{id}](https://developer.allegro.pl/documentation/#operation/getOrdersDetailsUsingGET).
- [GET /order/checkout-forms](https://developer.allegro.pl/documentation/#operation/getListOfOrdersUsingGET)

W obiekcie "messageToSellerSettings", w polu "mode" możesz przekazać jedną z wartości:

- REQUIRED - wyświetlimy kupującemu pole “Ważne informacje dla sprzedającego” w formularzu dostawy i płatności - jego wypełnienie będzie dla kupującego obowiązkowe.
- HIDDEN - ukryjemy pole “Ważne informacje dla sprzedającego” w formularzu dostawy i płatności - kupujący nie będzie mógł wprowadzić żadnej wiadomości.
- OPTIONAL - wyświetlimy kupującemu pole “Ważne informacje dla sprzedającego” w formularzu dostawy i płatności, ale nie będzie musiał go uzupełniać.

Dla wartości REQUIRED musisz także uzupełnić podpowiedź dla kupującego w polu "hint".

```
{
  "id": "7276261934",
  "name": "iPhone",
   …
    "messageToSellerSettings": {
        "mode": "REQUIRED"                     // określ, czy “Ważna wiadomość do
                                                sprzedającego“ ma być wymagana
                                                (REQUIRED), opcjonalna (OPTIONAL), czy
                                                ukryta (HIDDEN),
       "hint": "Wybierz wzór"                   // podpowiedź dla kupującego - dostępna i
                                                wymagana tylko dla wartości REQUIRED w
                                                polu “mode“.
        }
   …
}
```

Z wartości REQUIRED skorzystasz tylko w niektórych kategoriach. Aby sprawdzić, czy jest to możliwe w wybranej kategorii, użyj [GET /sale/categories/{categoryId}](https://developer.allegro.pl/documentation/#operation/getCategoryUsingGET_1). W polu "options" we fladze "sellerCanRequirePurchaseComments" dla takiej kategorii zwrócimy wartość true.

Jeżeli nie przekażesz żadnej wartości w obiekcie "messageToSellerSettings" (lub przekażesz null) - domyślnie, wypełnienie “Ważnych informacji dla sprzedającego” przez Kupującego będzie opcjonalne.

#### Załączniki

Do ofert możesz dodawać załączniki w formatach: PDF, JPG, JPEG i PNG. Wyświetlimy je pod opisem oferty w sekcji Dodatkowe informacje. Załączników może być wiele - po jednym załączniku z listy:

- Przetwarzanie danych (urządzenie) (HARDWARE_DATA_PROCESSING) - PDF
- Przetwarzanie danych (oprogramowanie) (SOFTWARE_DATA_PROCESSING) - PDF
- Instrukcja dotycząca bezpieczeństwa (SAFETY_INFORMATION_MANUAL) - PDF
- Etykieta opony (TIRE_LABEL) - JPEG, JPG, PNG
- Karta produktu (PRODUCT_INFORMATION_SHEET) - PDF
- Etykieta energetyczną (ENERGY_LABEL) - JPEG, JPG, PNG
- Instrukcja gry (GAME_INSTRUCTIONS) - PDF
- Instrukcja montażu (INSTALLATION_INSTRUCTIONS) - PDF
- Instrukcja obsługi (USER_MANUAL) - PDF
- Fragment książki (BOOK_EXCERPT) - PDF
- Regulamin konkursu (COMPETITION_RULES) - PDF
- Regulamin promocji (SPECIAL_OFFER_RULES) - PDF
- Poradnik (MANUAL) - PDF

Jeśli chcesz dodać załącznik do oferty:

1. Przesłany załącznik [podłącz do oferty](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#podlacz-zalacznik-do-oferty).
2. Na ten URL [prześlij plik](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#przeslij-plik), który chcesz dodać do oferty,
3. [Stwórz obiekt załącznika](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#stworz-obiekt-zalacznika), dzięki czemu otrzymasz identyfikator załącznika oraz adres URL, na który wyślesz załącznik,

##### Stwórz obiekt załącznika

Aby dodać załącznik, najpierw musisz stworzyć na swoim koncie obiekt załącznika. Zrobisz to za pomocą [POST /sale/offer-attachments](https://developer.allegro.pl/documentation/#operation/createOfferAttachmentUsingPOST). Gdy utworzysz obiekt, będziesz miał:

- adres URL, za pomocą którego prześlesz plik na nasz serwer.
- identyfikator załącznika,

Przykładowy request:

```
  curl -X POST \
  'https://api.allegro.pl/sale/offer-attachments' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -H 'Authorization: Bearer {token}'
  -d '{
      "type": "SPECIAL_OFFER_RULES",                      // wymagany, rodzaj załącznika,
                                                          dostępne wartości MANUAL,
                                                          SPECIAL_OFFER_RULES,
                                                          COMPETITION_RULES,
                                                          BOOK_EXCERPT, USER_MANUAL,
                                                          INSTALLATION_INSTRUCTIONS,
                                                          GAME_INSTRUCTIONS,
                                                          ENERGY_LABEL,
                                                          PRODUCT_INFORMATION_SHEET,
                                                        SAFETY_INFORMATION_MANUAL
                                                          TIRE_LABEL.
      "file": {
        "name": "abcde.pdf"                               // wymagany, nazwa pliku, który dodasz,
    }
}'
```

Adres URL, za pomocą którego prześlesz plik na nasz serwer, znajdziesz w nagłówku response. Adres ten jest jednorazowy i unikalny. Jego format może zmieniać się w czasie, dlatego za każdym razem korzystaj z adresu z nagłówka. Nie składaj samodzielnie adresu z dostępnych elementów.

---

Przykładowy response

201 - created - obiekt załącznika utworzony prawidłowo

Nagłówek response'a:

```
    Location: http://upload.allegro.pl/sale/offer-attachments/e9d1bf7c-804e-4faf-9e24-b2d3aa3eda05
```

Body response'a:

```
  {
    "id": "e9d1bf7c-804e-4faf-9e24-b2d3aa3eda05",              // identyfikator draftu załącznika,
    "type": "SPECIAL_OFFER_RULES",                             // rodzaj załącznika,
    "file": {
        "name": "abcde.pdf"                                    // nazwa pliku, który dodasz,
    }
  }
```

##### Prześlij plik

Teraz możesz przesłać załącznik na nasz serwer. Do tego celu użyj adresu, który otrzymałeś w nagłówku odpowiedzi (w polu Location) na poprzednie wywołanie.

Przykładowy request:

```
  curl -X PUT \
  'http://upload.allegro.pl/sale/offer-attachments/{attachmentId}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/pdf' \
  -H 'Authorization: Bearer {token}'
  --data-binary "@abcde.pdf"                               // wymagany, zawartość pliku z
                                                           załącznikiem w postaci binarnej
```

Przykładowy response:

```
  {
    "id": "07ee5e36-afc7-41eb-af49-3df5354ef858",          // identyfikator draftu załącznika,
    "type": "SPECIAL_OFFER_RULES",                         // rodzaj załącznika,
    "file":
        "name": "abcde.pdf",                               // nazwa pliku, który dodasz,
        "url": {adres_pliku}                               // adres, pod którym jest dostępny
                                                           załącznik.
    }
  }
```

##### Podłącz załącznik do oferty

Uwzględnij załącznik w ofercie, rozszerz swój request o pole attachments, w którym podaj wcześniej otrzymany identyfikator.

```
    …
    "attachments": [
            {
                "id": "07ee5e36-afc7-41eb-af49-3df5354ef858"
            }
        ]
   …
```

Szczegółowe informacje o załączniku możesz zawsze pobrać korzystając z [GET /sale/offer-attachments/{attachmentId}](https://developer.allegro.pl/documentation#operation/getOfferAttachment).

#### Usługi dodatkowe

​​Aby uatrakcyjnić Twoje oferty, możesz skorzystać z usług dodatkowych, np. zapakowanie na prezent, wniesienie, montaż, itd. Więcej informacji znajdziesz w [Pomocy Allegro](https://allegro.pl/pomoc/dla-sprzedajacych/wystawianie-oferty-przez-formularz/wniesienie-montaz-i-inne-uslugi-dodatkowe-w-ofertach-xG71gnKLDCG).

Aby uwzględnić informację o usługach dodatkowych w ofercie, rozszerz swój request o pole additionalServices, w którym przekaż ID lub nazwę wybranej grupy usług dodatkowych:

```
    …
    "additionalServices":   {
                "id": "02ee5e36-afc7-41eb-afs9-3df5354ef818"
            }
   …
```

Więcej informacji o tym, jak zarządzać usługami dodatkowymi, znajdziesz w [naszym poradniku](https://developer.allegro.pl/tutorials/jak-zarzadzac-ofertami-7GzB2L37ase#jak-zarzadzac-uslugami-dodatkowymi).

#### Dane teleadresowe producenta

Aby dodać informację o danych teleadresowych producenta produktu, rozszerz request o pole "productSet.[].responsibleProducer", w którym wskaż:

“type” - typ identyfikatora, obecnie dostępne wartości: “ID”, "NAME";

dla typu "ID" podaj w polu "id" identyfikator danych producenta.

```
...
   "responsibleProducer": {
          "type": "ID",                                 // typ identyfikatora
          "id": "12345678-9abc-def1-2345-6789abcdef12"  // identyfikator danych producenta
   }
...
```

dla typu "NAME" podaj w polu "name" nazwę własną danych producenta.

```
...
  "responsibleProducer": {
         "type": "NAME",                               // typ identyfikatora
         "name": "Producent ABC"                       // nazwa własna danych producenta
  }
...
```

Identyfikatory i nazwy utworzonych na koncie danych teleadresowych producentów pobierzesz za pomocą [GET /sale/responsible-producers](https://developer.allegro.pl/documentation/#operation/responsibleProducersGET). Więcej informacji znajdziesz w [naszym poradniku](https://developer.allegro.pl/tutorials/jak-zarzadzac-kontem-danymi-uzytkownika-ZM9YAKgPgi2#dane-teleadresowe-producenta).

Gdy tworzysz draft oferty:

- możesz użyć globalnych, sugerowanych przez nas, danych producenta za pomocą [GET /sale/products](https://developer.allegro.pl/documentation#operation/getSaleProducts)- wyszukaj odpowiedni produkt i pobierz dane z pola products[].productSafety.
- i nie podasz nam danych producenta, wstawimy automatycznie sugerowane dane tylko pod warunkiem, jeśli dla danej marki posiadamy dokładnie jedne dane producenta,

#### Osoba odpowiedzialna za zgodność produktu z przepisami unijnymi

Aby dodać informację o podmiocie odpowiedzialnym za zgodność produktu z przepisami unijnymi, rozszerz request o pole productSet.[].responsiblePerson, w których wskaż:

ID podmiotu odpowiedzialnego:

```
…
"responsiblePerson":
{
      "id": "34c8ebb6-04d0-47be-bb20-426b7f69b9ab",
}
…
```

lub nazwę:

```
…
"responsiblePerson":
{
      "name": "responsible person",
}
…
```

Identyfikatory i nazwy utworzonych na koncie osób odpowiedzialnych za zgodność produktu z przepisami unijnymi pobierzesz za pomocą [GET /sale/responsible-persons](https://developer.allegro.pl/documentation#operation/responsiblePersonsGET). Więcej informacji znajdziesz w [naszym poradniku](https://developer.allegro.pl/tutorials/jak-zarzadzac-kontem-danymi-uzytkownika-ZM9YAKgPgi2#osoba-odpowiedzialna-za-zgodnosc-produktu-z-przepisami-unijnymi).

#### Informacje o bezpieczeństwie produktu

Aby dodać informację o bezpieczeństwie produktu, rozszerz request o pole "productSet.[].safetyInformation", w którym wskaż, czy dla danego produktu posiadasz informacje o bezpieczeństwie produktu. Dla każdego produktu musisz przekazać osobne dane.

Możesz zdefiniować jeden z trzech typów informacji:

- "ATTACHMENTS" - jeżeli dodajesz załączniki jako informacje o bezpieczeństwie produktu. Do każdego produktu możesz dodać maksymalnie 20 załączników.

```
{
  "productSet": [
    {
      "safetyInformation": {
         "type": "ATTACHMENTS",
         "attachments": [
               {
                 "id": "184e6fcc-db46-4727-b80c-2bb652d9b58b" // identyfikator załącznika (“SAFETY_INFORMATION_MANUAL”)
               }
         ]
      },
      ...
    }
  ],
  ...
}
```

Załączniki z informacją o bezpieczeństwie produktu (“SAFETY_INFORMATION_MANUAL”) dodasz w oparciu o zasób [POST /sale/offer-attachments](https://developer.allegro.pl/documentation/#operation/createOfferAttachmentUsingPOST).

“TEXT” - jeśli informacje o bezpieczeństwie produktu przekazujesz w postaci opisu tekstowego.

Opis tekstowy musi spełniać wymagania:

- dozwolone jest dodanie znaku nowej lini “\n”.
- nie obsługuje tagów HTML;
- dopuszczalna liczba znaków od 1 do 5000;

Wprowadzone informacje automatycznie przetłumaczymy na języki rynków, na których Twoja oferta będzie dostępna.

```
{
  "productSet": [
    {
      "safetyInformation": {
         "type": "TEXT",
         "description": "To jest informacja o bezpieczeństwie produktu.\n
          Jedná se o bezpečnostní informace o výrobku."
      },
      ...
    }
  ],
  ...
}
```

Gdy tworzysz draft oferty i wybierzesz produkt z naszego katalogu, automatycznie uzupełnimy w ofercie informacje o bezpieczeństwie, jeśli są uwzględnione po naszej stronie we wskazanym produkcie,

#### Kategorie podobne

```
  curl -X POST \
  'https://api.allegro.pl/sale/product-offers' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json'
  -d '{
  "productSet": [{
       "product": {
          "id": "5902719471797"
    }}],
  "category": {
        "id": "305121"                           // id kategorii podobnej, czyli jedna z
                                                wartości, którą zwróciliśmy w
                                                produkcie w liście category.similar
    },                               
  "sellingMode": {
    "price": {
      "amount": "29.01",
      "currency": "PLN"
    }
  },
  "stock": {
    "available": 199
  },
  "afterSalesServices": {
    "impliedWarranty": null,
    "returnPolicy": null,
    "warranty": null
  },
  "location": {
    "countryCode": "PL",
    "province": "KUJAWSKO_POMORSKIE",
    "city": "Żnin",
    "postCode": "88-400"
  },
  "parameters":[
      {
         "id":"11323",
         "valuesIds":[
            "11323_1"
         ]
      }
   ],
      "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Przykładowy opis</p>"
                    }
                ]
            }
        ]
    }
}'
```

zamknij

Przykładowy request z wykorzystaniem kategorii podobnej

Niektóre produkty pasują do wielu kategorii, dlatego możesz je wykorzystać, aby wystawić ofertę w jednej z kategorii podobnych.

Aby uzyskać zbiór kategorii podobnych - skorzystaj z [GET /sale/products/{productId}](https://developer.allegro.pl/documentation/#operation/getSaleProduct). W odpowiedzi zwrócimy listę category.similar, w której wskazujemy id kategorii podobnych.

Listy kategorii podobnych są definiowane przez nas - są one zwracane w odpowiedzi na [GET /sale/products/{productId}](https://developer.allegro.pl/documentation/#operation/getSaleProduct) i nie możesz tworzyć ich samodzielnie.

---

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/products/b2b61e23-b580-4471-b653-6ed25fd179f7' \
  -H 'Authorization: Bearer {token}' \
  -H 'accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response:

```
{
    "id": "b2b61e23-b580-4471-b653-6ed25fd179f7",
    "name": "BIO Pochodnia",
    "category": {
        "id": "261573",
        "similar": [
            {
                "id": "110914"
            },
            {
                "id": "305121"
            }
        ]
    }
…
}
```

Kategorie mogą różnić się dostępnymi w nich parametrami, dlatego część uzupełnionych w produkcie parametrów może nie być zgodna z tymi możliwymi do użycia w kategorii podobnej.

Użyj [GET ​/sale​/products​/{productId}?category.id={similarCategoryId}](https://developer.allegro.pl/documentation/#operation/getSaleProduct), a w parametrze category.id podaj jeden identyfikator ze zwróconego przez nas zbioru kategorii podobnych.

Dzięki temu wyfiltrujesz uzupełnione w produkcie parametry dla wybranej kategorii podobnej.

Aby wystawić ofertę z produktu w kategorii podobnej, rozszerz swoje żądanie w części ofertowej o pole category.id, w którym podasz identyfikator kategorii podobnej.

Jeżeli w żądaniu nie wskażesz konkretnego produkt w polu productSet[].product.id, możesz także przekazać id kategorii w części produktowej żądania. W przypadku, gdy dopasujemy na podstawie przesłanych parametrów istniejący produkt z naszego Katalogu Produktów - oferta zostanie wystawiona we wskazanej kategorii ze zbioru kategorii podobnych.

Jeżeli w odpowiedzi otrzymasz informację, aby uzupełnić brakujące parametry obowiązkowe, przekaż je w obiekcie product. Identyfikator parametru wraz z wartością sprawdzisz za pomocą [GET /sale/{categoryID}/parameters](https://developer.allegro.pl/documentation/#operation/getFlatParametersUsingGET_2).

### Jak utworzyć zestaw produktowy

Jak wspomnieliśmy na początku, endpoint [POST /sale/product-offers](https://developer.allegro.pl/documentation#operation/createProductOffers) pozwala na utworzenie zestawu produktowego.

Zestaw produktowy to oferta sprzedaży, która składa się z:

- Wielu sztuk jednego produktu (tzw. wielopak).
- Kilku różnych produktów (maksymalnie 10), np. konsola z dodatkową grą oraz dwoma padami.

Zestawy produktowe utworzysz wyłącznie za pomocą zasobów /sale/product-offers w wersji public.v1.

Zestawy zdefiniujesz na podstawie:

danych, które są potrzebne do utworzenia produktu (jeśli nie znajdziesz produktu w naszym Katalogu). W oparciu o nie przypiszemy do oferty:

- ID produktów z naszego Katalogu, które rozpoznaliśmy na podstawie przekazanych danych.
- ID utworzonych produktów

#### Jak utworzyć zestaw na podstawie produktów z naszego Katalogu

```
  curl -X POST
  'https://api.allegro.pl/sale/product-offers' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json' \
  -H 'Content-Type: application/vnd.allegro.public.v1+json' \
  -d '{
     "name": "Zestaw PlayStation 5 + Ratchet & Clank + 2pady",
     "productSet": [
        {
         "product": {"id": "7b167551-0c7d-42fd-ba39-102ac5e4efc7"}, 
        "quantity": {"value": 1}   // liczba sztuk wskazanego produktu, która 
                                   wejdzie w skład pojedynczego zestawu
        },
        {
        "product": {"id": "2903dd7e-4958-436c-8be0-491ea1ea0d85"},
          "quantity": {"value": 1}
        },
        {
        "product": {"id": "8487577e-e831-452c-83d7-d8b23b7fc1d3"}, 
          "quantity": {"value": 2} 
        }
     ],
     "sellingMode": {
       "price": {
          "amount": "4000.00",
          "currency": "PLN"
        }
      },
     "stock": {
       "available": 99
     }
  }'
```

zamknij

Przykładowy request z zestawem produktów

```
 {
    "id": "7680796491",
    "name": "Zestaw PlayStation 5 + Ratchet & Clank + 2pady",
    "productSet": [
        {
            "product": {
                "id": "7b167551-0c7d-42fd-ba39-102ac5e4efc7",
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
        },
        {
            "product": {
                "id": "2903dd7e-4958-436c-8be0-491ea1ea0d85",
                "publication": {
                    "status": "LISTED"
                }
            },
            "quantity": {
                "value": 1
            }
        },
        {
            "product": {
                "id": "8487577e-e831-452c-83d7-d8b23b7fc1d3",
                "publication": {
                    "status": "LISTED"
                }
            },
            "quantity": {
                "value": 2
            }
        }
    ],
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
            "id": "1377b0a6-b397-4e1e-b57c-4234bd84d036"
        },
        "returnPolicy": {
            "id": "e261d4ed-ced7-4c10-82cd-13aa26192895"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "VAT"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": 4000,
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 99,
        "unit": "UNIT"
    },
    "location": {
        "countryCode": "PL",
        "province": “WIELKOPOLSKIE”,
        "city": "Poznań",
        "postCode": "60-166"
    },
    "delivery": {
        "shippingRates": {
            "id": "0ef455de-fc6e-4d6e-a7c8-c22aecf0b914"
        },
        "handlingTime": "PT24H",
        "additionalInfo": null,
        "shipmentDate": null
    },
    "publication": {
        "duration": null,
        "status": "ACTIVE",
        "endedBy": null,
        "endingAt": null,
        "startingAt": null,
        "republish": false,
                "marketplaces": {
            "base": {
                "id": "allegro-pl"
            },
            "additional": []
        }
    },
        "additionalMarketplaces": {
        "allegro-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        }
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Opis oferty</p>"
                    }
                ]
            }
        ]
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2021-09-20T08:52:23.390Z"
    },
    "createdAt": "2021-09-20T08:52:23.000Z",
    "updatedAt": "2021-09-20T08:52:23.390Z",
    "images": [],
    "external": null,
    "category": {
        "id": "315569"
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

zamknij

Przykładowy response z zestawem produktów

Powyżej przedstawiliśmy przykład, jak utworzyć zestaw na podstawie produktów z naszego Katalogu, w którego skład wejdą:

- Kontroler Sony PS5 DualSense PAD Bezprzewodowy - 2 sztuki.
- Gra Ratchet & Clank: Rift Apart - 1 sztuka
- Konsola Sony PlayStation 5 Digital Edition - 1 sztuka

Aby to zrobić, skorzystaj z [POST /sale/product-offers](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA) i przekaż w polach:

- productSet.quantity.value - liczba sztuk wskazanego produktu, która wejdzie w skład pojedynczego zestawu.
- productSet.product.id - identyfikator lub GTIN produktu z naszego Katalogu.

Request uzupełnij o dane na temat ceny i liczby sztuk.

#### Jak utworzyć zestaw na podstawie własnych danych produktowych

```
 curl -X POST
 'https://api.allegro.pl/sale/product-offers' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \
 -H 'Content-Type: application/vnd.allegro.public.v1+json' \
 -d '
 {
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": "85",
            "currency": "PLN"
        }
    },
    "name": "Testowy produkt",
    "productSet": [{
        "product": {
            "name": "test 12333",
            "category": {
                "id": "79155"
            },
            "images": [    "adres obrazka"
            ],
            "parameters": [{
                    "id": "223545",
                    "values": [
                        "Świat Lodu i Ognia"
                    ]
                },
                {
                    "id": "223489",
                    "values": [
                        "Elio M. García. Jr.",
                        "George R. R. Martin",
                        "Linda Antonsson"
                    ]
                },
                {
                    "id": "75",
                    "valuesIds": [
                        "75_2"
                    ]
                },
                {
                    "id": "74",
                    "values": [
                        "2014"
                    ]
                },
                {
                    "id": "24648",
                    "valuesIds": [
                        "24648_1",
                        "24648_2"
                    ]
                },
                {
                    "id": "223333",
                    "values": [
                        "20.5"
                    ]
                },
                {
                    "id": "245669",
                    "values": [
                        "7860275839780"
                    ]
                },
                {
                    "id": "223541",
                    "valuesIds": [
                        "223541_303061"
                    ]
                }
            ]
        },
              "quantity": {
                "value": 1
             }
    },
    {
        "product": {
            "name": "Testowy produkt",
            "category": {
                "id": "79155"
            },
            "images": [ “adres obrazka”
            ],
            "parameters": [{
                    "id": "223545",
                    "values": [
                        "Ogień i krew"
                    ]
                },
                {
                    "id": "223489",
                    "values": [
                        "George R. R. Martin"
                    ]
                },
                {
                    "id": "75",
                    "valuesIds": [
                        "75_2"
                    ]
                },
                {
                    "id": "74",
                    "values": [
                        "2018"
                    ]
                },
                {
                    "id": "24648",
                    "valuesIds": [
                        "24648_1",
                        "24648_2"
                    ]
                },
                {
                    "id": "223333",
                    "values": [
                        "20.5"
                    ]
                },
                {
                    "id": "245669",
                    "values": [
                        "9788381164931"
                    ]
                },
                {
                    "id": "223541",
                    "valuesIds": [
                        "223541_303061"
                    ]
                }
            ]
        },
               "quantity": {
                 "value": 1
  }
    }],
    "stock": {
        "available": "10",
        "unit": "UNIT"
    }
  }'
```

zamknij

Przykładowy request z zestawem produktów

```
 {
    "id": "7680799058",
    "name": "Testowa oferta",
    "productSet": [
        {
            "product": {
                "id": "4f60d825-e031-49e8-a84e-1db17e0f6afd",
                "publication": {
                    "status": "PROPOSED"
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
        },
        {
            "product": {
                "id": "65d661be-c27d-4826-88ad-8ea1d8da5325",
                "publication": {
                    "status": "PROPOSED"
                }
            },
            "quantity": {
                "value": 1
            }
        }
    ],
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
            "id": "1377b0a6-b397-4e1e-b57c-4234bd84d036"
        },
        "returnPolicy": {
            "id": "e261d4ed-ced7-4c10-82cd-13aa26192895"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "VAT"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": 85,
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 10,
        "unit": "UNIT"
    },
    "location": {
        "countryCode": "PL",
        "province": “WIELKOPOLSKIE”,
        "city": "Poznań",
        "postCode": "60-166"
    },
    "delivery": {
        "shippingRates": {
            "id": "0ef455de-fc6e-4d6e-a7c8-c22aecf0b914"
        },
        "handlingTime": "PT24H",
        "additionalInfo": null,
        "shipmentDate": null
    },
    "publication": {
        "duration": null,
        "status": "ACTIVE",
        "endedBy": null,
        "endingAt": null,
        "startingAt": null,
        "republish": false,
                "marketplaces": {
            "base": {
                "id": "allegro-pl"
            },
            "additional": []
        }
    },
        "additionalMarketplaces": {
        "allegro-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        }
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Przykładowy opis</p>"
                    }
                ]
            }
        ]
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2021-09-21T12:19:24.585Z"
    },
    "createdAt": "2021-09-21T12:19:24.000Z",
    "updatedAt": "2021-09-21T12:19:24.598Z",
    "images": [
        "adres obrazka"
    ],
    "external": null,
    "category": {
        "id": "79155"
    },
    "taxSettings": null,
    "sizeTable": null,
    "discounts": {
        "wholesalePriceList": null
    },
    "contact": null,
    "b2b": {
        "buyableOnlyByBusiness": false
    }
 }
```

zamknij

Przykładowy response z zestawem produktów

Aby to zrobić, skorzystaj z [POST /sale/product-offers](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA) i w sekcji productSet.product, przekaż komplet danych, które opisują sprzedawane produkty. Więcej informacji, jak utworzyć nowy produkt, znajdziesz we [wcześniejszej części poradnika](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#jak-wystawic-oferte-z-nowym-produktem). Request uzupełnij o dane na temat ceny i liczby sztuk.

#### Jak utworzyć zestaw, który składa się z wielu sztuk jednego przedmiotu

```
  curl -X POST
 'https://api.allegro.pl/sale/product-offers' \
 -H 'Authorization: Bearer {token}' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \
 -H 'Content-Type: application/vnd.allegro.public.v1+json' \
 -d '
  {
   "name": "Tytuł oferty",
   "productSet": [
    {
     "product": {"id": "7b167551-0c7d-42fd-ba39-102ac5e4efc7"}, 
     "quantity": {"value": 5} 
    }
   ],
   "sellingMode": {
       "price": {
           "amount": "50.00",
           "currency": "PLN"
       }
   },
   "stock": {
       "available": 20
   }
  }'
```

zamknij

Przykładowy request z zestawem produktu

```
{
    "id": "7680796491",
    "name": "Tytuł oferty",
    "productSet": [
        {
            "product": {
                "id": "7b167551-0c7d-42fd-ba39-102ac5e4efc7",
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
        }
    ],
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
            "id": "1377b0a6-b397-4e1e-b57c-4234bd84d036"
        },
        "returnPolicy": {
            "id": "e261d4ed-ced7-4c10-82cd-13aa26192895"
        },
        "warranty": null
    },
    "payments": {
        "invoice": "VAT"
    },
    "sellingMode": {
        "format": "BUY_NOW",
        "price": {
            "amount": 4000,
            "currency": "PLN"
        },
        "startingPrice": null,
        "minimalPrice": null
    },
    "stock": {
        "available": 99,
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
            "id": "0ef455de-fc6e-4d6e-a7c8-c22aecf0b914"
        },
        "handlingTime": "PT24H",
        "additionalInfo": null,
        "shipmentDate": null
    },
    "publication": {
        "duration": null,
        "status": "ACTIVE",
        "endedBy": null,
        "endingAt": null,
        "startingAt": null,
        "republish": false,
        "marketplaces": {
            "base": {
                "id": "allegro-pl"
            },
            "additional": []
        }
    },
    "additionalMarketplaces": {
        "allegro-cz": {
            "sellingMode": null,
            "publication": {
                "state": "NOT_REQUESTED",
                "refusalReasons": []
            }
        }
    },
    "description": {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Opis oferty</p>"
                    }
                ]
            }
        ]
    },
    "validation": {
        "errors": [],
        "warnings": [],
        "validatedAt": "2021-09-20T08:52:23.390Z"
    },
    "createdAt": "2021-09-20T08:52:23.000Z",
    "updatedAt": "2021-09-20T08:52:23.390Z",
    "images": [],
    "external": null,
    "category": {
        "id": "315569"
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

zamknij

Przykładowy response z zestawem produktu

Aby to zrobić, skorzystaj z [POST /sale/product-offers](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA). Prócz danych produktu w sekcji productSet.product, przekaż także informację o liczbie sztuk danego przedmiotu - zrobisz to w polu productSet.quantity.value.

### Katalog Produktów

#### Jak znaleźć produkt

Skorzystaj w tym celu z [GET /sale/products](https://developer.allegro.pl/documentation/#operation/getSaleProducts). Jest to zasób, dzięki któremu wyszukasz produkty w Katalogu Allegro. W odpowiedzi otrzymasz listę dopasowanych produktów wraz z informacjami o:

- opisie produktu (jeśli jest załączony w produkcie).
- zdjęciach produktu
- podstawowych parametrach produktu
- kategorii produktu oraz kategoriach podobnych, w których także możesz wystawić dany produkt
- nazwie produktu
- identyfikatorze produktu

Dla tego zasobu obowiązuje [Dodatkowy limit liczby zapytań dla użytkownika](https://developer.allegro.pl/tutorials/q9ntbx-b21569boAI1#ograniczenie-liczby-zapytan-limity).

---

Cały czas pracujemy nad rozbudową naszego Katalogu produktów - aktualizujemy dane o produktach i rozszerzamy ją o kolejne kategorie.

Aby odnaleźć poszukiwany przez Ciebie produkt, skorzystaj z udostępnionych przez nas parametrów:

- filtry w danej kategorii.
- kategorie podobne (dodatkowy filtr, jeśli wyszukujesz po kategorii)
- kategoria
- język danych
- fraza i tryb wyszukiwania

Jeśli używasz znaków diakrytycznych, skorzystaj z kodowania znaków UTF-8.

---

##### Fraza i tryb wyszukiwania

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/products?phrase=888462600712&language=pl-PL&mode=GTIN \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

```
     {
 "products": [
  {
   "id": "5272069b-0759-4283-8ba7-7f05b416f1d9",        // identyfikator produktu - użyj go w ofercie,
                                                      //  by powiązać ją z produktem
   "name": "Smartfon Apple iPhone 6S srebrny 128 GB",   // nazwa produktu
   "category": {
    "id": "253002",                                     // kategoria produktu
    "path": [                                           // ścieżka kategorii głównej wskazanej 
                                                    //    w “category.id”
            {
                "id": "954b95b6-43cf-4104-8354-dea4d9b10ddf",
                "name": "Allegro"
            },
            {
                "id": "42540aec-367a-4e5e-b411-17c09b08e41f",
                "name": "Elektronika"
            },
            {
                "id": "4",
                "name": "Telefony i Akcesoria"
            },
            {
                "id": "165",
                "name": "Smartfony i telefony komórkowe"
            },
            {
                "id": "48978",
                "name": "Apple"
            },
            {
                "id": "253002",
                "name": "iPhone 6S"
            }
        ],
    "similar": [
            {
                "id": "316188",
                "path": [                                -- ścieżka kategorii podobnej wskazanej 
                                                        // w “category.similar.id”
                    {
                        "id": "954b95b6-43cf-4104-8354-dea4d9b10ddf",
                        "name": "Allegro"
                    },
                    {
                        "id": "42540aec-367a-4e5e-b411-17c09b08e41f",
                        "name": "Elektronika"
                    },
                    {
                        "id": "4",
                        "name": "Telefony i Akcesoria"
                    },
                    {
                        "id": "165",
                        "name": "Smartfony i telefony komórkowe"
                    },
                    {
                        "id": "48978",
                        "name": "Apple"
                    },
                    {
                        "id": "316188",
                        "name": "iPhone 12"
                    }
                ]
   },
   "parameters": [                                      // parametry produktu
    {
     "id": "224017",                                    // identyfikator parametru
     "name": "Kod producenta",                          // nazwa parametru
     "valuesLabels": [                                  // etykieta wartości parametru
      "MKQU2PM/A"
     ],
     "values": [
      "MKQU2PM/A"                                       // wartość parametru - dla typu string
     ],
     "unit": null,                                      // jednostka wartości parametru. Jeśli
                                                      //  dany parametr nie ma jednostki,
                                                      //  zwracamy wartość null
     "options": {
      "identifiesProduct": true                         // czy parametr identyfikuje produkt
     }                                                  
    },                                                  
    {
     "id": "127448",                                    // identyfikator parametru
     "name": "Kolor",                                   // nazwa parametru
     "valuesLabels": [                                  // etykieta wartości parametru
      "srebrny"
     ],
     "valuesIds": [                                     // identyfikator wartości parametru,
      "127448_8"                                       // dla typu słownikowego
     ],
     "unit": null,                                      // jednostka wartości parametru. Jeśli
                                                      //  dany parametr nie ma jednostki,
                                                     //   zwracamy wartość null
     "options": {
         "identifiesProduct": true
     }
    },
    {
     "id": "202733",                                    // identyfikator parametru
     "name": "Funkcje aparatu",                         // nazwa parametru
     "valuesLabels": [                                  // etykiety wartości parametrów
      "HDR",
      "autofocus",
      "lampa błyskowa",
      "panorama",
      "samowyzwalacz",
      "wykrywanie twarzy",
      "zdjęcia seryjne"
     ],
     "valuesIds": [                                     // identyfikatory wartości parametru,
      "202733_1024",                                    dla typu słownikowego wielowartościowego
      "202733_2",
      "202733_1",
      "202733_4",
      "202733_128",
      "202733_32",
      "202733_64"
     ],
     "unit": null,                                      // jednostka wartości parametru. Jeśli
                                                        dany parametr nie ma jednostki,
                                                        zwracamy wartość null
     "options": {
         "identifiesProduct": false
     }
    },
    {
    "id": "225693",                                     // identyfikator parametru
    "name": "EAN",                                      // nazwa parametru
    "valuesLabels": [
        "888462600712"                                  // etykieta wartości parametru
    ],
    "values": [
        "888462600712"                                  // wartość parametru
    ],
    "unit": null,
    "options": {
        "identifiesProduct": true,
        "isGTIN": true                                  // pole ma znaczenie przy sugerowaniu nowego
    }                                                   produktu, jeśli parametr ma wiele wartości,
                                                        możesz przekazać tylko jedną z nich  
    },
  ...
   ],
   "images": [                                          // zdjęcia produktu
    {
     "url": "https://a.allegroimg.com/original/00e0c9/1d7c95614fd6a7c713b075d0251a/
     Smartfon-Apple-iPhone-6S-srebrny-128-GB"
    }   
   ],
   "publication": {
           "status": "LISTED"         // status produktu. "PROPOSED" zwracamy dla 
                                       nowych propozycji produktów i produktów z katalogu, 
                                       które nie zostały przez nas sprawdzone, "LISTED" dla 
                                       produktów z katalogu, które zostały przez nas sprawdzone, 
                                       np. zweryfikowaliśmy, że podany numer GTIN znajduje się w oficjalnej bazie GS1
            },
   "aiCoCreatedContent": {               // informacja o tym, czy określona część produktu 
                                            (zwrócona w polu „paths”) została wygenerowana przez AI
        "paths": []
            },
    "trustedContent": {    // elementy danych produktów, które są zaufane
        "paths": [
            "images"
        ]
    }
     }]}
```

zamknij

Przykładowy response z listą produktów

Skorzystaj z [GET /sale/products](https://developer.allegro.pl/documentation/#operation/getSaleProducts) i podaj jako parametry:

Tryb wyszukiwania, dzięki któremu doprecyzujesz, czy podana przez Ciebie fraza to GTIN lub MPN. Pozwoli nam to lepiej dopasować wynik wyszukiwania. Parametr przyjmuje jedną z poniższych wartości:

- MPN - wyszukamy produkty, biorąc pod uwagę tylko przypisane do nich numery katalogowe producenta, np. w parametrze “Numer katalogowy części”.
- GTIN - wyszukamy produkty, biorąc pod uwagę tylko przypisane do nich numery GTIN.

Jeśli w parametrze phrase wskazujesz nazwę produktu, pozostaw mode puste.

Kategoria - w odpowiedzi, w sekcji "categories" znajdziesz informacje, ile wyników wyszukiwania znajduje się w danej kategorii. Możesz wykorzystać identyfikator danej kategorii, aby zawęzić wyniki wyszukiwania.

```
  GET https://api.allegro.pl/sale/products?phrase=Harry Potter i Książę Półkrwi&category.id=66781
```

Kategorie podobne - część kategorii posiada zbiór kategorii podobnych. Aby rozszerzyć wyszukiwanie produktów o zbiór kategorii podobnych, w parametrze searchFeatures przekaż wartość SIMILAR_CATEGORIES. Parametr możesz użyć tylko wtedy, gdy w tym samym requeście przekazujesz także parametr category.id.

```
  GET https://api.allegro.pl/sale/products?phrase=karta pamięci&category.id=16242&searchFeatures=SIMILAR_CATEGORIES
```

Liczbę wyników ze wszystkich kategorii zsumujemy dla kategorii podanej w parametrze category.id w polu categories.subcategories.count.

Jeżeli rozszerzysz swoje wyszukiwania o zbiór kategorii podobnych, nie otrzymasz w odpowiedzi filtrów. W związku z tym - nie skorzystasz z opcji filtrowania wyników.

Filtry - gdy szukasz produktu w danej kategorii, na końcu odpowiedzi - w sekcji “filters” - otrzymasz listę dostępnych filtrów. Dzięki nim możesz odpowiednio zawęzić wyniki wyszukiwania do swoich preferencji.

Lista filtrów:

Nie jest tożsama z wartościami, które otrzymasz dla GET /sale/categories/{categoryId}/parameters. Filtr tworzysz, podając identyfikator filtra i identyfikator szukanej wartości, na zasadzie {filter.id}={filter.value}.

Im niższy poziom drzewa, tym więcej filtrów możesz użyć.

Filtry działają tylko w tych kategoriach, dla których zostały zwrócone. Nie skorzystasz z filtrów bez podania kategorii.

W zapytaniu możesz podać wiele filtrów, traktujemy je jako połączone operatorem AND. W odpowiedzi zwrócimy produkty, które zawierają wszystkie wartości wskazane dla podanych filtrów.

Ignorujemy niepoprawnie użyte filtry - otrzymasz wyniki wyszukiwania, tak jakby błędny filtr nie został użyty.

Dla wartości filtrów słownikowych podajemy “count” - czyli liczbę produktów z daną wartością parametru:

Dla filtrów wykorzystanych w zapytaniu - “count” pozostaje bez zmian, czyli otrzymujesz liczbę przedmiotów dla każdej wartości filtra tak, jakby dany filtr nie był użyty.

Dla filtrów niewykorzystanych w zapytaniu - “count” przeliczymy, czyli otrzymasz liczbę produktów dla każdej wartości, która jest sumą spełniających aktualne warunki wyszukiwania i spełniających warunki wyszukiwania z użyciem konkretnej wartości.

#### Typy filtrów i stronicowanie

Dla [GET /sale/products](https://developer.allegro.pl/documentation/#operation/getSaleProducts) wyróżniamy następujące typy filtrów:

- MULTI - filtr dla parametrów wielokrotnego wyboru
- SINGLE - filtr dla parametrów pojedynczego wyboru

Filtr tworzysz podając identyfikator filtra i identyfikator szukanej wartości, na zasadzie {filter.id}={filter.value}.

Np. wyniki dla frazy iphone 6s chcesz zawęzić wg wbudowanej pamięci (filter.id=202869) o wartości 128 GB (filter.value=214189):

```
  GET https://api.allegro.pl/sale/products?phrase=iphone%206s&category.id=253002&202869=214189
```

Możesz podać wiele wartości dla wybranego filter.id, traktujemy je wtedy jako połączone operatorem OR - czyli zwracamy wszystkie produkty, które mają choć jedną ze wskazanych wartości.

- NUMERIC - filtr dla parametrów liczbowych Filtr tworzysz podając identyfikator filtra i zakres wartości w przyrostkach from i to, dla których chcesz otrzymać wyniki wyszukiwania, na zasadzie {filter.id}.from={value}&{filter.id}.to={value}.

Np. wyniki dla frazy Harry Potter chcesz zawęzić wg roku wydania (filter.id=74) od 2017 do 2019 roku:

```
  GET https://api.allegro.pl/sale/products?phrase=Harry%20Potter&category.id=66781&
  74.from=2017&74.to=2019
```

- NUMERIC_SINGLE - filtr dla parametrów zakresowych Filtr tworzysz podając identyfikator filtra i szukaną wartość, na zasadzie {filter.id}={value}.

Np. wyniki dla frazy “Kosiarka spalinowa” chcesz zawęzić do modeli z wysokością koszenia (filter.id=1117823) równą 5 cm:

```
  GET https://api.allegro.pl/sale/products?phrase=Kosiarka%20spalinowa&category.id=85213&1117823=5
```

Nie podawaj wielu wartości dla wybranego filter.id, nie otrzymasz wtedy poprawnych wyników.

---

Jeśli warunki wyszukiwania spełnia więcej niż 30 produktów, odpowiedź podzielimy na strony.

W pierwszej odpowiedzi otrzymasz identyfikator kolejnej strony, którą możesz otrzymać tworząc odpowiedni request:

```
  GET https://api.allegro.pl/sale/products?phrase=iphone%206s&category.id=253002&202869=214189
```

#### Jak pobrać pełne dane o produkcie

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/products/634238b1-4385-4de7-9c00-dfa49fce16ab?language=pl-PL' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

Przykładowy response ze szczegółami produktu

Skorzystaj w tym celu z [GET /sale/products/{productId}](https://developer.allegro.pl/documentation/#operation/getSaleProduct). Jako productId przekaż identyfikator [wyszukanego wcześniej](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#jak-znalezc-produkt) produktu. Dane produktu możesz otrzymać w różnych językach, dlatego korzystaj z parametru "language".

W odpowiedzi otrzymasz:

opcjonalnie:

- informację o specyfikacji TecDoc.
- sekcję ‘Pasuje do'
- opis produktu (jeśli jest do niego załączony)

Dla tego zasobu obowiązuje [Dodatkowy limit liczby zapytań dla użytkownika](https://developer.allegro.pl/tutorials/q9ntbx-b21569boAI1#ograniczenie-liczby-zapytan-limity).

---

#### Jak utworzyć nowy produkt

##### Sprawdź, czy w danej kategorii możesz dodać produkt

Wywołaj [GET /sale/categories/{categoryId}](https://developer.allegro.pl/documentation/#operation/getCategoryUsingGET_1), jeśli w odpowiedz otrzymasz "productCreationEnabled"=true, w danej kategorii możesz dodać produkt.

Pamiętaj, że ofertę możesz utworzyć w tzw. liściu, czyli w kategorii najniższego rzędu, którą oznaczamy "leaf": true.

##### Pobierz parametry, które możesz podać w produkcie

Przykładowy request:

```
  curl -X GET \
  'https://api.allegro.pl/sale/categories/165/parameters' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

```
  {
  …
  {
    "id": "224017",
    "name": "Kod producenta",
    "type": "string",
    "required": false,
    "unit": null,
    "requiredForProduct": true
    "options": {
        "variantsAllowed": false,
        "variantsEqual": false,
        "ambiguousValueId": null,
        "dependsOnParameterId": null,
        "describesProduct": true
    },
    "restrictions": {
        "minLength": 2,
        "maxLength": 35,
        "allowedNumberOfValues": 1
    }
 },
 {
    "id": "202685",
    "name": "Typ",
    "type": "dictionary",
    "required": true,
    "unit": null,
    "requiredForProduct": true
    "options": {
        "variantsAllowed": true,
        "variantsEqual": false,
        "ambiguousValueId": "202685_385861",
        "dependsOnParameterId": null,
        "describesProduct": true
    },
    "dictionary": [
        {
            "id": "202685_212929",
            "value": "Smartfon",
            "dependsOnValueIds": []
        },
        {
            "id": "202685_212933",
            "value": "Telefon komórkowy",
            "dependsOnValueIds": []
        },
        {
            "id": "202685_385861",
            "value": "inny",
            "dependsOnValueIds": []
        }
        ],
    "restrictions": {
        "multipleChoices": false
    }
  },
 ...
 }
```

zamknij

Przykładowy response z parametrami w podanej kategorii

Gdy wiesz już, w jakiej kategorii chcesz dodać produkt, wykorzystaj [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation/#operation/getFlatParametersUsingGET_2), by pobrać parametry dla tworzonego produktu. Wartość true w polu:

options.describesProduct - oznacza, że dany parametr jest produktowy i możesz go użyć.

requiredForProduct - oznacza, że musisz przekazać wartość dla danego parametru.

Przykładowy request dla kategorii [79153 - Fantasy](https://allegro.pl/kategoria/fantasy-science-fiction-horror-fantasy-79156):

```
  curl -X GET \
  'https://api.allegro.pl/sale/categories/79153/product-parameters' \
  -H 'Authorization: Bearer {token}' \
  -H 'Accept: application/vnd.allegro.public.v1+json'
```

```
 {
  "parameters": [                       // parametry dostępne dla produktu
    {
      "id": "223545",                   // identyfikator parametru
      "name": "Tytuł",                  // nazwa parametru
      "type": "string",                 // typ parametru - przykład dla typu string
      "required": true,                 // czy parametr jest wymagany, by utworzyć produkt
      "unit": null,                     // jednostka dla wartości parametru
      "restrictions": {                 // ograniczenia dla parametru typu string
        "minLength": 1,                 // minimalna liczba znaków
        "maxLength": 200,               // maksymalna liczba znaków
        "allowedNumberOfValues": 1      // ile wartości można podać dla danego parametru
      }
    },
  ...
    {
      "id": "75",                       // identyfikator parametru
      "name": "Okładka",                // nazwa parametru
      "type": "dictionary",             // typ parametru - przykład dla typu słownikowego
      "required": true,                 // czy parametr jest wymagany, by utworzyć produkt
      "unit": null,                     // jednostka dla wartości parametru
      "dictionary": [                   // wartości parametru słownikowego
        {
          "id": "75_1",                 // identyfikator wartości
          "value": "miękka"             // wartość
        },
        {
          "id": "75_314838",
          "value": "inna"
        }
      ],
      "restrictions": {                 // ograniczenia dla parametru typu słownikowego
        "multipleChoices": false        // czy dla danego parametru można przekazać wiele wartości
      }
    },
    {
      "id": "74",                       // identyfikator parametru
      "name": "Rok wydania",            // nazwa parametru
      "type": "integer",                // typ parametru - przykład dla typu integer
      "required": true,                 // czy parametr jest wymagany, by utworzyć produkt
      "unit": null,                     // jednostka dla wartości parametru
      "restrictions": {                 // ograniczenia dla parametru typu integer
        "min": 1400,                    // minimalna wartość
        "max": 2099,                    // maksymalna wartość
        "range": false                  // czy dla danego parametru można przekazać zakres wartości
      }
    },
  ...
    {
      "id": "223333",                   // identyfikator parametru
      "name": "Szerokość produktu",     // nazwa parametru
      "type": "float",                  // typ parametru - przykład dla typu float
      "required": false,                // czy parametr jest wymagany, by utworzyć produkt
      "unit": "cm",                     // jednostka dla wartości parametru
      "restrictions": {                 // ograniczenia dla parametru typu float
        "min": 1.0,                     // minimalna wartość
        "max": 250.0,                   // maksymalna wartość
        "range": false,                 // czy dla danego parametru można przekazać zakres wartości
        "precision": 2                  // określa dopuszczalną liczbę miejsc po przecinku,
                                        które można przekazać w wartości dla tego parametru
  }}]}
```

zamknij

Przykładowy response z parametrami produktowymi

Aby pobrać parametry potrzebne do utworzenia produktu, możesz także skorzystać z [GET /sale/categories/{categoryId}/product-parameters](https://developer.allegro.pl/documentation/#operation/getFlatProductParametersUsingGET).

##### Dodaj zdjęcia produktu

Przy pomocy [POST /sale/images](https://developer.allegro.pl/documentation/#operation/uploadOfferImageUsingPOST) prześlesz zdjęcie na nasze serwery protokołem HTTP lub HTTPS.

Zdjęcia możesz przesłać na dwa sposoby:

w postaci linku

w postaci binarnej.

W odpowiedzi otrzymasz adres zdjęcia. Do produktu musisz dodać co najmniej jedno zdjęcie, natomiast maksymalnie możesz dodać 16 zdjęć. Obowiązują [te same zasady](https://help.allegro.com/pl/sell/a/zasady-dla-zdjec-w-galerii-i-w-opisie-8dvWz3eo4T5?marketplaceId=allegro-pl), jak dla zdjęć w ofercie. Więcej informacji na ten temat znajdziesz w poradniku [Jak wystawić ofertę](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#wlasne-zdjecia-i-opis-oferty).

##### Opisz produkt

Podobnie jak dla oferty, dla produktu możesz przesłać również opis. Dla opisu obowiązują [te same zasady, jak dla oferty](https://help.allegro.com/pl/sell/a/jakie-sa-zasady-dotyczace-wystawiania-i-opisu-6M9EGaKm1SV?marketplaceId=allegro-pl). Tworzysz go też w identyczny sposób. Szczegółowe informacje o tym, jaka jest struktura opisu, z jakich elementów utworzyć opis oraz jakich znaków możesz użyć w opisie, znajdziesz w poradniku [Jak wystawić ofertę](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#wlasne-zdjecia-i-opis-oferty).

##### Dodaj propozycję produktu

```
curl -X POST \
 'https://api.allegro.pl/sale/product-proposals' \
 -H 'Authorization: Bearer {token}' \
 -H 'Content-Type: application/vnd.allegro.public.v1+json' \
 -H 'Accept: application/vnd.allegro.public.v1+json' \
 -d '{
    "name": "Świat Lodu i Ognia George R. R. Martin i inni", // wymagane, sugerowana nazwa produktu (max. 75 znaków)
    "category": {
        "id": "79157" // wymagane, identyfikator kategorii
    },
    "language": "pl-PL", // wymagane, język, w którym przesyłasz dane produktu
    "parameters": [ // wymagane, tablica parametrów produktu
        {
            "id": "223545", // wymagane, identyfikator parametru
            "values": [
                "Świat Lodu i Ognia" // wartość parametru typu string (na przykładzie tytułu)
            ]
        },
        {
            "id": "223489",
            "values": [ // wartości parametru typu string
                "Elio M. García. Jr.", //  z wieloma wartościami (na przykładzie autora)
                "George R. R. Martin",
                "Linda Antonsson"
            ]
        },
        {
            "id": "75",
            "valuesIds": [
                "75_2" // wartość parametru typu słownikowego (na przykładzie okładki)
            ]
        },
        {
            "id": "74",
            "values": [
                "2014" // wartość parametru typu integer (na przykładzie roku wydania)
            ]
        },
        {
            "id": "24648",
            "valuesIds": [ // wartość parametru typu słownikowego
                "24648_1", // wielowartościowego (na przykładzie wydania)
                "24648_2"
            ]
        },
        {
            "id": "223333",
            "values": [ // wartość parametru typu float
                "20.5" //  (na przykładzie szerokości produktu)
            ]
        },
        {
            "id": "245669", // parametr GTIN
            "name": "ISBN",
            "valuesLabels": [
                "9788380082434"
            ],
            "values": [
                "9788380082434" // wartość parametru GTIN (za pomocą 
                //  GET /sale/categories/{categoryId}/parameters sprawdź
                //  w polu requiredForProduct w parametrze GTIN, 
                //  czy musisz podać przynajmniej jeden numer GTIN)
            ],
            "unit": null,
            "options": {
                "identifiesProduct": true,
                "isGTIN": true
            }
        }
    ],
    "images": [ // wymagane conajmniej 1, zdjęcia produktu
        {
            "url": "https://a.allegroimg.com/original/03d68a/6092f8024506a01087c820e58f0c"
        }
    ],
    "description": { // opis produktu
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": "<p>Opis produktu</p>"
                    }
                ]
            }
        ]
    }
}}'
```

zamknij

Przykładowy request z propozycją produktu

Za pomocą zasobu [POST /sale/product-proposals](https://developer.allegro.pl/documentation/#operation/proposeSaleProduct) prześlesz propozycję produktu. Przesłane dane weryfikujemy, a zaakceptowane przez nas dane produktu są dostępne na platformie. Część danych może być weryfikowana automatycznie, część po pewnym czasie.

Gdy chcesz powiązać produkt z ofertą, skorzystaj z [GET /sale/products/{product.id}](https://developer.allegro.pl/documentation/#operation/getSaleProduct) i sprawdź, które dane produktu zaakceptowaliśmy i dzięki temu możesz je wykorzystać w ofercie.

Przygotuj następujące dane, by zaproponować produkt:

- (opcjonalnie) opis produktu
- zdjęcia
- parametry i wartości parametrów
- kategorię
- sugerowaną nazwę produktu
- język, w którym prześlesz dane produktu

i prześlij je za pomocą [POST /sale/product-proposals](https://developer.allegro.pl/documentation/#operation/proposeSaleProduct). W odpowiedzi otrzymasz identyfikator produktu.

Pole "name" to sugerowana nazwa produktu. W zależności od kategorii i podanych wartości parametrów nazwę produktu:

albo stworzymy automatycznie, na podstawie wartości przekazanych parametrów,

albo stworzymy na podstawie wartości podanej w polu name.

Nazwę utworzonego produktu otrzymasz w response.

##### Jak identyfikujemy duplikaty

Gdy tworzysz produkt sprawdzamy jego parametry i kod EAN. Jeśli zidentyfikujemy duplikat, w odpowiedzi otrzymasz status HTTP 409 - Conflict.

Adres istniejącego produktu otrzymasz w nagłówku Location.

---

##### Warunki i zasady dodawania produktu

Każde wywołanie zasobu [POST /sale/product-proposals](https://developer.allegro.pl/documentation/#operation/proposeSaleProduct) oznacza zgodę warunki i zasady dodawania produktu, które opisaliśmy w [Załączniku nr 10 Regulaminu Allegro](https://allegro.pl/regulamin/zalacznik/10).

#### Jak zgłosić błąd w produkcie

```
curl -X POST 'https://api.allegro.pl/sale/products/73b31ae5-18b0-4d25-8154-47f48a628365/change-proposals' \
- H 'Authorization: Bearer {token}' \
- H 'Accept: application/vnd.allegro.public.v1+json' \
- H 'Content-type: application/vnd.allegro.public.v1+json'
- d '{
    "name": "Harry Potter i kamień filozoficzny ilustrowana J.K. Rowling", // wymagane, nazwa produktu
    "category": {
        "id": "260395"
    },
    "parameters": [ // wymagane parametry oznaczone dla danej kategorii jako
        //  "requiredForProduct": true
        {
            "id": "1", // przykład dla wartości tekstowej
            "values": [
                "Harry Potter i kamień filozoficzny"
            ]
        },
        {
            "id": "2", // przykład dla wartości słownikowej
            "valuesIds": [
                "2_3"
            ]
        },
        {
            "id": "4", // przykład dla wartości zakresowej
            "rangeValue": {
                "from": "5",
                "to": "6"
            }
        },
        {
            "id": "7", // przykład dla wartości własnej spoza słownika
            "valuesIds": [
                "7_8"
            ],
            "values": [
                "Wartość własna spoza słownika"
            ]
        }
    ],
    "images": [ // wymagane co najmniej 1 zdjęcia produktu
        {
            "url": "https://a.allegroimg.com/original/003006/187e52b840ceac70c0782d2bceba"
        }
    ],
    "note": "Nazwa produktu jest niepoprawna, proszę o zmianę", // informacje dodatkowe dla osób weryfikujących zgłoszenia
    "notifyViaEmailAfterVerification": true, // czy chcesz otrzymać powiadomienie email po rozpatrzeniu sugestii
    "language": "pl-PL" // język dostarczanych danych w sugestii zmian w produkcie (obowiązkowy)
}'
```

zamknij

Przykładowy request z sugestią zmiany w produkcie

```
{
    "id": "96224dbf-64b5-46a3-9218-7376299a4051",                                   // identyfikator zgłoszenia
    "name": {
        "current": "Harry Potter i kamień filozoficzny",                            // aktualna nazwa produktu
        "proposal": "Harry Potter i kamień filozoficzny ilustrowana J.K. Rowling",              
                                                                                   // proponowana nazwa produktu
        "reason": "Oczekuje na weryfikację",                                        // komunikat o statusie zgłoszenia
        "resolutionType": "UNRESOLVED"                                              // status zgłoszenia
    },
    "images": [                                                                     // zdjęcia produktu
        {
            "current": null,
            "proposal": "https://a.allegroimg.com/original/003006/187e52b840ceac70c0782d2bceba",
            "reason": "Oczekuje na weryfikację",
            "resolutionType": "UNRESOLVED"
        },
        {
            "current": "https://a.allegroimg.com/original/116185/c482db7840d8bd3e3f0fc411b5e2",
            "proposal": null,
            "reason": "Oczekuje na weryfikację",
            "resolutionType": "UNRESOLVED"
        }
    ],
    "parameters": [],                                                              // parametry
    "category": null,
    "note": "Aktualne zdjęcie nie należy do tego produktu",                        // informacje dodatkowe od
                                                                                   zgłaszającego
    "notifyViaEmailAfterVerification": true,                                        // czy chcesz otrzymać powiadomienie
                                                                                    email po rozpatrzeniu sugestii
    "language": "pl-PL" -- język dostarczanych danych w sugestii zmian w produkcie                                                                                                                                            
}
```

zamknij

Przykładowy response z sugestią zmiany w produkcie

Za pomocą [POST /sale/products/{productId}/change-proposals](https://developer.allegro.pl/documentation/#operation/productChangeProposal) prześlesz sugestię zmiany w produkcie. Podaj swój docelowy wygląd produktu.

Dane, które musisz podać:

- zdjęcie - przynajmniej jedno.
- parametry - wszystkie wymagane w ramach kategorii, w której znajduje się produkt
- kategoria - zmiana kategorii wymaga podania wszystkich parametrów wymaganych w ramach tej nowej kategorii
- nazwa produktu

Aby wysłać sugestię zmiany w produkcie w innych językach niż polski, przekaż w obowiązkowym polu "language" preferowaną wartość, np. cs-CZ, en-US, pl-PL.

Zasób posiada dodatkowy limit - pojedynczy sprzedawca może zgłosić 100 sugestii w ciągu 1 dnia.

---

Przykładowy request:

```
curl -X GET \ 'https://api.allegro.pl.pl/sale/products/change-proposals/96224dbf-64b5-46a3-9218-7376299a4051' \
-H 'Authorization: Bearer {token}' \
-H 'Accept: application/vnd.allegro.public.v1+json'
```

```
 "id": "96224dbf-64b5-46a3-9218-7376299a4051",                                     // identyfikator zgłoszenia
    "name": {
        "current": "Harry Potter i kamień filozoficzny",                           // aktualna nazwa produktu
        "proposal": "Harry Potter i kamień filozoficzny ilustrowana J.K. Rowling", // proponowana nazwa produktu
        "reason": "Propozycja zaakceptowana",                                      // komunikat o statusie zgłoszenia
        "resolutionType": "ACCEPTED"                                               // status zgłoszenia, 
                                                                                      dostępne wartości: UNRESOLVED, 
                                                                                      ACCEPTED, REJECTED
    },
    "images": [                                                                    // zdjęcia produktu 
        {
            "current": null,
            "proposal": "https://a.allegroimg.com/original/003006/187e52b840ceac70c0782d2bceba",
            "reason": "Sugerowane zdjęcie jest zdjęciem ofertowym, nie produktowym",
            "resolutionType": "REJECTED"
        },
        {
            "current": "https://a.allegroimg.com/original/116185/c482db7840d8bd3e3f0fc411b5e2",
            "proposal": null,
            "reason": "Zdjęcie identyfikuje produkt, więc nie możemy go usunąć",
            "resolutionType": "REJECTED"
        }
    ],
    "parameters": [],                                                             // parametry
    "category": null,                                                             // kategoria
    "note": "Aktualne zdjęcie nie należy do tego produktu",                       // informacje dodatkowe od
                                                                                  zgłaszającego
    "notifyViaEmailAfterVerification": true,                                       // czy chcesz otrzymać powiadomienie
                                                                                  email po rozpatrzeniu sugestii
    "language": "pl-PL" -- język dostarczanych danych w sugestii zmian w produkcie                                                                                                                                                              
}
```

zamknij

Przykładowy response ze statusem zgłoszenia

Aby sprawdzić status zgłoszenia, skorzystaj z [GET /sale/products/change-proposals/{id}](https://developer.allegro.pl/documentation/#operation/getProductChangeProposal).

### Obsługa błędów

#### Metadane

##### PARAMETER_MISMATCH

Jednym z częstych błędów podczas wystawiania oferty produktu jest rozbieżność między częścią parametrów, które do nas wysyłasz, a danymi produktu w Katalogu Allegro. Sytuacja taka może mieć miejsce gdy na podstawie przesłanych przez Ciebie danych rozpoznaliśmy istniejący produkt.

Aby łatwiej sięgnąć po dane produktu, którego błąd dotyczy i zaprezentować je sprzedającemu, skorzystaj z danych, które zwracamy w obiekcie “metadata”:

- expectedParameterValue - nazwa oczekiwanej, uwzględnionej w produkcie z katalogu, wartości parametru
- expectedParameterValueId - ID oczekiwanej, uwzględnionej w produkcie z katalogu, wartości parametru (dotyczy tylko parametrów typu słownikowego)
- currentParameterValue - nazwa wysłanej wartości parametru
- currentParameterValueId - ID wysłanej wartości parametru (dotyczy tylko parametrów typu słownikowego)
- parameterName - nazwa parametru, którego dotyczy błąd
- parameterId - ID parametru, którego dotyczy błąd
- productId - ID odnalezionego produktu z katalogu

Przykład errors.metadata w przypadku rozbieżności parametrów typu string, gdzie sam wprowadzasz wartość:

```
"metadata": {
                "productId": "04ee251b-8979-40f4-a2da-b331987a0a0a",
                "parameterId": "219781",
                "parameterName": "Dedykowany model",
                "currentParameterValue": "MOTOROLA EDGE 20 PRO 5G",
                "expectedParameterValue": "MOTOROLA G73"
  }
```

Przykład errors.metadata w przypadku rozbieżności parametrów typu słownikowego:

```
"metadata": {
                "productId": "04ee251b-8979-40f4-a2da-b331987a0a0a",
                "parameterId": "219781",
                "parameterName": "Materiał dominujący",
                "currentParameterValueId": "236902_406918",
                "currentParameterValue": "nylon",
                "expectedParameterValueId": "236902_406926",
                "expectedParameterValue": "poliamid"
  }
```

Przykład errors.metadata w przypadku rozbieżności parametrów typu zakresowego:

```
"metadata": {
                "productId": "04ee251b-8979-40f4-a2da-b331987a0a0a",
                "parameterId": "219781",
                "parameterName": "Wysokośc",
                "currentParameterValue": "121, 121",
                "expectedParameterValue": "112, 121"
  }
```

##### DictionaryParameterValueNotFound

Błąd ten zwrócimy, jeśli dla danego parametru, w polu “values”, wskażesz nam wartość, która nie występuje w słowniku dostępnych wartości.

Aby łatwiej sięgnąć po dane, które generują problem, skorzystaj z wartości, które zwracamy w obiekcie metadata:

- requestedDictionaryValue - błędna wartość przekazana przez sprzedającego
- parameterName - nazwa parametru, którego dotyczy błąd
- parameterId - ID parametru, którego dotyczy błąd

Przykład errors.metadata w przypadku wartości parametru “Stan”, która nie występuje w słowniku:

```
            "metadata": {
                "parameterId": "11323",
                "parameterName": "Stan",
                "requestedDictionaryValue": "Po zwrocie"
            }
```

##### DictionaryParameterIdNotFound

Błąd ten zwrócimy, jeśli dla danego parametru, w polu “valuesIds”, wskażesz nam ID wartości, która nie występuje w słowniku dostępnych wartości.

Aby łatwiej sięgnąć po dane, które generują problem, skorzystaj z wartości, które zwracamy w obiekcie metadata:

- requestedDictionaryValueId - błędny ID wartości przekazany przez sprzedającego
- parameterName - nazwa parametru, którego dotyczy błąd
- parameterId - ID parametru, którego dotyczy błąd

Przykład errors.metadata w przypadku ID wartości parametru “Stan”, która nie występuje w słowniku:

```
           "metadata": {
                "parameterId": "11323",
                "parameterName": "Stan",
                "requestedDictionaryValueId": "11323_3"
            }
```

#### Najczęstsze błędy

opis błędu / rozwiązanie

Nie możesz wystawić oferty bez powiązanego produktu w tej kategorii. Wybierz z katalogu lub utwórz nowy produkt i połącz go ze swoją ofertą.

opis błędu / rozwiązanie

Nie odnaleźliśmy produktu dla wskazanego identyfikatora w polu [product.id](http://product.id/). Wyszukaj prawidłowy produkt za pomocą [GET /sale/products](https://developer.allegro.pl/documentation#operation/getSaleProducts) i uwzględnij go w ofercie.

opis błędu / rozwiązanie

Wskazujesz GTIN, dla którego posiadamy więcej niż jeden produkt. Za pomocą [GET /sale/products](https://developer.allegro.pl/documentation#operation/getSaleProducts) wyszukaj produkty, jakie kryją się pod danym GTIN i pobierz ID wybranego produktu. ID wstaw w polu [product.id](http://product.id/), a pole "idType" usuń lub przekaż w nim null.

opis błędu / rozwiązanie

Nie udało nam się wyszukać konkretnego produktu i uwzględnić go w ofercie na podstawie wskazanego numeru GTIN oraz parametrów. Uzupełnij brakujące parametry wskazane w "message".

opis błędu / rozwiązanie

Nie udało się utworzyć produktu na podstawie wskazanego numeru GTIN. Usuń pole "product.id" i "product.idType" i spróbuj utworzyć nowy produkt.

opis błędu / rozwiązanie

Nie możesz wystawić oferty produktu wskazanej marki, jest ona przez nas zablokowana. Jeśli chcesz dowiedzieć się więcej szczegółów, skorzystaj z [formularza kontaktowego.](https://allegro.pl/pomoc/kontakt?srsltid=AfmBOorgCsPsNSG7goo1oxsMHAj2VsVHtNNWty5KEGiiARrrlMG8RHfv)

opis błędu / rozwiązanie

Na konto użytkownika, które próbuje wystawić ofertę, została nałożona blokada. Aby uzyskać więcej szczegółów, skontaktuj się z obsługą za pomocą [formularza](https://allegro.pl/pomoc/kontakt).

opis błędu / rozwiązanie

Na konto użytkownika, które próbuje utworzyć nowy produkt, została nałożona blokada. Aby uzyskać więcej szczegółów, skontaktuj się z obsługą za pomocą [formularza](https://allegro.pl/pomoc/kontakt).

opis błędu / rozwiązanie

Posiadasz już 5 ofert danego produktu, nie możesz utworzyć kolejnej lub edytować aktualnej. Więcej informacji na ten temat znajdziesz [w newsie](https://allegro.pl/pomoc/aktualnosci/od-16-pazdziernika-polaczysz-maksymalnie-5-ofert-z-tym-samym-produktem-z-katalogu-eKaE250LPCq#:~:text=2023%2C%2008%3A29-,Od%2016%20pa%C5%BAdziernika%20po%C5%82%C4%85czysz%20maksymalnie%205%20ofert%20z%20tym%20samym,5%20ofert%20ze%20stanem%20Nowy.).

opis błędu / rozwiązanie

Konto osiągnęło już maksymalny limit draftów ofert (20 000). Usuń część z nich za pomocą [DELETE /sale/offers/{offerID}](https://developer.allegro.pl/documentation#operation/deleteOfferUsingDELETE), aby móc utworzyć nowe.

opis błędu / rozwiązanie

Nie możesz mieć więcej niż 30 000 aktywnych ofert B2B. Zakończ istniejącą ofertę dla biznesu przed wystawieniem nowej.

opis błędu / rozwiązanie

Nie możesz wystawiać ofert w tej kategorii. Aby otrzymać więcej szczegółów, skontaktuj się przez [formularz kontaktowy](https://allegro.pl/pomoc/kontakt?srsltid=AfmBOorgCsPsNSG7goo1oxsMHAj2VsVHtNNWty5KEGiiARrrlMG8RHfv).

opis błędu / rozwiązanie

Wysyłasz w zapytaniu nadmiarowe pola, które nie są opisane w dokumentacji. Szczegółowe informacje znajdziesz w polu "metadata". Usuń niepotrzebne pola.

opis błędu / rozwiązanie

Próbujesz utworzyć nowy produkt, jednak nie przekazujesz nam nazwy. Uzupełnij ją w polu productSet.product.name.

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

Nie przekazano ID kategorii, w której chcesz wystawić ofertę produktu. Listę dostępnych kategorii pobierzesz za pomocą [GET /sale/categories](https://developer.allegro.pl/documentation#operation/getCategoriesUsingGET), możesz również z zasobu, w którym podpowiadamy kategorię na podstawie wskazanej frazy - [GET /sale/matching-categories](https://developer.allegro.pl/documentation#operation/categorySuggestionUsingGET).

opis błędu / rozwiązanie

Na podstawie przekazanych danych wykryliśmy istniejący produkt w naszym Katalogu i próbujemy uwzględnić go ofercie. Jest to jednak niemożliwe ze względu na rozbieżność między danymi wskazanymi przez sprzedawcę, a danymi w katalogu. W takiej sytuacji możesz poprawić dane w swoim żądaniu lub - jeśli jesteś pewien, że Twoje wartości są prawidłowe - zgłosić sugestię zmiany danych w produkcie.

opis błędu / rozwiązanie

Przekazano błędny numer [GTIN](https://help.allegro.com/sell/pl/a/parametry-w-allegro-aMZKj37Vauq?marketplaceId=allegro-pl#czym-jest-ean-gtin). Wskaż prawidłowy numer, który istnieje w bazie GS1.

opis błędu / rozwiązanie

Błąd walidacji danych produktu, zwróć uwagę na dokładną treść zwróconą w "message".

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

Nie udało się pobrać zdjęć z danych oferty. Upewnij się, że linki przekazane w sekcji "images" są poprawne i spróbuj ponownie.

opis błędu / rozwiązanie

Przekroczono limit zdjęć w galerii, maksymalnie w ofercie możesz uwzględnić 16 zdjęć (wliczając w to zdjęcia z produktu). Więcej o zasadach dla zdjęc przeczytasz [w naszym poradniku](https://developer.allegro.pl/tutorials/jak-jednym-requestem-wystawic-oferte-powiazana-z-produktem-D7Kj9gw4xFA#wlasne-zdjecia-i-opis-oferty).

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

Błąd walidacji danych w ofercie, najczęściej dotyczy braku lub błędnej ceny w ofercie. Upewnij się, że tę wartość przesyłasz poprawnie.

opis błędu / rozwiązanie

Przekazano ujemną liczby sztuk. Musi ona być równa 0 lub większa - popraw wartość w polu "stock.available".

| error code | opis błędu / rozwiązanie |
| --- | --- |
| "ConstraintViolationException.ProductizationMinLimitReached" |
| "ProductNotFoundException" |
| "MultipleProductsFoundException" |
| "DuplicateDetectionMissingParametersException" |
| "MatchingProductForDataNotFoundException" |
| "brandBlock" |
| "ConstraintViolationException.NoSellBlockades" |
| "SellerAccountWithSellBlockadeException" |
| "offerCounter" |
| "ConstraintViolationException.MaxInactiveOffers" |
| "B2B_OFFER_LIMIT_EXCEEDED" |
| "ConstraintViolationException.CategorySellingRestrictions" |
| "UnknownJSONProperty" |
| "RequiredProductName" |
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
| "MissedCategoryIdException" |
| "ProductConstraintViolationException.DataIntegrity" |
| "ConstraintViolationException.GtinNotExistsInGtinParameter" |
| "ProductValidationException" |
| "ProductLanguageVersionUnavailableException" |
| "ConstraintViolationException.ValidTecdocSpecification" |
| "ConstraintViolationException.ValidCompatibilityTable" |
| "ConstraintViolationException.ValidTemporaryProduct" |
| "ConstraintViolationException.StringLength" |
| "ConstraintViolationException.MaxWordLength" |
| "ConstraintViolationException.CharacterNotAllowed" |
| "ConstraintViolationException.OfferValidation" |
| "ReturnPolicyNotFoundException" |
| "ImpliedWarrantyNotFoundException" |
| "AfterSalesServiceConditionsOwnedBySeller" |
| "AfterSalesServiceConditionsRequiredByCompany" |
| "ShippingRatesNotFoundException" |
| "SHIPPING_RATES_ACCESS_DENIED" |
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
| "VALIDATION_FAILED" |
| "AvailableStockMustEqualToZeroOrBeGreaterThanZero" |

### FAQ

Przy próbie aktywacji / wznowienia oferty otrzymuję błąd “You cannot schedule activating an offer in the past”. Co on oznacza?

W polu scheduledFor przekazujesz datę z przeszłości. Aby wyeliminować ten błąd, podaj datę z przyszłości lub pozostaw to pole puste. Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/GRaj0q1PMSK#publikacja-oferty).

Otrzymałem komunikat - “You cannot create new drafts - your account has exceeded the maximum number {maxInactiveOffers} of drafts.” Co powinienem zrobić?

Otrzymałeś taki komunikat, ponieważ przekroczyłeś dostępny limit szkiców ofert (draftów), dotyczy to ofert z statusem INACTIVE - obecny limit to 20 000. Aby rozwiązać ten problem:

- usuń niepotrzebne za pomocą [DELETE /sale/offers/{offerId}](https://developer.allegro.pl/documentation#operation/deleteOfferUsingDELETE). Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/GRaj0q1PMSK#draft-oferty).
- sprawdź aktualną liczbę draftów za pomocą [GET /sale/offers?publication.status=INACTIVE](https://developer.allegro.pl/documentation#operation/getOfferUsingGET),

Ile ofert maksymalnie mogę aktywować lub zakończyć za pomocą PUT /sale/offer-publication-commands/{commandId}?

Maksymalnie możesz aktywować lub zakończyć 1000 ofert.

Próbuję utworzyć draft oferty, jednak w odpowiedzi otrzymuję status 401 Unauthorized wraz z komunikatem “Empty user_name claim”. Co on oznacza?

Posługujesz się tokenem uzyskanym w wyniku autoryzacji [client_credentials](https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR#clientcredentials-flow), który nie posiada kontekstu użytkownika. Aby utworzyć draft oferty, musisz posiadać token wygenerowany przez [code](https://developer.allegro.pl/tutorials/zlq9e75GdIR#authorization-code-flow) lub [device flow](https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR#device-flow).

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

Czy jest możliwe, że przy wyszukiwaniu produktu, jeśli podam numer EAN, otrzymam więcej niż jeden produkt?

Tak, może wystąpić taki przypadek, gdyż:

- np. w modzie może być jeden EAN na wiele rodzajów kolorystycznych danej odzieży.
- np. przy niektórych laptopach może być jeden numer EAN, a laptopy będą się różniły specyfikacją techniczną np. wielkością dysku,

Dlatego identyfikujemy produkty nie tylko po EAN-ie, ale też po jego parametrach. Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/BvZjx6exPfD).

Czym są produkty tymczasowe?

Produkty tymczasowe tworzymy automatycznie w wybranych kategoriach wyłącznie na podstawie ofert, w których sprzedawca dla parametru “Stan” wybrał wartość inną niż “Nowy” oraz nie przekazał wszystkich parametrów, które identyfikują produkt (lub dla przynajmniej jednego z nich wskazał wartość niejednoznaczną), czyli np. numeru katalogowego części.

Więcej szczegółów znajdziesz w [naszym newsie](https://developer.allegro.pl/news/w-wybranych-kategoriach-bedziemy-tworzyc-produkty-tymczasowe-nn9Y12dbqHM).

Jak wystawić licytację z opcją Kup Teraz?

Jeśli chcesz wystawić taką ofertę wystarczy, że prześlesz w polu "format" wartość AUCTION i uzupełnisz pola:

- minimalPrice - cena minimalna. To pole nie jest wymagane.
- startingPrice - cena początkowa

Dlaczego wprowadziliśmy funkcję draftów?

Dzięki draftom możesz przygotować zalążek oferty, na którym możesz pracować w innym terminie - np. gdy chcesz wypracować ostateczny kształt opisu. Możesz również od razu przygotować kompletny draft i opublikować ofertę w serwisie.

Dlaczego wprowadziliśmy osobny zasób dla cenników dostaw?

Dzięki temu, że ceny wysyłki są niezależne od oferty i dzięki osobnemu zasobowi do cenników dostawy, będziesz mógł szybciej przeprowadzić hurtową edycję cen dostawy. Wystarczy, że wprowadzisz zmianę w cenniku dostawy, a koszt przesyłki zmieni się we wszystkich ofertach, do których przypiąłeś dany cennik. Takie rozwiązanie pozwoli dynamicznie reagować na zmiany cen u przewoźników.

Otrzymałem komunikat - ‘You cannot create new drafts - your account has exceeded the maximum number {maxInactiveOffers} of drafts.’ Co powinienem zrobić?

Otrzymałeś taki komunikat, ponieważ przekroczyłeś dostępny limit szkiców ofert (draftów), dotyczy to ofert ze statusem “INACTIVE” - obecny limit to 20 000. Aby rozwiązać ten problem:

- usuń niepotrzebne za pomocą [DELETE /sale/offers/{offerId}}](https://developer.allegro.pl/documentation/#operation/deleteOfferUsingDELETE).
- sprawdź aktualną liczbę draftów za pomocą [GET /sale/offers?publication.status=INACTIVE](https://developer.allegro.pl/documentation/#operation/searchOffersUsingGET)

Próbuję utworzyć draft oferty, jednak w odpowiedzi otrzymuję status 401 Unauthorized wraz z komunikatem ‘Empty user_name claim’. Co on oznacza?

Posługujesz się tokenem uzyskanym w wyniku autoryzacji [client_credentials](https://developer.allegro.pl/auth/#clientCredentialsFlow), który nie posiada kontekstu użytkownika. Aby utworzyć draft oferty, musisz posiadać token wygenerowany przez [code](https://developer.allegro.pl/auth/#app) lub [device](https://developer.allegro.pl/auth/#DeviceFlow) flow.

Gdy próbuję aktywować oferty za pomocą PUT /sale/offer-publication-commands/{commandId}, w odpowiedzi otrzymuję same zera. Czy to prawidłowe zachowanie?

Tak, dzieje się tak ponieważ ten zasób działa asynchronicznie. Aby sprawdzić szczegółowy status realizacji zadania, użyj [GET /sale/offer-publication-commands/{commandId}/tasks](https://developer.allegro.pl/documentation/#operation/getPublicationTasksUsingGET).

W odpowiedzi na żądanie otrzymuję błąd 422 wraz z komunikatem ‘Description images are not valid.’. Co on oznacza?

Upewnij się, że linki do obrazków, które przesyłasz w sekcji description, prawidłowo przekazujesz także w sekcji images.

Nie znalazłem odpowiedniego produktu, jak mogę powiązać ofertę z produktem, który w niej sprzedaję?

Upewnij się, że podałeś odpowiednie i poprawne dane wejściowe w wywołaniu [GET /sale/products](https://developer.allegro.pl/documentation/#operation/getSaleProducts).

Katalog produktów cały czas rozbudowujemy - powtórz wyszukiwanie za jakiś czas i sprawdź, czy produkt jest już dostępny.

Dodaj produkt przez [POST /sale/product-proposals](https://developer.allegro.pl/documentation/#operation/proposeSaleProduct) lub przy tworzeniu oferty za pomocą [POST /sale/product-offers](https://developer.allegro.pl/documentation#operation/createProductOffers).

Co, jeśli przekażę inne wartości parametrów w ofercie niż otrzymałem dla produktu?

Otrzymasz błąd w polu "validation", który wskaże wartość parametru oferty niezgodną z danymi produktu.

Czy sprzedawca może dane o produkcie pobrane z Allegro przez GET /sale/products/{productId} wykorzystać również w innych miejscach np w swoim sklepie?

Nie - wynika to z praw autorskich do informacji zawartych w naszej bazie danych. Można je wykorzystać tylko i wyłącznie w serwisie Allegro.

Co, jeśli potrzebuję zmienić lub zaktualizować dane produktu?

Zmiany w danych produktu możesz zgłosić przez [formularz kontaktowy](https://allegro.pl/pomoc/kontakt), lub za pomocą [POST /sale/products/{productId}/change-proposals](https://developer.allegro.pl/documentation/#operation/productChangeProposal). Takie zgłoszenia są przez nas weryfikowane i - jeśli uznamy je za zasadne - odpowiednie zmiany wprowadzamy w danych produktu.

Czy mogę usunąć produkt?

Nie, i nie planujemy takiej możliwości.

Chcę w ofercie prezentować tylko własne zdjęcia produktu. Co zrobić, aby nie pobierać zdjęć z Katalogu Produktów?

Jeżeli chcesz, abyśmy nie zapisali w ofercie zdjęć produktu z Katalogu Produktów, przekaż pustą tablicę w polu "images" w obiekcie "productSet.product". Własne zdjęcia przekaż w tablicy "images" poza obiektem "productSet.product".

Czy podczas wystawiania oferty z produktem za pomocą /sale/product-offers mogę nadpisywać parametry produktu istniejącego w Katalogu Produktów?

Możesz nadpisać tylko te parametry, które nie identyfikują produktu, czyli te, dla których zwracamy wartość false w polu "options.identifiesProduct" w odpowiedzi dla [GET /sale/products/{productId}](https://developer.allegro.pl/documentation#operation/getSaleProduct). Parametry, które identyfikują produkt muszą być zgodne z tymi zapisanymi w naszym Katalogu. Jeżeli uważasz, że dane produktu zapisane w naszym Katalogu Produktów nie są zgodne z rzeczywistością - możesz zaproponować zmianę w produkcie za pomocą [GET /sale/products/{productId}/change-proposals](https://developer.allegro.pl/documentation#operation/productChangeProposal).

Czy za pomocą /sale/product-offers mogę wystawić także ogłoszenia (oferty w kategoriach ogłoszeniowych)?

Tak, jest to możliwe. Działa to tak samo, jak w przypadku /sale/offers:

- aktywuj ofertę, [zmieniając jej status na "ACTIVE"](https://developer.allegro.pl/tutorials/jak-zarzadzac-ofertami-7GzB2L37ase#zmiana-statusu-oferty).
- przypisz pakiet ogłoszeniowy za pomocą [PUT /sale/offer-classifieds-packages/{offer-id}](https://developer.allegro.pl/documentation#operation/assignClassifiedPackagesUsingPUT)
- utwórz najpierw draft ogłoszenia (oferta w statusie "INACTIVE"), zrobimy to od razu, jeżeli przekażesz w "sellingMode.format" wartość "ADVERTISEMENT", uzupełnij także wszystkie niezbędne parametry

### Lista zasobów

Pełną dokumentację zasobów w postaci pliku swagger.yaml znajdziesz [tu](https://developer.allegro.pl/swagger.yaml).

Lista zasobów podstawowych opisanych w poradniku:

- [POST /sale/product-proposals](https://developer.allegro.pl/documentation/#operation/proposeSaleProduct)- dodaj propozycję produktu
- [GET /sale/categories/{categoryId}/product-parameters](https://developer.allegro.pl/documentation/#operation/getFlatProductParametersUsingGET)- pobierz parametry dla tworzonego produktu
- [GET /sale/products/{productId}](https://developer.allegro.pl/documentation/#operation/getSaleProduct)- pobierz szczegółowe informacje o produkcie
- [POST /sale/images](https://developer.allegro.pl/documentation/#operation/uploadOfferImageUsingPOST)- dodaj zdjęcia
- [GET /sale/categories/{categoryId}/parameters](https://developer.allegro.pl/documentation/#operation/getFlatParametersUsingGET_2)- pobierz listę parametrów dla kategorii
- [GET /sale/categories/{categoryId}](https://developer.allegro.pl/documentation/#operation/getCategoryUsingGET_1)- pobierz informacje o wskazanej kategorii
- [GET /sale/categories](https://developer.allegro.pl/documentation/#operation/getCategoriesUsingGET)- pobierz listę kategorii
- [PATCH /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/editProductOffers)- edytuj ofertę
- [GET /sale/product-offers/{offerId}](https://developer.allegro.pl/documentation/#operation/getProductOffer)- pobierz szczegóły oferty
- [GET /sale/product-offers/{offerId}/operations/{operationId}](https://developer.allegro.pl/documentation/#operation/getProductOfferProcessingStatus)- sprawdź status publikacji / edycji oferty
- [GET /sale/products](https://developer.allegro.pl/documentation/#operation/getSaleProducts)- wyszukaj produkt
- [POST /sale/product-offers](https://developer.allegro.pl/documentation/#operation/createProductOffers)- utwórz ofertę powiązaną z produktem

Lista zasobów wspierających opisanych w poradniku:

- [GET /sale/products/change-proposals/{id}](https://developer.allegro.pl/documentation/#operation/getProductChangeProposal)- pobierz status zgłoszenia zmiany w produkcie
- [POST /sale/products/{productId}/change-proposals](https://developer.allegro.pl/documentation/#operation/productChangeProposal)- zgłoś sugestię zmiany w produkcie
- [PUT /sale/offer-attachments/{attachmentId}](https://developer.allegro.pl/documentation/#operation/uploadOfferAttachmentUsingPUT)- prześlij załącznik do oferty
- [POST /sale/offer-attachments](https://developer.allegro.pl/documentation/#operation/createOfferAttachmentUsingPOST)- dodaj obiekt załącznika do oferty
- [GET /sale/size-tables](https://developer.allegro.pl/documentation/#operation/getTablesUsingGET)- pobierz tabele rozmiarów
- [GET /after-sales-service-conditions/warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET_2)- pobierz informacje o gwarancjach
- [GET /after-sales-service-conditions/implied-warranties](https://developer.allegro.pl/documentation/#operation/getPublicSellerListingUsingGET)- pobierz warunki reklamacji
- [GET /after-sales-service-conditions/return-policies](https://developer.allegro.pl/documentation/#operation/getAfterSalesServiceReturnPolicyUsingGET)- pobierz warunki zwrotów
- [GET /sale/shipping-rates](https://developer.allegro.pl/documentation/#operation/getListOfShippingRatestUsingGET)- pobierz cenniki dostawy

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