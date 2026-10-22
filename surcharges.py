"""Contract amounts from the supplied 2026 FedEx surcharge PDF (EUR)."""
import math


def package_dimensions(line):
    length, width, height = sorted(
        (math.ceil(line[k]) for k in ('Lengte cm', 'Breedte cm', 'Hoogte cm')),
        reverse=True,
    )
    volume = length * width * height
    girth = length + 2 * width + 2 * height
    handling = length > 121 or width > 76 or girth > 266 or volume > 169901
    oversize = length > 243 or girth > 330 or volume > 283168 or line['Kg per stuk'] > 50
    return handling, oversize


def calculate_surcharges(lines, pallet, service=''):
    details = []
    for index, line in enumerate(lines, 1):
        qty = int(line['Aantal'])
        charges = []
        if pallet:
            limit = 178 if service == 'Regional Economy Freight' else 157
            if max(line[k] for k in ('Lengte cm', 'Breedte cm', 'Hoogte cm')) > limit:
                charges.append(('Bijkomende behandeling vracht', 55, True))
            if line.get('Niet stapelbaar', False):
                charges.append(('Niet stapelbaar', 200, False))
        else:
            dimension, oversize = package_dimensions(line)
            candidates = []
            if dimension:
                candidates.append(('Bijkomende behandeling afmetingen', 35, True))
            if line.get('Afwijkende verpakking', False):
                candidates.append(('Bijkomende behandeling verpakking', 25, True))
            if line['Kg per stuk'] > 25:
                candidates.append(('Bijkomende behandeling gewicht', 36, True))
            if oversize:
                candidates.append(('Buitenmaatse afmetingen', 55, True))
            # FedEx 2026: only the highest package handling/oversize charge applies.
            if candidates:
                charges.append(max(candidates, key=lambda charge: charge[1]))
        for label, rate, fuel in charges:
            details.append({'Regel': index, 'Toeslag': label, 'Aantal': qty,
                            'Per stuk EUR': rate, 'Totaal EUR': qty * rate,
                            'Fuel van toepassing': fuel})
    total = sum(d['Totaal EUR'] for d in details)
    fuel_base = sum(d['Totaal EUR'] for d in details if d['Fuel van toepassing'])
    return total, fuel_base, details
