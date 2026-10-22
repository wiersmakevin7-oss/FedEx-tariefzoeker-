# Courtesy Tariefzoeker

Zelfstandige Streamlit-app met het aangeleverde FedEx NL Courtesy Net Rates bestand.
Start: `python -m streamlit run app.py --server.port 8504`.

Export/import, pakket/Freight, meerdere regels, postcodezones, fuel en winstmarge.
De Excel in data wordt automatisch geladen. Package-tabellen worden gebruikt voor
pakketten, Freight-tabellen voor pallets; Pak en Envelope worden uitgesloten.
Gewichtstaffels naar boven; per-kilo intervallen vermenigvuldigd met hele kg naar boven.
Volumegewicht met cm naar boven afgerond / 5000; minimaal 68 kg per Freight-eenheid.
Controleer contractafwijkingen en servicebeschikbaarheid bij FedEx.

Fuel wordt over basis berekend. Margebasis is expliciet selecteerbaar: opslag op
inkoop of marge als percentage van verkoop. Afronding van geld naar 2 decimalen.
Invoeren blijven binnen de browsersessie; geen cloudinstellingen of publicatie.
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
