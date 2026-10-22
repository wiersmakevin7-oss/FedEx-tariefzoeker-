"""Read the supplied FedEx report without evaluating workbook instructions."""
import math
import re
from decimal import Decimal, ROUND_HALF_UP
import openpyxl
from surcharges import package_dimensions

SERVICES = {
    'D1': 'FedEx First', 'D2': 'FedEx Priority Express', 'D3': 'FedEx Priority',
    'D4F': 'FedEx Priority Express Freight', 'D5F': 'FedEx Priority Freight',
    'IPE': 'International Priority Express', 'IP': 'International Priority',
    'IE': 'International Economy', 'RE': 'Regional Economy',
    'IPF': 'International Priority Freight', 'IEF': 'International Economy Freight',
    'REF': 'Regional Economy Freight', 'FDF': 'International Deferred Freight',
}

def number(value):
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace('.', '').replace(',', '.'))
    except (ValueError, TypeError):
        return None

def load_book(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rates, destinations = [], []
    service = direction = section = None
    zone_columns, country_columns = {}, {}
    chart = False
    try:
        for rowno, row in enumerate(wb['Report'].values, 1):
            text = str(row[0] or '').strip()
            if text.startswith('FedEx ') and (' Export' in text or ' Import' in text):
                direction = 'Export' if ' Export' in text else 'Import'
                service = next((k for k,v in sorted(SERVICES.items(), key=lambda x: -len(x[1])) if v in text), None)
                section, chart, zone_columns = None, False, {}
            if 'Zone Chart' in text:
                chart = True
                direction = 'Export' if 'Export' in text else 'Import'
                country_columns = {}
            if chart:
                if text == 'Country/Territory':
                    country_columns = {i:str(v).strip() for i,v in enumerate(row) if str(v).strip() in SERVICES}
                elif country_columns and text and not text.startswith(('Agreement No.', 'Netherlands', '"')):
                    zones = {s:str(row[i]).strip() for i,s in country_columns.items() if row[i] and str(row[i]).strip()}
                    if zones:
                        match = re.fullmatch(r'(.+) ([0-9A-Z]+)-([0-9A-Z]+)', text)
                        country, low, high = match.groups() if match else (text, None, None)
                        destinations.append(dict(direction=direction, country=country, low=low, high=high, zones=zones, row=rowno))
                continue
            if text == 'Kgs':
                zone_columns = {i:str(v).strip() for i,v in enumerate(row) if i and v and str(v).strip()}
            if text in ('Package', 'Pak', 'Envelope'):
                section = text
            interval = re.fullmatch(r'([\d,.]+)\s*-\s*([\d,.]+)', text)
            weight = float(row[0]) if isinstance(row[0], (int,float)) else None
            if not service or not zone_columns or not (interval or (weight and section == 'Package')):
                continue
            low, high = (float(v.replace(',', '')) for v in interval.groups()) if interval else (0, weight)
            for col, zone in zone_columns.items():
                price = number(row[col])
                if price is not None and price > 0:
                    rates.append(dict(service=service, direction=direction, zone=zone, low=low, high=high, price=price, per_kg=bool(interval), row=rowno))
    finally:
        wb.close()
    return rates, destinations

def resolve_zone(destinations, direction, country, postcode, service):
    candidates = [d for d in destinations if d['direction']==direction and d['country']==country and service in d['zones']]
    ranged = [d for d in candidates if d['low'] is not None]
    if ranged:
        pc = re.sub(r'\s', '', postcode.upper())
        for d in ranged:
            if d['low'].isdigit():
                ok = pc.isdigit() and len(pc)==len(d['low']) and int(d['low'])<=int(pc)<=int(d['high'])
            else:
                prefix = re.match(r'[A-Z]+', pc)
                ok = bool(prefix and d['low']<=prefix[0]<=d['high'])
            if ok:
                return d['zones'][service]
        return None
    return next((d['zones'][service] for d in candidates if d['low'] is None), None)

def shipment(lines, pallet):
    actual = volume = billable = 0.0
    count = 0
    for line in lines:
        qty, length, width, height, kg = (line[k] for k in ('Aantal','Lengte cm','Breedte cm','Hoogte cm','Kg per stuk'))
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in (qty,length,width,height,kg)) or int(qty)!=qty:
            raise ValueError('Vul voor elke regel een positief aantal, afmetingen en gewicht in.')
        if not pallet and kg>68:
            raise ValueError('Een pakket boven 68 kg moet als pallet/Freight worden aangeboden.')
        dim = math.ceil(length)*math.ceil(width)*math.ceil(height)/5000
        actual += qty*kg
        volume += qty*length*width*height/1e6
        minimum = 68 if pallet else (18 if package_dimensions(line)[0] else 0)
        billable += qty*max(kg,dim,minimum)
        count += qty
    if not count:
        raise ValueError('Voeg minimaal een pakket of pallet toe.')
    return actual, volume, billable, count

def quote(rates, destinations, direction, country, postcode, pallet, weight):
    results = []
    for service in SERVICES:
        if ('F' in service) != pallet:
            continue
        zone = resolve_zone(destinations,direction,country,postcode,service)
        options = [r for r in rates if r['direction']==direction and r['service']==service and r['zone']==zone]
        fixed = sorted((r for r in options if not r['per_kg'] and r['high']>=weight-1e-9), key=lambda r:r['high'])
        if fixed:
            r = fixed[0]
            charged, base = r['high'], r['price']
        else:
            charged = math.ceil(weight-1e-9)
            r = next((r for r in options if r['per_kg'] and r['low']<=charged<=r['high']), None)
            if not r:
                continue
            base = r['price']*charged
        results.append(dict(service=SERVICES[service],zone=zone,base=base,charged=charged,rate=r['price'],row=r['row'],per_kg=r['per_kg']))
    return sorted(results,key=lambda r:r['base'])

def amounts(base, fuel, margin, mode='Opslag op inkoop', extra=0, fuel_extra=0):
    base,fuel,margin = map(lambda x:Decimal(str(x)), (base,fuel,margin))
    surcharge = (base + Decimal(str(fuel_extra)))*fuel/100
    purchase = base+surcharge+Decimal(str(extra))
    if mode=='Marge op verkoop':
        if margin>=100:
            raise ValueError('Marge op verkoop moet lager zijn dan 100%.')
        sale = purchase/(1-margin/100)
    else:
        sale = purchase*(1+margin/100)
    return [float(x.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)) for x in (base,surcharge,purchase,sale,sale-purchase)]
