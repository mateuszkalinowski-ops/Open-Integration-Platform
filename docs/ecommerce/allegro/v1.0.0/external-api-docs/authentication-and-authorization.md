Uwierzytelnianie i autoryzacja - Allegro Developer Portal - baza wiedzy o Allegro REST API

Wstęp

Authorization Code flow

Device flow

Client_credentials flow

Dynamic Client Registration

Scope w API Allegro

Wywołanie zasobu REST API

Przedłużenie ważności tokena

Kiedy token straci ważność

Sprawdź, jakie aplikacje są powiązane z Twoim kontem Allegro

Usuń powiązanie danej aplikacji z Twoim kontem Allegro

FAQ

# Uwierzytelnianie i autoryzacja

Jak korzystać z OAuth Allegro i poprawnie autoryzować aplikację oraz użytkowników.

### Wstęp

W Allegro API udostępniamy 4 sposoby autoryzacji i uwierzytelniania:

- Dynamic Client Registration (DCR) - umożliwia tworzenie instancji aplikacji w sposób zautomatyzowany - przeznaczona dla aplikacji, gdzie użytkownik instaluje kopię oprogramowania (np. instancję platformy sklepowej we własnej infrastrukturze).
- Client_credentials flow - umożliwia autoryzację aplikacji bez zgody użytkownika na jej działanie, przeznaczona do zasobów, które pozwalają na dostęp do publicznych danych, np. pobieranie listy kategorii,
- Device flow - umożliwia autoryzację na urządzeniach lub w aplikacjach, które nie posiadają interfejsu graficznego lub sposobu na wpisanie tekstu,
- Authorization Code flow - najpopularniejsza metoda autoryzacji dla standardu OAuth, w jej ramach aplikacja może wykonywać operacje w imieniu użytkownika,

W tym poradniku dowiesz się, czym się charakteryzują oraz w jaki sposób z nich korzystać.

Niezależnie od metody autoryzacji aplikacja powinna działać na jednym kluczu (Client_ID). Aby zapewnić bezpieczeństwo i spójność integracji, aplikacje korzystające z naszego API nie mogą żądać od użytkowników podawania ich Client_ID i Client_Secret. Zamiast tego, aplikacje powinny używać własnych danych uwierzytelniających i implementować standardowy przepływ autoryzacji OAuth, aby uzyskać dostęp do zasobów użytkownika.

### Authorization Code flow

W ramach REST API udostępniliśmy autoryzację dostępu typu Authorization Code - najpopularniejsza dla standardu OAuth. Jest ona wykorzystywana w sytuacjach, w których klient (aplikacja) potrzebuje wykonywać operacje w imieniu użytkownika. W takim przypadku niezbędne staje się otrzymanie zgody od użytkownika na takie działanie. W tym celu użytkownik zostaje przekierowany do strony Allegro.pl celem zalogowania się, a po poprawnym uwierzytelnieniu aplikacja zwraca kod, który następnie należy przekazać do OAuth celem uzyskania tokena dostępowego operującego w kontekście zalogowanego użytkownika.

Zabezpiecz swoją aplikację przed wykorzystaniem kodu autoryzacyjnego przez złośliwe oprogramowanie - w tym celu przekaż parametry opcjonalne code_challenge oraz code_challenge_method związane z mechanizmem [PKCE](https://tools.ietf.org/html/rfc7636)(Proof Key for Code Exchange). Więcej informacji znajdziesz w dalszej części poradnika.

#### Rejestracja aplikacji

Przed zalogowaniem użytkownika (a tym samym uzyskaniem przyzwolenia na wykonywanie przez aplikację żądań w jego imieniu), musisz zarejestrować aplikację, dziękie czemu uzyskasz dane dostępowe niezbędne do działania oprogramowania komunikującego się z Allegro REST API.

[Rejestracja aplikacji](https://apps.developer.allegro.pl/) jest możliwa tylko dla [aktywnych kont](https://allegro.pl/pomoc/dla-sprzedajacych/rejestracja-i-aktywacja/czym-jest-pelna-aktywacja-konta-i-jak-moge-ja-przeprowadzic-GDeq5WOB8uE) z włączonym [dwustopniowym logowaniem](https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/czym-jest-dwustopniowe-logowanie-i-dlaczego-warto-z-niego-korzystac-dykqg9nMKSZ).

Dla ułatwienia na [środowisku testowym](https://allegro.pl.allegrosandbox.pl/) dwustopniowe logowanie nie jest wymagane.

Aby skorzystać z Authorization Code flow, zarejestruj nową aplikację w [udostępnionym przez nas narzędziu](https://apps.developer.allegro.pl/) i podaj poniższe dane:

- adresy do przekierowania (adresy aplikacji, do których przekazany ma zostać kod autoryzujący).
- zaznacz opcję "Aplikacja będzie posiadać dostęp do przeglądarki, za pomocą której użytkownik będzie się logował do Allegro (np. aplikacja na serwerze albo plik wykonywalny)",
- krótki opis (opcjonalnie) - nie będziemy go prezentowali użytkownikom twojej aplikacji. Jest to informacja dla Ciebie, aby w łatwy sposób rozróżnić poszczególne aplikacje,
- nazwę aplikacji - prezentujemy ją użytkownikowi, gdy wyraża zgodę na dostęp aplikacji do swojego konta,

W formularzu musisz również zaakceptować [regulamin REST API](https://developer.allegro.pl/rules).

Na jednym koncie możesz posiadać do 5 kluczy aplikacji jednocześnie.

Gdy zatwierdzisz formularz, otrzymasz dane dostępowe, które pozwolą ci korzystać z zasobów REST API: Client ID oraz Client Secret.

Nie możesz zmienić typu zarejestrowanej aplikacji.

Client ID oraz Client Secret są niezbędne do komunikacji w ramach protokołu [OAuth](https://en.wikipedia.org/wiki/OAuth), który - w wersji 2.0 - Allegro REST API obsługuje w standardzie. Tokeny dostępowe są zgodne ze standardem [JWT](https://en.wikipedia.org/wiki/JSON_Web_Token).

W Allegro REST API obowiązuje limit dla liczby access tokenów, które możesz wygenerować w określonym czasie dla jednego użytkownika. Jeżeli go przekroczysz, w odpowiedzi zwrócimy błąd HTTP: 429 Too Many Requests. Oznacza to, że działanie twojej aplikacji odbiega od normy - upewnij się, że nie tworzysz więcej tokenów niż wymagają tego operacje, które wykonujesz. Raz wygenerowany token dla jednego użytkownika powinien być używany aż do momentu wygaśnięcia, po tym czasie odśwież token za pomocą refresh tokena.

Wszystkie zasoby niezbędne do autoryzacji udostępniamy pod adresem: [https://allegro.pl](https://allegro.pl/). Nie są one dostepne pod adresem do wywołania zasobów: [https://api.allegro.pl/](https://api.allegro.pl/).

#### Autoryzacja użytkownika

Cały proces wygląda następująco:

1. Udostępnij w swojej aplikacji przycisk/odnośnik, np. Zaloguj do Allegro, wywołujący odpowiednio sparametryzowane żądanie HTTP do zasobu pozwalającego na uwierzytelnienie użytkownika:

```
https://allegro.pl/auth/oauth/authorize?response_type=code&client_id=a21...6be&redirect_uri=http://exemplary.redirect.uri
```

Jeżeli chcesz wyświetlić stronę logowania dla innego rynku (w innym języku), wystarczy, że zamienisz domenę z allegro.pl na inną, np. allegro.cz:

```
https://allegro.cz/auth/oauth/authorize?response_type=code&client_id=a21...6be&redirect_uri=http://exemplary.redirect.uri
```

opis

Rodzaj odpowiedzi (w tym przypadku code)

wymagany / opcjonalny

wymagany

opis

ID klienta (otrzymane przy rejestracji aplikacji)

wymagany / opcjonalny

wymagany

opis

Adres do przekierowania, na który wysłany zostanie kod (musi być zgodny z tym podanym przy rejestracji aplikacji)

wymagany / opcjonalny

wymagany

opis

Sposób szyfrowania code_challenge w mechanizmie PKCE

wymagany / opcjonalny

opcjonalny

opis

Kod na potrzeby mechanizmu PKCE

wymagany / opcjonalny

opcjonalny

opis

Sposób uwierzytelniania użytkownika w procesie autoryzacji

wymagany / opcjonalny

opcjonalny

opis

Dodatkowe dane, które zostaną przekazane z powrotem do aplikacji po autoryzacji

wymagany / opcjonalny

opcjonalny

opis

Zakresy określające poziom uprawnień do korzystania z API Allegro. Więcej dowiesz się w dalszej części poradnika.

wymagany / opcjonalny

opcjonalny

| parametr | opis | wymagany / opcjonalny |
| --- | --- | --- |
| response_type |
| client_id |
| redirect_uri |
| code_challenge_method |
| code_challenge |
| prompt |
| state |
| scope |

W procesie autoryzacji możesz skorzystać z dodatkowych, dowolnych parametrów w adresie URL, które zostaną przekazane w redirect_uri. [Specyfikacja OAuth rekomenduje](https://auth0.com/docs/protocols/oauth2/redirect-users) jednak używanie parametru state do przekazywania danych, które są potrzebne aplikacji do przywrócenia jej stanu po przekierowaniu.

Jeśli wysyłasz parametr [state](https://auth0.com/docs/secure/attack-protection/state-parameters):

- niezakodowany w adresie URL - przekierujemy użytkownika z zakodowanym parametrem state w adresie URL (UTF-8).
- zakodowany w adresie URL (UTF-8), zawierający [znaki zastrzeżone](https://datatracker.ietf.org/doc/html/rfc3986#section-2.2)- serwer OAuth zwróci wówczas niezmieniony parametr state podczas przekierowania,

Dzięki temu, pomimo różnych form parametru state przekazanych podczas wstępnego żądania autoryzacji, w przekierowaniu będzie on zawsze zakodowany.

##### PKCE

Zabezpiecz swoją aplikację przed wykorzystaniem kodu autoryzacyjnego przez złośliwe oprogramowanie - w tym celu zastosuj mechanizm [PKCE](https://tools.ietf.org/html/rfc7636)(Proof Key for Code Exchange). By z niego skorzystać, wygeneruj we własnym zakresie code_verifier, który powinien być losowym ciągiem znaków o długości pomiędzy 43 a 128 znaków. Następnie w procesie autoryzacji dodaj dwa parametry: code_challenge oraz code_challenge_method. Wartość code_verifier wykorzystasz później, podczas żądania o token (pkt. 5). Parametr code_challenge_method musi przyjąć wartość S256 - oznacza, że code_challenge jest zahashowanym (algorytmem SHA-256) code_verifier. Zapewnia to większe bezpieczeństwo ze względu na użyte hashowanie.

S256: codechallenge = BASE64URL-ENCODE(SHA256(ASCII(codeverifier))),

Mechanizm PKCE nie ma zastosowania w procesie przedłużania ważności tokena.

Przykład żądania HTTP dla codeverifier = KnAijeNvdSeloYlVcOh3HRmgZX57wDeVHiwRFQKO2F9DdBI:

```
https://allegro.pl/auth/oauth/authorize?response_type=code&client_id=a21...6be&redirect_uri=http://exemplary.redirect.uri&code_challenge_method=S256&code_challenge=a69se03ZmsPhTLYQKHpGUH7m5waf-U8D-5pTwFRgLI4
```

##### Parametr prompt

Kolejnym opcjonalnym mechanizmem, z którego możesz skorzystać, jest ekran potwierdzenia konta podczas uwierzytelniania w allegro. Ekran pokażemy, jeśli w procesie autoryzacji, dodasz parametr prompt=confirm:

```
https://allegro.pl/auth/oauth/authorize?response_type=code&client_id=a21...6be&redirect_uri=http://exemplary.redirect.uri&prompt=confirm
```

2. Gdy użytkownik skorzysta z przycisku/odnośnika, zostaje przekierowany do formularza logowania na stronie Allegro.pl:

3. Po poprawnym uwierzytelnieniu użytkownik zostanie przekierowany do strony, na której zgadza się by dana aplikacja miała możliwość wykonywania operacji/żądań w jego imieniu:

Pamiętaj, że warto obsłużyć scenariusz, w którym użytkownik wybierze "Anuluj". Powinien wtedy otrzymać odpowiedni komunikat.

4. Po wyrażeniu zgody użytkownik wraca do aplikacji, a na adres podany w ramach redirect_uri, zwracamy kod autoryzujący.

Kod jest:

- potrzebny by uzyskać token dostępowy.
- ważny przez 10 sekund,
- jednorazowego użytku,

```
http://exemplary.redirect.uri/?code=pOPEy9Tq94aEss540azzC7xL6nCJDWto
```

5. Mając ważny kod, aplikacja zgłasza się po token wykonując żądanie HTTP metodą POST na adres: [https://allegro.pl/auth/oauth/token](https://allegro.pl/auth/oauth/token), dołączając nagłówek Authorization z odpowiednią zawartością:

```
curl -X POST \
  https://allegro.pl/auth/oauth/token \
  -H 'Authorization: Basic base64(clientId:secret)' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=authorization_code&code=pOPEy9Tq94aEss540azzC7xL6nCJDWto&redirect_uri=http://exemplary.redirect.uri'
```

opis

Nagłówek HTTP: Authorization. Autoryzacja typu Basic, z zawartością w formie client_id:client_secret (dane otrzymane przy rejestracji aplikacji) w postaci [Base64](http://base64encode.org/). Pamiętaj aby zakodować całość danych client_id:client_secret wraz ze znakiem “:” pomiędzy wartościami.

wymagany / opcjonalny

wymagany

opis

Rodzaj dostępu potrzebny do uzyskania tokena (w tym przypadku authorization_code)

wymagany / opcjonalny

wymagany

opis

Kod autoryzujący (uzyskany w kroku 4)

wymagany / opcjonalny

wymagany

opis

Adres do przekierowania (musi być zgodny z tym podanym przy rejestracji aplikacji)

wymagany / opcjonalny

wymagany

opis

Kod weryfikujący na potrzeby mechanizmu PKCE

wymagany / opcjonalny

opcjonalny

| parametr | opis | wymagany / opcjonalny |
| --- | --- | --- |
| Authorization |
| grant_type |
| code |
| redirect_uri |
| code_verifier |

Jeśli w pkt.1 zastosowano mechanizm PKCE, to zamiast przekazywać nagłówek Authorization przekaż parametr client_id, oraz parametr code_verifier. Podaj tę samą wartość, jaką określiłeś wcześniej, np.:

```
curl -X POST \
  https://allegro.pl/auth/oauth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=authorization_code&code=pOPEy9Tq94aEss540azzC7xL6nCJDWto&redirect_uri=http://exemplary.redirect.uri&code_verifier=KnAijeNvdSeloYlVcOh3HRmgZX57wDeVHiwRFQKO2F9DdBI&client_id={client_id}'
```

6. Po poprawnym wykonaniu żądania, zwracamy odpowiedź w formacie JSON zawierającą m.in. token dostępowy, z którego możemy korzystać przy wywoływaniu zasobów REST API.

Przykładowy response:

```
{
  "access_token":"eyJ...dUA",   // token dostępowy, który pozwala wykonywać operacje na zasobach dostępnych publicznie
  "token_type":"bearer",  // typ tokena (w naszym przypadku: bearer)
  "refresh_token":"eyJ...QEQ",  // refresh token jednorazowego użytku, pozwalający na przedłużenie ważności autoryzacji użytkownika dla aplikacji do max. 3 miesięcy
  "expires_in":43199,   // czas ważności tokena dostępowego w sekundach (token jest ważny 12 godzin)
  "scope":"allegro_api",   // zasięg danych/funkcjonalności do których użytkownik autoryzował aplikacje
  "allegro_api": true,   // opcjonalne, w przyszłości całkowicie usuniemy - flaga wskazująca na fakt, że token został wygenerowany dla celów API (brak bezpośredniego zastosowania)
  "jti":"2184f3be-f6de-4a66-bd8f-b11347d7ba80"   // identyfikator tokena JWT (brak bezpośredniego zastosowania)
}
```

W przyszłości w odpowiedzi mogą pojawić się dodatkowe pola.

Przykładowy kod realizujący autoryzację typu Authorization Code (z PKCE):

```
<?php

define('CLIENT_ID', ''); // wprowadź Client_ID aplikacji
define('CLIENT_SECRET', ''); // wprowadź Client_Secret aplikacji
define('REDIRECT_URI', ''); // wprowadź redirect_uri
define('AUTH_URL', 'https://allegro.pl/auth/oauth/authorize');
define('TOKEN_URL', 'https://allegro.pl/auth/oauth/token');


function generateCodeVerifier() {
    $verifier_bytes = random_bytes(80);
    $code_verifier = rtrim(strtr(base64_encode($verifier_bytes), "+/", "-_"), "=");
    return $code_verifier;
}

function generateCodeChallenge($code_verifier) {
    $challenge_bytes = hash("sha256", $code_verifier, true);
    $code_challenge = rtrim(strtr(base64_encode($challenge_bytes), "+/", "-_"), "=");
    return $code_challenge;
}

function getAuthorizationCode($code_verifier) {
    $code_challenge = generateCodeChallenge($code_verifier);
    $authorization_redirect_url = AUTH_URL . "?response_type=code&client_id=" 
    . CLIENT_ID . "&redirect_uri=" . REDIRECT_URI . "&code_challenge_method=S256&code_challenge=" . $code_challenge;
    ?>
    <html>
    <body>
    <a href="<?php echo $authorization_redirect_url; ?>">Zaloguj do Allegro</a>
    </body>
    </html>
    <?php
}


function getCurl($content) {
    $ch = curl_init();
    curl_setopt_array($ch, array(
        CURLOPT_URL => TOKEN_URL,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $content
    ));
    return $ch;
}


function getAccessToken($authorization_code, $code_verifier) {
    $authorization_code = urlencode($authorization_code);
    $content = "grant_type=authorization_code&code=${authorization_code}&redirect_uri=" . REDIRECT_URI . "&code_verifier=${code_verifier}&client_id=" . CLIENT_ID . "";
    $ch = getCurl($content);
    $tokenResult = curl_exec($ch);
    $resultCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($tokenResult === false || $resultCode !== 200) {
        exit ("Something went wrong $resultCode $tokenResult");
    }
    return json_decode($tokenResult)->access_token;
}


function main(){
    $code_verifier = generateCodeVerifier();
    if ($_GET["code"]) {
        $access_token = getAccessToken($_GET["code"], $code_verifier);
        echo "access_token = ", $access_token;
    } else {    
        getAuthorizationCode($code_verifier);
    }
}


main();

?>
```

zamknij

PHP

```
import base64
import hashlib
import secrets
import string
import requests
import json

CLIENT_ID = ""          # wprowadź Client_ID aplikacji
CLIENT_SECRET = ""      # wprowadź Client_Secret aplikacji
REDIRECT_URI = ""       # wprowadź redirect_uri
AUTH_URL = "https://allegro.pl/auth/oauth/authorize"
TOKEN_URL = "https://allegro.pl/auth/oauth/token"


def generate_code_verifier():
    code_verifier = ''.join((secrets.choice(string.ascii_letters) for i in range(40)))
    return code_verifier


def generate_code_challenge(code_verifier):
    hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    base64_encoded = base64.urlsafe_b64encode(hashed).decode('utf-8')
    code_challenge = base64_encoded.replace('=', '')
    return code_challenge


def get_authorization_code(code_verifier):
    code_challenge = generate_code_challenge(code_verifier)
    authorization_redirect_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}" \
                                 f"&code_challenge_method=S256&code_challenge={code_challenge}"
    print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
    print(f"--- {authorization_redirect_url} ---")
    authorization_code = input('code: ')
    return authorization_code


def get_access_token(authorization_code, code_verifier):
    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code,
                'redirect_uri': REDIRECT_URI, 'code_verifier': code_verifier, 'client_id': CLIENT_ID}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=False)
        response_body = json.loads(access_token_response.text)
        return response_body
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def main():
    code_verifier = generate_code_verifier()
    authorization_code = get_authorization_code(code_verifier)
    response = get_access_token(authorization_code, code_verifier)
    access_token = response['access_token']
    print(f"access token = {access_token}")


if __name__ == "__main__":
    main()
```

zamknij

Python

Przykładowy kod realizujący autoryzację typu Authorization Code (bez PKCE):

```
<?php

define('CLIENT_ID', ''); // wprowadź Client_ID aplikacji
define('CLIENT_SECRET', ''); // wprowadź Client_Secret aplikacji
define('REDIRECT_URI', ''); // wprowadź redirect_uri
define('AUTH_URL', 'https://allegro.pl/auth/oauth/authorize');
define('TOKEN_URL', 'https://allegro.pl/auth/oauth/token');


function getAuthorizationCode() {
    $authorization_redirect_url = AUTH_URL . "?response_type=code&client_id=" 
    . CLIENT_ID . "&redirect_uri=" . REDIRECT_URI;
    ?>
    <html>
    <body>
    <a href="<?php echo $authorization_redirect_url; ?>">Zaloguj do Allegro</a>
    </body>
    </html>
    <?php
}


function getCurl($headers, $content) {
    $ch = curl_init();
    curl_setopt_array($ch, array(
        CURLOPT_URL => TOKEN_URL,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $content
    ));
    return $ch;
}


function getAccessToken($authorization_code) {
    $authorization = base64_encode(CLIENT_ID.':'.CLIENT_SECRET);
    $authorization_code = urlencode($authorization_code);
    $headers = array("Authorization: Basic {$authorization}","Content-Type: application/x-www-form-urlencoded");
    $content = "grant_type=authorization_code&code=${authorization_code}&redirect_uri=" . REDIRECT_URI;
    $ch = getCurl($headers, $content);
    $tokenResult = curl_exec($ch);
    $resultCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($tokenResult === false || $resultCode !== 200) {
        exit ("Something went wrong $resultCode $tokenResult");
    }
    return json_decode($tokenResult)->access_token;
}


function main(){
    if ($_GET["code"]) {
        $access_token = getAccessToken($_GET["code"]);
        echo "access_token = ", $access_token;
    } else {    
        getAuthorizationCode();
    }
}


main();

?>
```

zamknij

PHP

```
import requests
import json

CLIENT_ID = ""          # wprowadź Client_ID aplikacji
CLIENT_SECRET = ""      # wprowadź Client_Secret aplikacji
REDIRECT_URI = ""       # wprowadź redirect_uri
AUTH_URL = "https://allegro.pl/auth/oauth/authorize"
TOKEN_URL = "https://allegro.pl/auth/oauth/token"


def get_authorization_code():
    authorization_redirect_url = AUTH_URL + '?response_type=code&client_id=' + CLIENT_ID + \
                                 '&redirect_uri=' + REDIRECT_URI
    print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
    print("---  " + authorization_redirect_url + "  ---")
    authorization_code = input('code: ')
    return authorization_code


def get_access_token(authorization_code):
    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': REDIRECT_URI}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=False, auth=(CLIENT_ID, CLIENT_SECRET))
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        return access_token
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def main():
    authorization_code = get_authorization_code()
    access_token = get_access_token(authorization_code)
    print("access token = " + access_token)


if __name__ == "__main__":
    main()
```

zamknij

Python

### Device flow

Dzięki ścieżce device flow możesz zautoryzować użytkownika na urządzeniach lub w aplikacjach, które nie posiadają:

- lub innego prostego sposobu na wpisanie tekstu.
- przeglądarki,
- interfejsu graficznego,

Jest to implementacja [RFC OAuth 2.0 Device Flow](https://tools.ietf.org/html/draft-ietf-oauth-device-flow-12), więcej informacji na jej temat znajdziesz w poniższych artykułach:

- [OAuth 2.0 Device Flow Grant](https://alexbilbie.github.io/2016/04/oauth-2-device-flow-grant/).
- [OAuth for Browserless and Input-Constrained Devices](https://www.oauth.com/oauth2-servers/device-flow/),

#### Rejestracja aplikacji typu Device

Aby skorzystać z Device flow, zarejestruj nową aplikację w [udostępnionym przez nas narzędziu](https://apps.developer.allegro.pl/) i podaj poniższe dane:

- zaznacz opcję "Aplikacja będzie działać w środowisku bez dostępu do przeglądarki albo klawiatury (np. aplikacja konsolowa albo na urządzeniu typu telewizor)".
- krótki opis (opcjonalnie) - nie będziemy go prezentowali użytkownikom twojej aplikacji. Jest to informacja dla Ciebie, aby w łatwy sposób rozróżnić poszczególne aplikacje,
- nazwę aplikacji - prezentujemy ją użytkownikowi, gdy wyraża zgodę na dostęp aplikacji do swojego konta,

W formularzu musisz również zaakceptować [regulamin REST API](https://developer.allegro.pl/rules).

[Rejestracja aplikacji](https://apps.developer.allegro.pl/) jest możliwa tylko dla [aktywnych kont](https://allegro.pl/pomoc/dla-sprzedajacych/rejestracja-i-aktywacja/czym-jest-pelna-aktywacja-konta-i-jak-moge-ja-przeprowadzic-GDeq5WOB8uE) z włączonym [dwustopniowym logowaniem](https://allegro.pl/pomoc/dla-kupujacych/logowanie-i-haslo/czym-jest-dwustopniowe-logowanie-i-dlaczego-warto-z-niego-korzystac-dykqg9nMKSZ).

Dla ułatwienia na [środowisku testowym](https://allegro.pl.allegrosandbox.pl/) dwustopniowe logowanie nie jest wymagane.

Gdy zatwierdzisz formularz, otrzymasz dane dostępowe, które pozwolą ci korzystać z zasobów REST API: Client ID oraz Client Secret.

Na jednym koncie możesz posiadać do 5 kluczy aplikacji jednocześnie.

W Allegro REST API obowiązuje limit dla liczby access tokenów, które możesz wygenerować w określonym czasie dla jednego użytkownika. Jeżeli go przekroczysz, w odpowiedzi zwrócimy błąd HTTP: 429 Too Many Requests. Oznacza to, że działanie twojej aplikacji odbiega od normy - upewnij się, że nie tworzysz więcej tokenów niż wymagają tego operacje, które wykonujesz. Raz wygenerowany token dla jednego użytkownika powinien być używany aż do momentu wygaśnięcia, po tym czasie odśwież token za pomocą refresh tokena.

Nie możesz zmienić typu zarejestrowanej aplikacji.

#### Device flow - autoryzacja użytkownika

Do integracji ze swoją aplikacją otrzymasz kod użytkownika (user_code) i kod urządzenia (device_code). Użytkownik wpisuje otrzymany od ciebie kod użytkownika (user_code) na specjalnej stronie (verification_uri). Jeśli chcesz, aby taki link był “klikalny” (np. zamierzasz wysłać go mailem albo przedstawić w postaci QR code) użyj verification_uri_complete. Następnie użytkownik wyraża zgodę na dostęp aplikacji do swoich danych i realizowanie zmian w jego imieniu (jeżeli wcześniej nie wyraził zgody). W tym czasie twoja aplikacja odpytuje dedykowany endpoint korzystając z kodu urządzenia (device_code), aby otrzymać m.in. token dostępowy, z którego możesz korzystać przy wywoływaniu zasobów REST API w imieniu użytkownika.

Cały proces wygląda następująco:

1, 2. Skorzystaj z zasobu POST [https://allegro.pl/auth/oauth/device](https://allegro.pl/auth/oauth/device), aby otrzymać:

- device_code, który jest niezbędny do uzyskania tokena dostępowego.
- user_code, który wraz z adresem do weryfikacji przekaż użytkownikowi,

Okres ważności device_code i user_code jest podany w polu expires_in.

Nagłówek HTTP: Authorization zawiera autoryzację typu Basic, z zawartością w formie client_id:client_secret (dane te otrzymałeś przy rejestracji aplikacji) zakodowane przy pomocy Base64. Pamiętaj, aby zakodować całość danych client_id:client_secret wraz ze znakiem “:” pomiędzy wartościami.

Przykładowy request:

```
curl -X POST \
  'https://allegro.pl/auth/oauth/device?client_id={client_id}' \
  -H 'Authorization: Basic {base64(client_id:client_secret)}' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
```

W żądaniu, w zawartości po client_id:client_secret , możesz przekazać dodatkowy parametr scope po znaku & (np. {client_id}:{client_secret}&scope=allegro:api:sale:offers:write%20allegro:api:orders:read) - są to zakresy określające poziom uprawnień do korzystania z API Allegro. Więcej dowiesz się w dalszej części poradnika.

Przykładowy response:

```
{
        user_code: "cbt3zdu4g",  // kod użytkownika - zalecamy przedstawić te dane użytkownikowi w postaci XXX XXX XXX. Taka forma będzie dla niego czytelniejsza przy przepisywaniu.
        device_code: "645629715",  // kod aplikacji - niezbędny do uzyskania tokenu dostępowego
        expires_in: "3600",  // liczba sekund, przez które ważne są oba kody
        interval: “5”,  // wymagany odstęp (w sekundach) pomiędzy kolejnymi zapytaniami o status autoryzacji. Jeśli będziesz odpytywać częściej otrzymasz odpowiedź o statusie HTTP 400 z kodem: "slow_down".
        verification_uri: “https://allegro.pl/skojarz-aplikacje”,   // adres do weryfikacji użytkownika
        verification_uri_complete: “https://allegro.pl/skojarz-aplikacje?code=cbt3zdu4g”  // adres do weryfikacji dla użytkownika z wypełnionym kodem użytkownika
}
```

3, 4a, 5. Poproś użytkownika, aby przeszedł z poziomu dowolnego urządzenia na podany przez ciebie adres (verification_uri) i podał tam kod użytkownika (user_code).

Jeśli chcesz, aby taki link był "klikalny" (np. zamierzasz wysłać go mailem albo przedstawić w postaci QR code) użyj verification_uri_complete. Dzięki temu użytkownik nie będzie musiał wpisywać ręcznie kodu użytkownika.

Gdy użytkownik poprawnie wprowadzi kod, poprosimy, aby zalogował się do Allegro i wyraził zgodę, na dostęp aplikacji do jego danych. Po tym jak poprawnie wykona wszystkie czynności, wyświetlimy mu informację o pomyślnej autoryzacji jego konta.

4b. Równocześnie twoja aplikacja powinna zacząć odpytywać zasób:

```
curl -X POST \
  https://allegro.pl/auth/oauth/token \
  -H 'Authorization: Basic base64(clientId:secret)' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=urn:ietf:params:oauth:grant-type:device_code&device_code={device_code}'
```

Możesz otrzymać 5 rodzajów odpowiedzi:

Status HTTP 200 - odpowiedź prawidłowa. W odpowiedzi otrzymasz m.in. token dostępowy, który pozwoli ci korzystać z zasobów REST API. Kolejna próba użycia tego samego device code skończy się odpowiedzią o statusie 400. Device_code może tylko raz zwrócić token.

Przykładowy response:

```
{
"access_token":"eyJ...dUA",
"token_type":"bearer",
"refresh_token":"eyJ...SDA",
"expires_in":43199,
"scope":"allegro_api",
"allegro_api": true,
"jti":"2184f3be-f6de-4a66-bd8f-b11347d7ba80"
}
```

W przyszłości, w odpowiedzi mogą pojawić się dodatkowe pola.

Status HTTP 400 z kodem:

```
{
  "error":"authorization_pending"  // oznacza, że Twoja aplikacja powinna nadal odpytywać ten zasób, 
      ponieważ użytkownik nie zezwolił jeszcze na dostęp Twojej aplikacji.
}
```

lub

```
{
  "error":"slow_down"  // oznacza, że Twoja aplikacja zbyt często odpytuje zasób. 
      // Zmniejsz częstotliwość zapytań do wartości określonej w polu “interval”.
}
```

Status HTTP 400 z kodem:

```
{
  "error":"access_denied"   // oznacza, że użytkownik odmówił dostępu Twojej aplikacji. 
       // Twoja aplikacja powinna przestać odpytywać ten zasób.
}
```

Status HTTP 400 z kodem:

```
{
  "error": "Invalid device code"  // oznacza, że kod kod device_code jest niepoprawny lub został zużyty. 
      // W takim przypadku Twoja  aplikacja powinna zaprzestać odpytywania z tym kodem i wygenerować nowy.
}
```

Odpowiedź o statusie 400 z innym kodem błędu oznacza, że device_code i user_code straciły ważność albo w twoim zapytaniu jest błąd. Sprawdź, czy wysyłasz poprawne wartości:

- Device_code.
- Client Secret,
- Client ID,

Przykładowy kod realizujący autoryzację typu Device Flow:

```
<?php
define('CLIENT_ID', ''); // wprowadź Client_ID aplikacji
define('CLIENT_SECRET', ''); // wprowadź Client_Secret aplikacji
define('CODE_URL', 'https://allegro.pl/auth/oauth/device');
define('TOKEN_URL', 'https://allegro.pl/auth/oauth/token');

function getCurl($url, $headers, $content) {
    $ch = curl_init();
    curl_setopt_array($ch, array(
        CURLOPT_URL => $url,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $content
    ));
    return $ch;
}


function getCode(){
    $authorization = base64_encode(CLIENT_ID.':'.CLIENT_SECRET);
    $headers = array("Authorization: Basic {$authorization}","Content-Type: application/x-www-form-urlencoded");
    $content = "client_id=" .CLIENT_ID;
    $ch = getCurl(CODE_URL, $headers, $content);
    $result = curl_exec($ch);
    $resultCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($result === false || $resultCode !== 200) {
        exit ("Something went wrong:  $resultCode $result");
    }
    return json_decode($result);
}


function getAccessToken($device_code) {
    $authorization = base64_encode(CLIENT_ID.':'.CLIENT_SECRET);
    $headers = array("Authorization: Basic {$authorization}","Content-Type: application/x-www-form-urlencoded");
    $content = "grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code&device_code=${device_code}";
    $ch = getCurl(TOKEN_URL, $headers, $content);
    $tokenResult = curl_exec($ch);
    curl_close($ch);
    return json_decode($tokenResult);
}


function main(){
    $result = getCode();
    echo "Użytkowniku, otwórz ten adres w przeglądarce: \n" . $result->verification_uri_complete ."\n";
    $accessToken = false;
    $interval = (int)$result->interval;
     do {
         sleep($interval);
         $device_code = $result->device_code;
         $resultAccessToken = getAccessToken($device_code);
          if (isset($resultAccessToken->error)) {
               if ($resultAccessToken->error == 'access_denied') {
                   break; 
              } elseif ($resultAccessToken->error == 'slow_down') {
                   $interval++; 
                }
            } else {
                $accessToken = $resultAccessToken->access_token;
                echo "access_token = ", $accessToken;
            }
        } while ($accessToken == false);

    }


main();

?>
```

zamknij

PHP

```
import requests
import json
import time

CLIENT_ID = ""          # wprowadź Client_ID aplikacji
CLIENT_SECRET = ""      # wprowadź Client_Secret aplikacji
CODE_URL = "https://allegro.pl/auth/oauth/device"
TOKEN_URL = "https://allegro.pl/auth/oauth/token"


def get_code():
    try:
        payload = {'client_id': CLIENT_ID}
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        api_call_response = requests.post(CODE_URL, auth=(CLIENT_ID, CLIENT_SECRET),
                                          headers=headers, data=payload, verify=False)
        return api_call_response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_access_token(device_code):
    try:
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code', 'device_code': device_code}
        api_call_response = requests.post(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET),
                                          headers=headers, data=data, verify=False)
        return api_call_response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def await_for_access_token(interval, device_code):
    while True:
        time.sleep(interval)
        result_access_token = get_access_token(device_code)
        token = json.loads(result_access_token.text)
        if result_access_token.status_code == 400:
            if token['error'] == 'slow_down':
                interval += interval
            if token['error'] == 'access_denied':
                break
        else:
            return token['access_token']


def main():
    code = get_code()
    result = json.loads(code.text)
    print("User, open this address in the browser:" + result['verification_uri_complete'])
    access_token = await_for_access_token(int(result['interval']), result['device_code'])
    print("access_token = " + access_token)


if __name__ == "__main__":
    main()
```

zamknij

Python

### Client_credentials flow

W ramach OAuth2 udostępniliśmy ścieżkę, dzięki której możesz zautoryzować aplikację bez zgody użytkownika na jej działanie. W ten sposób uzyskasz dostęp do zasobów, które w [dokumentacji](https://developer.allegro.pl/documentation) w miejscu "Authorizations" oznaczyliśmy "bearer-token-for-application". Są to zasoby, które pozwalają na dostęp do publicznych danych, np. pobieranie listy kategorii itp.

Aby skorzystać z tej metody autoryzacji, musisz [zarejestrować aplikację](https://apps.developer.allegro.pl/), proces jest dokładnie taki sam jak w przypadku Authorization Code flow lub Device flow.

#### Autoryzacja aplikacji

Cały proces wygląda następująco:

1. Aplikacja zgłasza się po token - wykonuje żądanie HTTP metodą POST na adres: [https://allegro.pl/auth/oauth/token](https://allegro.pl/auth/oauth/token), gdzie musi:

- dołączyć nagłówek Authorization w formacie Basic [base64](http://base64encode.org/)(client_id:client_secret).
- podać wartość dla typu dostępu "grant_type=client_credentials",

Pamiętaj, aby zakodować ciąg "client_id:client_secret" wraz ze znakiem ":" pomiędzy wartościami.

```
curl -X POST \
  https://allegro.pl/auth/oauth/token \
  -H 'Authorization: Basic base64(clientId:secret)' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials'
```

2. Gdy prześlesz poprawnie żądanie, otrzymasz odpowiedź w formacie JSON, która zwiera m.in. token dostępowy. Skorzystaj z niego w zasobach REST API, które w [dokumentacji](https://developer.allegro.pl/documentation) w miejscu "Authorizations" oznaczyliśmy "bearer-token-for-application".

Przykładowy response:

```
{
  "access_token":"eyJ...dUA",  // token dostępowy, który pozwala wykonywać operacje na zasobach dostępnych publicznie
  "token_type":"bearer",   // typ tokena (w naszym przypadku: bearer)
  "expires_in":43199,   // czas ważności tokena dostępowego w sekundach (token jest ważny 12 godzin)
  "scope":"allegro_api",   // zasięg danych/funkcjonalności do których użytkownik autoryzował aplikacje
  "allegro_api": true,  // opcjonalne, w przyszłości całkowicie usuniemy - flaga wskazująca na fakt, że token został wygenerowany dla celów API (brak bezpośredniego zastosowania)
  "jti":"2184f3be-f6de-4a66-bd8f-b11347d7ba80"  // identyfikator tokena JWT (brak bezpośredniego zastosowania)
}
```

W przyszłości, w odpowiedzi mogą pojawić się dodatkowe pola.

Przykładowy kod realizujący autoryzację typu Client_credentials flow:

```
<?php
define('CLIENT_ID', ''); // wprowadź Client_ID aplikacji
define('CLIENT_SECRET', ''); // wprowadź Client_Secret aplikacji
define('TOKEN_URL', 'https://allegro.pl/auth/oauth/token'); 

function getCurl($headers, $content) {
    $ch = curl_init();
    curl_setopt_array($ch, array(
        CURLOPT_URL => TOKEN_URL,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $content
    ));
    return $ch;
}


function getAccessToken() 
{
    $authorization = base64_encode(CLIENT_ID.':'.CLIENT_SECRET);
    $headers = array("Authorization: Basic {$authorization}","Content-Type: application/x-www-form-urlencoded");
    $content = "grant_type=client_credentials";
    $ch = getCurl($headers, $content);
    $tokenResult = curl_exec($ch);
    $resultCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($tokenResult === false || $resultCode !== 200) {
        exit ("Something went wrong $resultCode $tokenResult");
    }
    return json_decode($tokenResult)->access_token;
}


function main()
{
    echo "access_token = ", getAccessToken();
}


main();
?>
```

zamknij

PHP

```
import requests
import json

CLIENT_ID = ""          # wprowadź Client_ID aplikacji
CLIENT_SECRET = ""      # wprowadź Client_Secret aplikacji
TOKEN_URL = "https://allegro.pl/auth/oauth/token"


def get_access_token():
    try:
        data = {'grant_type': 'client_credentials'}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False, allow_redirects=False, auth=(CLIENT_ID, CLIENT_SECRET))
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        return access_token
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def main():
    access_token = get_access_token()
    print("access token = " + access_token)


if __name__ == "__main__":
    main()
```

zamknij

Python

### Dynamic Client Registration

DCR to rozszerzenie standardu OAuth2 umożliwiające tworzenie instancji twojej aplikacji w sposób zautomatyzowany. Jeżeli klient bezpośrednio instaluje kopię twojego oprogramowania (np. instancję platformy sklepowej we własnej infrastrukturze), to ten typ autoryzacji jest właśnie dla ciebie. Zapewnia on pełne bezpieczeństwo autoryzacji danych, a jednocześnie nie wymusza na każdym kliencie ręcznego generowania osobnych danych dostępowych (client ID oraz client secret).

#### Rejestracja aplikacji typu DCR

1. Aby korzystać z autoryzacji DCR, twoje oprogramowanie musi przedstawiać się Software statement ID, czyli unikalnym identyfikatorem aplikacji. Żeby go uzyskać, skontaktuj się z nami ([formularz kontaktowy](https://allegro.pl/pomoc/kontakt)) i napisz, dlaczego potrzebujesz skorzystać z DCR.

Jako autor aplikacji swój osobisty identyfikator Software statement ID znajdziesz na liście aplikacji (Szablony aplikacji) na stronie [Zarządzanie aplikacjami Allegro](https://apps.developer.allegro.pl/).

#### DCR - autoryzacja użytkownika

2. Aby w pełni korzystać z DCR, użytkownik twojej aplikacji musi posiadać konto na Allegro. Poproś użytkownika aplikacji, aby wygenerował jednorazowy kod na stronie [Wygeneruj kod](https://allegro.pl/uzytkownik/bezpieczenstwo/wygeneruj-kod).

Kod jest ważny 2 minuty, w tym czasie użytkownik aplikacji musi go wprowadzić np. w procesie instalacji własnej instancji twojej aplikacji.

3a. Gdy aplikacja instaluje się u klienta, instalator musi wywołać POST [https://api.allegro.pl/register](https://api.allegro.pl/register) i przekazać:

client_name - nazwa instalowanej aplikacji:

- nie można zmienić nadanej nazwy aplikacji. Oznacza to, że np. przy aktualizacji aplikacji, nazwa musi pozostać ta sama.
- musi zawierać od 3 do 50 znaków,
- musi być unikatowa - we własnym zakresie zaproponuj unikatową w skali całego Allegro nazwę dla tej konkretnej instancji aplikacji, np. nazwa twojej aplikacji + id użytkownika + data,

Przykładowy request:

```
curl -X POST \
‘https://api.allegro.pl/register’ \
-H ‘Accept: appication/json’ \
-H ‘Content-Type: application/json’
-d ‘
{
    "code": "PXGTQBZXE_przykład",
    "client_name": "moj.sklep.com 12345678 23-07-2020",
    "redirect_uris": [
        "https://moj.sklep.com/AllegroCallbackUrl.php"
    ],
    "software_statement_id": "3b8cacc7-eeec-42f9-9f7f-f35090c3d616"
}’
```

3b. W odpowiedzi instalowana aplikacja otrzyma:

- software_statement_id - identyfikator aplikacji, który został uzyskany od Allegro, jednoznacznie wiążacy instancję aplikacji z twoją aplikacją.
- client_name - nazwa instalowanej aplikacji (zgodna z requestem),
- client_id i client_secret - dane dostępowe, które są unikatowe w obrębie instalacji. Instancja aplikacji powinna wykorzystywać je podczas procesu autoryzacji (code_flow),
- software_statement_id - identyfikator aplikacji, który został uzyskany od Allegro, jednoznacznie wiążacy instancję aplikacji z twoją aplikacją.

Zadbaj, by instancja aplikacji zachowała wygenerowane dane dostępowe i używała ich w komunikacji z Allegro REST API.

Wartość client_secret nie będzie widoczna na liście [Zarządzanie aplikacjami Allegro](https://apps.developer.allegro.pl/).

Przykładowy response zgodny z specyfikacją [Dynamic Client Registration](https://tools.ietf.org/html/rfc7591#section-3.2.1):

```
201 Created
Content-Type: application/json
{
    "client_id": "17a747e9b9f74f428ad0203a245e7373",
    "client_secret": "edSDERFsx43dSDJKFDKFJDKLSFJ4dsdsjdkIRIfffeEDfxc",
    "client_id_issued_at": 1594363740,
    "client_secret_expires_at": 0,
    "redirect_uris": [
        "https://moj.sklep.com/AllegroCallbackUrl.php"
    ],
    "grant_types": [
        "authorization_code",
        "implicit",
        "refresh_token",
        "client_credentials"
    ],
    "client_name": "moj.sklep.com 12345678 23-07-2020",
    "software_statement_id": "3b8cacc7-eeec-42f9-9f7f-f35090c3d616"
}
```

Podczas generowania danych dostępowych mogą wystąpić błędy:

- 422 “Nazwa aplikacji jest już wykorzystywana - podaj inną.” - przesłana nazwa aplikacji nie jest unikalna.
- 403 “Niepoprawny kod dostępu. Wygeneruj nowy kod i spróbuj ponownie.” - użytkownik podał nieprawidłowy jednorazowy kod podczas instalacji aplikacji;

4. Autoryzuj użytkownika z wykorzystaniem otrzymanego client_id oraz client_secret. W tym celu skorzystaj z autoryzacji typu Authorization Code flow.

### Scope w API Allegro

Scope'y to zakresy określające poziom uprawnień do korzystania z API Allegro. Każdy zakres ma przypisany zestaw uprawnień, który definiuje:

- zestaw operacji, które można wykonać w scope'ie.
- zestaw zasobów, do których można uzyskać dostęp za pomocą scope'a,

#### Lista dostępnych scope'ów

Poszczególne scope'y zapewniają dostęp do wykonania szeregu operacji, które są dla nich zdefiniowane. Dostępne obecnie w API Allegro scope'y to:

Zakres dostępu

Odczyt danych konta

Dostępne operacje

- Odczyt danych takich jak: login, imię i nazwisko, nazwa firmy - Odczyt dodatkowych adresów e-mail - Odczyt ocen oraz statystyk ocen

Zakres dostępu

Zmiana danych konta

Dostępne operacje

- Dodawanie i usuwanie dodatkowych adresów e-mail

Zakres dostępu

Odczyt danych o ofertach

Dostępne operacje

- Odczyt listy wystawionych ofert - Odczyt szczegółów wystawionych ofert - Odczyt zdarzeń o wystawionych ofertach - Odczyt bazy produktowej - Odczyt tabel kompatybilności - Odczyt dostępnych pakietów ogłoszeniowych - Odczyt prognozowanych opłat za ofertę - Podgląd rabatów i promocji - Podgląd zestawów ofert - Podgląd ofert wielowariantowych - Odczyt statystyk ogłoszeń

Zakres dostępu

Zarządzanie ofertami

Dostępne operacje

- Tworzenie, edycja, usuwanie ofert - Publikowanie i kończenie ofert - Tworzenie oferty powiązanej z produktem - Zgłaszanie propozycji nowych produktów - Grupowa edycja ofert - Dodawanie i usuwanie ofert wielowariantowych - Dodawanie, edycja i usuwanie rabatów i promocji - Dodawanie, edycja i usuwanie zestawów ofert

Zakres dostępu

Odczyt zamówień

Dostępne operacje

- Odczyt szczegółów zamówień - Odczyt dziennika zdarzeń o zamówieniach - Odczyt złożonych wniosków o rabat transakcyjny - Odczyt szczegółów przesyłek, protokołów, etykiet

Zakres dostępu

Zarządzanie zamówieniami

Dostępne operacje

- Dodawanie numerów listów przewozowych - Zmiana statusów zamówień - Składanie i anulowanie wniosków o rabat transakcyjny - Tworzenie i usuwanie przesyłek

Zakres dostępu

Odczyt informacji o przesyłkach

Dostępne operacje

- Odczyt danych przesyłek - Odczyt etykiet - Odczyt protokołów

Zakres dostępu

Zarządzanie przesyłkami

Dostępne operacje

- Tworzenie przesyłek - Zlecenie odbioru

Zakres dostępu

Zarządzanie ocenami i komentarzami

Dostępne operacje

- Odczyt ocen od kupujących - Odpowiedź na komentarze od kupujących - Prośba o anulowanie komentarza

Zakres dostępu

Zarządzanie sporami transakcyjnymi

Dostępne operacje

- Wyświetlanie sporów transakcyjnych, wiadomości i załączników - Odpowiadanie w sporach transakcyjnych i dodawanie załączników

Zakres dostępu

Zarządzanie licytacjami

Dostępne operacje

- Składanie ofert kupna w aukcjach - Podgląd złożonych ofert kupna

Zakres dostępu

Zarządzanie Centrum wiadomości

Dostępne operacje

- Odczyt listy wątków i wiadomości - Tworzenie, wysyłanie i usuwanie wiadomości - Pobieranie i dodawanie załączników do wiadomości

Zakres dostępu

Odczyt opłat Allegro

Dostępne operacje

- Podgląd salda i opłat na koncie Allegro - Podgląd naliczonych opłat za oferty

Zakres dostępu

Odczyt danych o płatnościach

Dostępne operacje

- Odczyt historii płatności - Odczyt wykonanych zwrotów płatności

Zakres dostępu

Zwrot wpłat do kupujących

Dostępne operacje

- Zwracanie wpłat do kupujących

Zakres dostępu

Odczyt ustawień sprzedaży

Dostępne operacje

- Odczyt tabel rozmiarów - Odczyt punktów odbioru - Odczyt kontaktów do ogłoszeń - Odczyt zdefiniowanych usług dodatkowych - Odczyt definicji polityki zwrotów, gwarancji i reklamacji - Odczyt cenników dostawy - Odczyt ustawień dotyczących dostawy - Odczyt tagów zdefiniowanych przez użytkownika

Zakres dostępu

Zmiana ustawień sprzedaży

Dostępne operacje

- Dodawanie, usuwanie i edycja punktów odbioru - Dodawanie i zmiana kontaktów ogłoszeniowych - Definiowanie i edycja usług dodatkowych - Definiowanie i edycja polityki zwrotów, gwarancji i reklamacji - Definiowanie cenników dostaw - Zmiana ustawień dotyczących dostawy - Dodawanie, edycja i usuwanie tagów ofertowych

Zakres dostępu

Zarządzanie kampaniami

Dostępne operacje

- Zgłaszanie i obsługa zgłoszeń do Strefy Okazji - Zgłaszanie i obsługa zgłoszeń ofert do kampanii, programów specjalnych i oznaczeń Allegro - Zarządzanie Allegro Ceny

Zakres dostępu

Odczyt informacji w One Fulfillment

Dostępne operacje

- Odczyt informacji o awizo (ASN) - Odczyt informacji o generowanych etykietach - Odczyt statusu wysyłki awizo - Odczyt postępu odbioru awizo przez magazyn - Odczyt stanów magazynowych - Odczyt informacji o dostępnych produktach

Zakres dostępu

Zarządzanie informacji w One Fulfillment

Dostępne operacje

- Tworzenie awizo (ASN) - Edycja awizo - Usuwanie awizo - Generowanie etykiet - Wysyłka awizo

Zakres dostępu

Odczyt danych z zasobów afiliacyjnych

Dostępne operacje

- Pobieranie informacji dla Allegro Affiliate Business

Zakres dostępu

Zarządzanie i edycja danych z zasobów afiliacyjnych

Dostępne operacje

- Zarządzanie danymi dla Allegro Affiliate Business

| Nazwa scope | Zakres dostępu | Dostępne operacje |
| --- | --- | --- |
| allegro:api:profile:read |
| allegro:api:profile:write |
| allegro:api:sale:offers:read |
| allegro:api:sale:offers:write |
| allegro:api:orders:read |
| allegro:api:orders:write |
| allegro:api:shipments:read |
| allegro:api:shipments:write |
| allegro:api:ratings |
| allegro:api:disputes |
| allegro:api:bids |
| allegro:api:messaging |
| allegro:api:billing:read |
| allegro:api:payments:read |
| allegro:api:payments:write |
| allegro:api:sale:settings:read |
| allegro:api:sale:settings:write |
| allegro:api:campaigns |
| allegro:api:fulfillment:read |
| allegro:api:fulfillment:write |
| allegro:api:affiliate:read |
| allegro:api:affiliate:write |

Wartość scope przypisaną do danego zasobu Allegro REST API znajdziesz w [dokumentacji](https://developer.allegro.pl/documentation).

#### Zarządzanie listą scope’ów aplikacji Allegro

Na stronie [Zarządzanie aplikacjami Allegro](https://apps.developer.allegro.pl/) możesz wybrać i edytować scope’y dla danej aplikacji. Dzięki temu określisz, z jakich funkcjonalności Twoja aplikacja będzie korzystać. Domyślnie każda aplikacja dodana przed 17.01.2022 ma zaznaczone wszystkie uprawnienia. Jeśli w przyszłości wprowadzimy nowy scope, nie dodamy go automatycznie. Sam zdecydujesz, czy Twoja aplikacja powinna z niego korzystać.

Jeśli podczas generowania tokena:

1. podasz węższy zakres niż zadeklarowałeś dla danej aplikacji - dostaniesz uprawnienie tylko na te funkcjonalności, które podałeś.
2. nie podasz konkretnych uprawnień - aplikacja będzie miała dostęp do wszystkich zadeklarowanych funkcjonalności,
3. podasz szerszy zakres niż przy deklaracji w [Developer Apps](https://apps.developer.allegro.pl/)- aplikacja będzie miała dostęp tylko do tych funkcjonalności, które wcześniej zadeklarowałeś,

#### Autoryzacja z wykorzystaniem scope

Dotychczas każda z aplikacji zarejestrowanych na stronie [Zarządzanie aplikacjami Allegro](https://apps.developer.allegro.pl/) prosiła o dostęp do wszystkich wymienionych w tabeli scope'ów. Teraz możesz wystąpić tylko o te scope'y, które faktycznie są niezbędne do prawidłowego funkcjonowania aplikacji. Jeżeli nie podejmiesz żadnych kroków, to twoja aplikacja będzie za każdym razem autoryzować się z pełną listą scope'ów - wyświetlimy je użytkownikowi na ekranie zgody (consent screen) podczas potwierdzania połączenia aplikacji z kontem użytkownika.

Aby ograniczyć dostęp aplikacji tylko do wybranych zasobów Allegro podczas uzyskiwania autoryzacji przekaż odpowiednie scope'y. Każdy kolejny scope oddziel spacją (“%20”).

Przykładowy request pozwalający na dostęp aplikacji tylko do zasobów do zarządzania ofertami oraz odczytu zamówień (dla Authorization Code flow):

```
https://allegro.pl/auth/oauth/authorize?response_type=code&redirect_uri=http://www.example.com&client_id=438f71d3a26e4d829783a0a621873465&scope=allegro:api:sale:offers:write%20allegro:api:orders:read
```

Ekran zgody w przypadku ograniczenia aplikacji do korzystania tylko z zasobów do zarządzania ofertami oraz odczytu zamówień:

### Wywołanie zasobu REST API

Aby w imieniu użytkownika wykonać żądanie do wybranego zasobu REST API, należy pamietać o przekazaniu tokena autoryzującego w nagłówku HTTP. Obok tokena niezbędne jest także przekazanie informacji o wersji zasobu, który nas interesuje:

```
curl -X GET \
  'https://api.allegro.pl/order/events' \
  -H 'Authorization: Bearer {token}' \
  -H 'accept: application/vnd.allegro.public.v1+json'
```

opis

Metoda HTTP, z którą wywoływany jest dany zasób (informację o niej znaleźć można w dokumentacji zasobu)

opis

Nagłówek HTTP: Authorization. Autoryzacja typu Bearer (zgodna z token_type zwracanym przy generowaniu tokena), wraz z otrzymanym z OAuth tokenem dostępowym

opis

Nagłówek Accept z odpowiednią wartością (wersją zasobu), niezbędny przy zapytaniach do API typu GET (informację o nim znaleźć można w dokumentacji zasobu)

opis

Wskazanie na konkretny zasób, który chcemy odpytać

| wartość | opis |
| --- | --- |
| GET |
| Authorization |
| Accept |
| [https://api.allegro.pl/order/events](https://api.allegro.pl/order/events) |

### Przedłużenie ważności tokena

Podstawowy token dostępowy (access_token) ważny jest 12 godzin. Aby nie zmuszać użytkownika do ponownej autoryzacji aplikacji dwa razy na dobę, udostępniamy również możliwość odświeżania tokenów - służy do tego refresh_token. Refresh token pozwala na uzyskanie nowego tokena dostępowego dla danego użytkownika w sposób dla użytkownika przezroczysty (bez konieczności ingerencji z jego strony). Token taki jest ważny przez 3 miesiące, po pierwszym odświeżeniu możesz z niego korzystać jeszcze przez 60 sekund.

Dzięki obsłudze tzw. odnawialnego czasu życia tokena, za każdym razem gdy używasz refresh token, w odpowiedzi otrzymasz nową parę - access token (ważny kolejne 12h ) oraz refresh token (ważny kolejne 3 miesiące).

Przykładowy request:

```
curl -X POST \
  https://allegro.pl/auth/oauth/token \
  -H 'Authorization: Basic base64(clientId:secret)' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=refresh_token&refresh_token={refresh_token}'
```

Przykładowy response:

```
{
  "access_token":"eyJ...dUA",   // token dostępowy, który pozwala wykonywać operacje na zasobach dostępnych publicznie
  "token_type":"bearer",  // typ tokena (w naszym przypadku: bearer)
  "refresh_token":"eyJ...QEQ",  // nowy refresh token jednorazowego użytku, pozwalający na przedłużenie ważności autoryzacji użytkownika dla aplikacji do max. 3 miesięcy
  "expires_in":43199,  // czas ważności tokena dostępowego w sekundach (token jest ważny 12 godzin)
  "scope":"allegro_api",  // zasięg danych/funkcjonalności do których użytkownik autoryzował aplikacje
  "allegro_api": true,  // flaga wskazująca na fakt, że token został wygenerowany dla celów API (brak bezpośredniego zastosowania)
  "jti":"2184f3be-f6de-4a66-bd8f-b11347d7ba80"  // identyfikator tokena JWT (brak bezpośredniego zastosowania)
}
```

Przykładowy kod realizujący odświeżanie tokena:

```
<?php

define('CLIENT_ID', ''); // wprowadź Client_ID aplikacji
define('CLIENT_SECRET', ''); // wprowadź Client_Secret aplikacji
define('REDIRECT_URI', ''); // wprowadź redirect_uri
define('AUTH_URL', 'https://allegro.pl/auth/oauth/authorize');
define('TOKEN_URL', 'https://allegro.pl/auth/oauth/token');


function getAuthorizationCode() {
    $authorization_redirect_url = AUTH_URL . "?response_type=code&client_id=" 
    . CLIENT_ID . "&redirect_uri=" . REDIRECT_URI;
    ?>
    <html>
    <body>
    <a href="<?php echo $authorization_redirect_url; ?>">Login to Allegro</a>
    </body>
    </html>
    <?php
}

function getCurl($headers, $content) {
    $ch = curl_init();
    curl_setopt_array($ch, array(
        CURLOPT_URL => TOKEN_URL,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $content
    ));
    return $ch;
}

function getRefreshToken($authorization_code) {
    $authorization = base64_encode(CLIENT_ID.':'.CLIENT_SECRET);
    $authorization_code = urlencode($authorization_code);
    $headers = array("Authorization: Basic {$authorization}","Content-Type: application/x-www-form-urlencoded");
    $content = "grant_type=authorization_code&code=${authorization_code}&redirect_uri=" . REDIRECT_URI;
    $ch = getCurl($headers, $content);
    $tokenResult = curl_exec($ch);
    $resultCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($tokenResult === false || $resultCode !== 200) {
        exit ("Something went wrong:  $resultCode $tokenResult");
    }
    return json_decode($tokenResult)->refresh_token;
}

function TokenRefresh($token) {
    $authorization = base64_encode(CLIENT_ID.':'.CLIENT_SECRET);
    $headers = array("Authorization: Basic {$authorization}","Content-Type: application/x-www-form-urlencoded");
    $content = "grant_type=refresh_token&refresh_token={$token}&redirect_uri=" . REDIRECT_URI;
    $ch = getCurl($headers, $content);
    $tokenResult = curl_exec($ch);
    $resultCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($tokenResult === false || $resultCode !== 200) {
        exit ("Something went wrong:  $resultCode $tokenResult");
    }

    return json_decode($tokenResult)->access_token;
}

function main(){
    if ($_GET["code"]) {
        $refreshToken = getRefreshToken($_GET["code"]);
        $nextToken= TokenRefresh($refreshToken);
        echo "access_token = ", $nextToken;
    } else {
        getAuthorizationCode();
    }
}

main();

?>
```

zamknij

PHP

```
import requests
import json

CLIENT_ID = ""          # wprowadź Client_ID aplikacji
CLIENT_SECRET = ""      # wprowadź Client_Secret aplikacji
REDIRECT_URI = ""       # wprowadź redirect_uri
AUTH_URL = "https://allegro.pl/auth/oauth/authorize"
TOKEN_URL = "https://allegro.pl/auth/oauth/token"


def get_authorization_code():
    authorization_redirect_url = AUTH_URL + '?response_type=code&client_id=' + CLIENT_ID + \
                                 '&redirect_uri=' + REDIRECT_URI
    print("Login to Allegro - use url in your browser and then enter authorization code from returned url: ")
    print("---  " + authorization_redirect_url + "  ---")
    authorization_code = input('code: ')
    return authorization_code


def get_refresh_token(authorization_code):
    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': REDIRECT_URI}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=False, auth=(CLIENT_ID, CLIENT_SECRET))
        tokens = json.loads(access_token_response.text)
        access_token = tokens['refresh_token']
        return access_token
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_next_token(token):
    try:
        data = {'grant_type': 'refresh_token', 'refresh_token': token, 'redirect_uri': REDIRECT_URI}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=False, auth=(CLIENT_ID, CLIENT_SECRET))
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        return access_token
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def main():
    authorization_code = get_authorization_code()
    refresh_token = get_refresh_token(authorization_code)
    print("refresh token = " + refresh_token)
    next_token = get_next_token(refresh_token)
    print("next access token = " + next_token)


if __name__ == "__main__":
    main()
```

zamknij

Python

### Kiedy token straci ważność

Poza standardowym scenariuszem, gdy token traci ważność ze względu na upływ 12 godzin lub z powodu użycia refresh tokena, wyróżniamy również dodatkowe sytuacje, kiedy użytkownik:

- przekroczy liczbę aktywnych sesji (max. 20 otwartych sesji dla jednego użytkownika).
- otrzyma blokadę sprzedaży,
- zmieni adres e-mail,
- zmieni hasło,
- wyloguje się ze wszystkich urządzeń, np. poprzez zakładkę [Logowanie i hasło](https://allegro.pl/moje-allegro/moje-konto/logowanie-i-haslo),

### Sprawdź, jakie aplikacje są powiązane z Twoim kontem Allegro

W dedykowanej zakładce " [Powiązane aplikacje](https://allegro.pl/moje-allegro/moje-konto/powiazane-aplikacje)” w “Moim Allegro” użytkownik może sprawdzić jakie aplikacje są powiązane z jego kontem.

### Usuń powiązanie danej aplikacji z Twoim kontem Allegro

W dedykowanej zakładce “ [Powiązane aplikacje](https://allegro.pl/moje-allegro/moje-konto/powiazane-aplikacje)” w “Moim Allegro” użytkownik może usunąć powiązanie aplikacji ze swoim kontem.

### FAQ

Dlaczego otrzymuję komunikat “nie możemy wyświetlić strony” wraz z numerem błędu, gdy chcę uzyskać 10 sekundowy kod do autoryzacji?

Upewnij się, że adres, który przekazujesz w redirect_uri jest taki sam, jak ten, który podałeś przy rejestracji aplikacji. Adresy przekierowań możesz sprawdzić oraz edytować na stronie [https://apps.developer.allegro.pl/](https://apps.developer.allegro.pl/). Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/zlq9e75GdIR).

Dlaczego, kiedy próbuję uzyskać token, w odpowiedzi otrzymuję komunikat “An authorization code must be supplied”?

Błąd wskazuje na to, że nieprawidłowo przekazujesz nazwę parametru code w URL, np.

[https://allegro.pl/auth/oauth/token?grant_type=authorization_code&codee=385MTAI0BQ16ZXSPUQ33qCot27xqNH1j&redirect_uri=http://localhojst:8080/exhange_code](https://allegro.pl/auth/oauth/token?grant_type=authorization_code&amp;codee=385MTAI0BQ16ZXSPUQ33qCot27xqNH1j&amp;redirect_uri=http://localhojst:8080/exhange_code)

lub nie przekazujesz go w ogóle. Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR).

Dlaczego, gdy próbuję uzyskać token, w odpowiedzi otrzymuję komunikat “Full authentication is required to access this resource”?

Upewnij się, że podajesz prawidłowy adres URL - [https://allegro.pl/auth/oauth/token?grant_type=authorization_code&code={code}&redirect_uri={redirect_uri}](https://allegro.pl/auth/oauth/token?grant_type=authorization_code&amp;code={code}&amp;redirect_uri={redirect_uri}). Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/zlq9e75GdIR).

W response otrzymuję status 401 Unauthorized / 403 Forbidden. Co może być przyczyną?

Sprawdź, czy jesteś zautoryzowany jako sprzedawca, do którego należą oferty, zamówienia, etc. (w zależności z którego zasobu korzystasz). W tym celu rozkoduj swój token - wpisz w wyszukiwarce “decode jwt token” i na jednej z dostępnych stron zweryfikuj wartość user_name po wklejeniu swojego tokena.

Zweryfikuj, jakiego typu autoryzacji wymagamy, aby skorzystać z danego zasobu. Tę informację znajdziesz w naszej [dokumentacji](https://developer.allegro.pl/documentation):

- bearer-token-for-application - [client_credentials](https://developer.allegro.pl/tutorials/zlq9e75GdIR#clientcredentials-flow).
- bearer-token-for-user - [code](https://developer.allegro.pl/tutorials/uwierzytelnianie-i-autoryzacja-zlq9e75GdIR#authorization-code-flow) lub [device](https://developer.allegro.pl/tutorials/zlq9e75GdIR#device-flow),

Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/zlq9e75GdIR).

Dlaczego w response otrzymuję komunikat “Cannot convert access token to JSON”?

Zweryfikuj, czy nie używasz tokena ze środowiska testowego na produkcyjnym lub odwrotnie. Więcej - w [naszym poradniku](https://developer.allegro.pl/tutorials/b21569boAI1#srodowisko-testowe).

W jakich sytuacjach Twój token może utracić ważność?

Dzieje się tak w przypadku:

- w wyniku przekroczenia liczby aktywnych sesji (max. 20 otwartych sesji dla jednego użytkownika).
- blokady sprzedaży,
- zmiany adresu e-mail,
- zmiany hasła,
- wylogowania się ze wszystkich urządzeń, np. poprzez zakładkę [Logowanie i hasło](https://allegro.pl/moje-allegro/moje-konto/logowanie-i-haslo),

Sytuacja dotyczy zarówno access_tokena, jak i refresh_tokena.

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