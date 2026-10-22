from pathlib import Path
import csv
import io
import hmac
import streamlit as st
from rates import load_book, shipment, quote, amounts
from surcharges import calculate_surcharges
from settings_store import DEFAULT, MODES, load, save

ROOT = Path(__file__).resolve().parent
BOOK = ROOT/'data'/'NL Courtesy-Net-Rates-15202126-English_TFF.xlsx'
st.set_page_config(page_title='FedEx tarieven', layout='wide')

def require_login():
    try:
        password = st.secrets.get('APP_PASSWORD', '')
    except FileNotFoundError:
        password = ''
    if not isinstance(password, str) or not password:
        st.title('FedEx tarieven')
        st.warning('Toegang nog niet ingesteld. Voeg APP_PASSWORD toe aan Streamlit Secrets.')
        st.stop()
    if st.session_state.get('authenticated', False):
        if st.sidebar.button('Uitloggen'):
            st.session_state.clear()
            st.rerun()
        return
    st.title('FedEx tarieven')
    with st.form('login'):
        entered = st.text_input('Wachtwoord', type='password')
        submitted = st.form_submit_button('Inloggen')
    if submitted:
        if hmac.compare_digest(entered.encode('utf-8'), password.encode('utf-8')):
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error('Wachtwoord klopt niet.')
    st.stop()

require_login()

token = str(st.secrets.get('GITHUB_TOKEN', '')).strip()
if 'saved_settings' not in st.session_state:
    try:
        settings, sha = load(token) if token else (dict(DEFAULT), None)
        st.session_state['saved_settings'] = settings
        st.session_state['settings_sha'] = sha
    except (ValueError, KeyError) as exc:
        st.error(f'Instellingen niet geladen: {exc}')
        st.stop()
settings = st.session_state['saved_settings']

@st.cache_data
def cached_book(stamp):
    return load_book(BOOK)

st.title('FedEx tarieven')
st.caption('FedEx · TFF · NL Courtesy Net Rates · EUR')
rates, destinations = cached_book(BOOK.stat().st_mtime_ns)
with st.sidebar:
    st.subheader('Tariefbron')
    st.write('NL Courtesy Net Rates')
    st.caption('Ingangsdatum: 27 januari 2026 · locatie ZWO')
    st.download_button('Excel downloaden', BOOK.read_bytes(), file_name=BOOK.name)
    st.divider()
    fuel = st.number_input('Fuel surcharge %', min_value=0.0, value=settings['fuel'], step=0.1, format='%.2f', key='fuel')
    margin = st.number_input('Winstmarge %', min_value=0.0, value=settings['margin'], step=0.5, format='%.2f', key='margin')
    margin_mode = st.selectbox('Margebasis', MODES, index=MODES.index(settings['mode']), key='margin_mode')
    if not token:
        st.info('Permanent opslaan vereist GITHUB_TOKEN in Streamlit Secrets.')
    if st.button('Instellingen opslaan', disabled=not token):
        try:
            data = {'fuel':fuel,'margin':margin,'mode':margin_mode}
            st.session_state['settings_sha'] = save(token,data,st.session_state['settings_sha'])
            st.session_state['saved_settings'] = data
            st.success('Fuel en marge permanent opgeslagen.')
        except (ValueError, KeyError) as exc:
            st.error(str(exc))

a,b,c = st.columns([1,2,1])
direction = a.selectbox('Richting', ['Export','Import'])
countries = sorted({d['country'] for d in destinations if d['direction']==direction})
country = b.selectbox('Bestemmingsland' if direction=='Export' else 'Land van herkomst', countries, index=countries.index('Germany'))
postcode = c.text_input('Postcode', '10115')
kind = st.radio('Zendingstype',['Pakket','Pallet'], horizontal=True)
pallet = kind=='Pallet'
st.subheader('Zending')
defaults = [{'Aantal':1,'Lengte cm':120.0 if pallet else 40.0,'Breedte cm':80.0 if pallet else 30.0,'Hoogte cm':100.0 if pallet else 20.0,'Kg per stuk':100.0 if pallet else 5.0}]
flag = 'Niet stapelbaar' if pallet else 'Afwijkende verpakking'
defaults[0][flag] = False
lines = st.data_editor(defaults, num_rows='dynamic', hide_index=True, use_container_width=True, key=f'lines_{kind}', column_config={
    'Aantal':st.column_config.NumberColumn(min_value=1,step=1,required=True),
    flag:st.column_config.CheckboxColumn(default=False, help='EUR 200 per niet-stapelbare pallet.' if pallet else 'Bijvoorbeeld geen kartonnen buitendoos, folie, cilindervorm, banden of uitstekende delen.'),
    **{k:st.column_config.NumberColumn(min_value=0.01,required=True) for k in defaults[0] if k not in ('Aantal',flag)}})
try:
    actual,volume,weight,count = shipment(lines,pallet)
except ValueError as exc:
    st.warning(str(exc))
    st.stop()
columns = st.columns(4)
for col,label,value in zip(columns,['Aantal','Werkelijk gewicht','Volume','Tariefgewicht'],[f'{count:g}',f'{actual:.2f} kg',f'{volume:.3f} m3',f'{weight:.2f} kg']):
    col.metric(label,value)
st.caption('Volumegewicht: L × B × H / 5.000. Hoogste gewicht per stuk; Freight minimaal 68 kg per pallet, bijkomende behandeling afmetingen minimaal 18 kg per pakket.')
results = quote(rates,destinations,direction,country,postcode,pallet,weight)
if not results:
    st.warning('Geen passend tarief. Controleer land, volledige postcode en gewicht; deze service of zone kan ontbreken in de staffel.')
    st.stop()
rows=[]
surcharge_details=[]
for r in results:
    extra, fuel_extra, details = calculate_surcharges(lines,pallet,r['service'])
    surcharge_details.extend({'Service':r['service'],**detail} for detail in details)
    try:
        base,surcharge,purchase,sale,profit = amounts(r['base'],fuel,margin,margin_mode,extra,fuel_extra)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    rows.append({'Service':r['service'],'Zone':r['zone'],'Tarief kg':r['charged'],'Basis EUR':base,'Toeslagen EUR':extra,'Fuel EUR':surcharge,'Inkoop EUR':purchase,'Verkoop EUR':sale,'Winst EUR':profit,'Excel-rij':r['row']})
rows.sort(key=lambda row:row['Inkoop EUR'])
st.subheader('Tarieven')
cols = st.columns(3)
cols[0].metric('Laagste inkoop',f"EUR {rows[0]['Inkoop EUR']:.2f}")
cols[1].metric('Verkoop',f"EUR {rows[0]['Verkoop EUR']:.2f}")
cols[2].metric('Winst',f"EUR {rows[0]['Winst EUR']:.2f}")
st.dataframe(rows,hide_index=True,use_container_width=True)
if surcharge_details:
    with st.expander('Specificatie toeslagen'):
        st.dataframe(surcharge_details,hide_index=True,use_container_width=True)
out=io.StringIO()
writer=csv.DictWriter(out,fieldnames=list(rows[0]),delimiter=';')
writer.writeheader()
writer.writerows(rows)
st.download_button('Vergelijking downloaden',out.getvalue().encode('utf-8-sig'),file_name='courtesy_tarieven.csv',mime='text/csv')
with st.expander('Berekening en voorwaarden'):
    st.write('Inkoop = basistarief + toeslagen + (basistarief + fuelplichtige toeslagen) × fuelpercentage / 100. Niet-stapelbaar valt buiten de fuelgrondslag.')
    st.write('Verkoop = inkoop × (1 + opslag / 100).' if margin_mode=='Opslag op inkoop' else 'Verkoop = inkoop / (1 - marge / 100).')
    st.write('Indicatieve net rates en toeslagen uit de aangeleverde offerte. Exclusief buitengebied, third-party billing, adrescorrectie, aangegeven waarde, grote vraag, btw, invoerrechten en niet-opgenomen diensten. Servicebeschikbaarheid en maximale afmetingen moeten bij FedEx worden bevestigd.')
    st.link_button('FedEx toeslagregels 2026','https://www.fedex.com/nl-nl/shipping/rates/fedex-rates.html')
    st.link_button('FedEx fuelgrondslag','https://www.fedex.com/nl-nl/shipping/surcharges.html')
    st.write('Alle ingevoerde regels vormen samen een zending. Afmetingen zijn inclusief verpakking/pallet.')
    st.link_button('FedEx gewichten en afmetingen','https://images.fedex.com/content/dam/fedex/international/rates/fedex-rates-domestic-en-nl.pdf')
