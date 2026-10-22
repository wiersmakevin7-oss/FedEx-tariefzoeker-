import base64
import json
import math
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

URL = 'https://api.github.com/repos/wiersmakevin7-oss/FedEx-tariefzoeker-/contents/courtesy_settings.json'
MODES = ['Opslag op inkoop', 'Marge op verkoop']
DEFAULT = {'fuel': 0.0, 'margin': 0.0, 'mode': MODES[0]}

def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Ongeldig instellingenbestand.')
    result = dict(DEFAULT, **data)
    for key in ('fuel', 'margin'):
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('Percentages moeten positieve getallen of nul zijn.')
        result[key] = float(value)
    if result['mode'] not in MODES or (result['mode']==MODES[1] and result['margin']>=100):
        raise ValueError('Controleer de margebasis en het margepercentage.')
    return {key: result[key] for key in DEFAULT}

def request(token, method='GET', body=None):
    req = Request(URL + ('?ref=main' if method=='GET' else ''),
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization':f'Bearer {token}', 'Accept':'application/vnd.github+json',
                 'Content-Type':'application/json', 'User-Agent':'Courtesy-Tariefzoeker'}, method=method)
    try:
        with urlopen(req, timeout=15) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code==404 and method=='GET':
            return None
        message = {401:'GitHub-token is ongeldig of verlopen.',403:'GitHub-token mist Contents: Read and write voor FedEx-tariefzoeker-.',409:'Instellingen zijn intussen gewijzigd. Herlaad de app voor je opnieuw opslaat.'}.get(exc.code, f'GitHub-opslag mislukt (HTTP {exc.code}).')
        raise ValueError(message) from None
    except (URLError, TimeoutError):
        raise ValueError('GitHub is niet bereikbaar. Probeer het later opnieuw.') from None

def load(token):
    payload = request(token)
    if payload is None:
        return dict(DEFAULT), None
    return validate(json.loads(base64.b64decode(payload['content']))), payload['sha']

def save(token, data, sha):
    if not token:
        raise ValueError('Voeg GITHUB_TOKEN toe aan Streamlit Secrets om permanent op te slaan.')
    body = {'message':'Update Courtesy fuel and margin', 'branch':'main',
            'content':base64.b64encode(json.dumps(validate(data),indent=2).encode()).decode()}
    if sha:
        body['sha']=sha
    return request(token,'PUT',body)['content']['sha']
