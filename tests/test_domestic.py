import unittest
from domestic import load_domestic, TABLES, WEIGHTS
from rates import quote, shipment, amounts
from surcharges import calculate_surcharges


class DomesticTest(unittest.TestCase):
    def setUp(self):
        self.rates, self.destinations = load_domestic()

    def quotes(self, weight, pallet=False):
        return quote(self.rates,self.destinations,'Binnenland','Nederland','1011AB',pallet,weight)

    def test_custom_only(self):
        rows = self.quotes(5)
        self.assertEqual(len(rows),3)
        self.assertEqual([r['base'] for r in rows],[4.46,9.71,46.39])
        self.assertEqual([r['row'] for r in rows],[8,6,4])
        self.assertTrue(all(len(prices)==len(WEIGHTS) for prices,_,_ in TABLES.values()))

    def test_brackets(self):
        for weight, charged, price in [(5.01,6,5.03),(30.01,35,10.87),(70,70,24.65),(70.5,70.5,24.61),(70.51,71,24.85),(100.1,101,35.35),(250.1,251,87.85),(500.1,501,175.35)]:
            with self.subTest(weight=weight):
                result=self.quotes(weight)[0]
                self.assertEqual(result['charged'],charged)
                self.assertAlmostEqual(result['base'],price)
        self.assertEqual(self.quotes(100000),[])

    def test_pallets(self):
        rows=self.quotes(200,True)
        self.assertEqual([r['base'] for r in rows],[94,342])
        self.assertEqual([r['row'] for r in rows],[11,10])

    def test_isolation(self):
        self.assertEqual(quote(self.rates,self.destinations,'Export','Germany','10115',False,5),[])

    def test_domestic_surcharges(self):
        line={'Aantal':2,'Lengte cm':170,'Breedte cm':80,'Hoogte cm':100,'Kg per stuk':100,'Niet stapelbaar':True}
        self.assertEqual(calculate_surcharges([line],True,'FedEx Priority Freight')[:2],(400,0))
        line['Lengte cm']=179
        self.assertEqual(calculate_surcharges([line],True,'FedEx Priority Express Freight')[:2],(510,110))
        self.assertEqual(amounts(4.46,10,20),[4.46,0.45,4.91,5.89,0.98])
