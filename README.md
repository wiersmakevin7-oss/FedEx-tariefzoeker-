# Courtesy Tariefzoeker

Zelfstandige Streamlit-app met het aangeleverde FedEx NL Courtesy Net Rates bestand.
Start: `python -m streamlit run app.py --server.port 8504`.

Export/import, pakket/Freight, meerdere regels, postcodezones, fuel en winstmarge.
De Excel in data wordt automatisch geladen. Package-tabellen worden gebruikt voor
pakketten, Freight-tabellen voor pallets; Pak en Envelope worden uitgesloten.
Gewichtstaffels naar boven; per-kilo intervallen vermenigvuldigd met hele kg naar boven.
Volumegewicht met cm naar boven afgerond / 5000; minimaal 68 kg per Freight-eenheid.
Controleer contractafwijkingen en servicebeschikbaarheid bij FedEx.

Fuel wordt over basis plus fuelplichtige handlingtoeslagen berekend. Margebasis is expliciet selecteerbaar: opslag op
inkoop of marge als percentage van verkoop. Afronding van geld naar 2 decimalen.
Zendinginvoer blijft binnen de browsersessie; fuel en marge kunnen worden opgeslagen.
Tariefbron: ingangsdatum 27 januari 2026, locatie ZWO, niet-bindende courtesy rates.

Test: `python -m unittest discover -s tests`.

## Streamlit Community Cloud

- Repository: `wiersmakevin7-oss/FedEx-tariefzoeker-`
- Branch: `main`
- Main file path: `app.py`

De Excel in `data/` is inbegrepen; uploaden is niet nodig.
Invoerwaarden worden alleen in de browsersessie bewaard.

## Wachtwoord

Voeg bij Streamlit Cloud Settings > Secrets toe:

```toml
APP_PASSWORD = "kies_een_eigen_wachtwoord"
```

Zonder ingesteld wachtwoord blijft de tariefzoeker geblokkeerd. Lokaal plaats
je dezelfde instelling in `.streamlit/secrets.toml` (uitgesloten van Git).
De login beschermt de app; een openbare GitHub-repository blijft openbaar.

## Fuel en marge bewaren

Voeg ook `GITHUB_TOKEN = "jouw_token"` toe aan Secrets. Gebruik een fine-grained
token met Contents: Read and write op `wiersmakevin7-oss/FedEx-tariefzoeker-`.
De knop Instellingen opslaan bewaart fuel, marge en margebasis in
`courtesy_settings.json` op main. Nieuwe sessies laden deze gedeelde waarden.
Zonder token werkt rekenen wel, maar permanent opslaan is uitgeschakeld.
Het instellingenbestand heeft dezelfde zichtbaarheid als de repository.

## Toeslagen 2026

Bedragen uit de aangeleverde `fedex toeslagen.pdf` (3 pagina's): pakketten
afmetingen EUR 35, verpakking EUR 25, werkelijk gewicht boven 25 kg EUR 36,
buitenmaats EUR 55. Per pakket geldt alleen de hoogste toepasselijke toeslag.
Afmetingencriteria geven minimaal 18 kg tariefgewicht per pakket, ook wanneer
een andere toeslag hoger is. Afmetingen worden naar hele cm boven afgerond.
Afwijkende verpakking is handmatig aan te vinken per regel.

Vracht: EUR 55 per eenheid boven 157 cm langste zijde, voor Regional Economy
Freight boven 178 cm (voetnoot 10). Niet-stapelbaar is optioneel per palletregel:
EUR 200 per eenheid, naast eventuele vrachtbehandeling, zonder fuel hierover.
Het aantal op een regel geldt ook voor de aangevinkte eigenschap.

Fuel geldt op basis en handling/buitenmaats; marge volgt op volledige inkoop.
Uitgesloten op verzoek: buitengebied, third-party billing, adrescorrectie,
aangegeven waarde en grote vraag. Geen andere diensten uit uitgebreidere
FedEx-lijsten toegevoegd. De prijs is geen bevestiging van acceptatie door FedEx.

Aanvullende bronnen voor samenloop, voetnoten en fuelgrondslag:
- https://www.fedex.com/nl-nl/shipping/rates/fedex-rates.html
- https://www.fedex.com/nl-nl/shipping/surcharges.html
- https://www.fedex.com/content/dam/fedex/international/rates/new-offer-rates-vassuis-nl-nl.pdf
