"""Proposal 281995, CUSTOM only, valid 22 October 2026; amounts in EUR.

Customer confirmed the fixed weight rows are shipment totals, not per-kg rates.
Source PDF pages 4-11. Preserve the quoted 70.5 kg Priority price verbatim.
"""

WEIGHTS = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5] + list(range(6, 31)) + [35, 40, 45, 50, 55, 60, 65, 70, 70.5]
TABLES = {
    'D1': ([46.39]*10 + [46.77,47.15,47.53,47.91,48.30,48.68,49.06,49.44,49.82,
        50.20,50.59,50.97,51.35,51.73,52.11,52.50,52.88,53.26,53.64,54.02,
        54.40,54.79,55.17,55.55,55.89,62.57,69.24,75.92,82.59,89.27,95.94,102.62,109.29,115.63], 1.63, 4),
    'D2': ([9.71]*10 + [10.25,10.40,10.55,10.70,10.85,12.52,12.69,12.86,13.03,
        13.20,13.37,13.54,13.71,13.88,14.05,14.23,14.40,14.57,14.74,14.91,
        15.08,15.25,15.42,15.59,15.75,16.89,19.57,22.26,24.94,27.63,30.31,32.99,35.68,38.29], 0.54, 6),
    'D3': ([4.46]*10 + [5.03,5.12,5.21,5.30,5.39,5.97,6.07,6.17,6.27,
        6.37,6.47,6.57,6.67,6.77,6.87,7.51,7.62,7.73,7.84,7.94,
        8.05,8.16,8.26,8.37,8.47,10.87,12.84,14.81,16.78,18.75,20.71,22.68,24.65,24.61], 0.35, 8),
}


def load_domestic():
    rates = []
    def add(service, low, high, price, per_kg, page):
        rates.append(dict(service=service, direction='Binnenland', zone='1',
                          low=low, high=high, price=price, per_kg=per_kg, row=page))
    for service, (prices, per_kg, page) in TABLES.items():
        for weight, price in zip(WEIGHTS, prices, strict=True):
            add(service, 0, weight, price, False, page if weight <= 14 else page+1)
        for low, high in [(71,100),(100.001,250),(250.001,500),(500.001,99999)]:
            add(service, low, high, per_kg, True, page+1)
    for service, price, page in [('D4F',1.71,10),('D5F',0.47,11)]:
        for low, high in [(68,70),(70.001,100),(100.001,300),(300.001,500),(500.001,99999)]:
            add(service, low, high, price, True, page)
    destinations = [dict(direction='Binnenland', country='Nederland', low=None,
                         high=None, zones={s:'1' for s in [*TABLES,'D4F','D5F']}, row=3)]
    return rates, destinations
