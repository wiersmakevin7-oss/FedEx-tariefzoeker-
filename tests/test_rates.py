import unittest
from pathlib import Path
from rates import load_book, quote, resolve_zone, amounts, shipment

class RatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r, cls.d = load_book(next((Path(__file__).resolve().parents[1]/'data').glob('*.xlsx')))

    def test_package_source(self):
        q=quote(self.r,self.d,'Export','Germany','10115',False,5)
        self.assertEqual(q[0]['base'],6.47)
        self.assertEqual(q[0]['row'],582)
        self.assertEqual(quote(self.r,self.d,'Export','Germany','10115',False,5.01)[0]['charged'],6)

    def test_freight(self):
        q=quote(self.r,self.d,'Export','Germany','10115',True,200)
        self.assertEqual(q[0]['base'],128)
        self.assertEqual(q[0]['row'],696)

    def test_postcode(self):
        self.assertEqual(resolve_zone(self.d,'Export','France','75001','RE'),'S')
        self.assertEqual(resolve_zone(self.d,'Export','France','01000','RE'),'T')
        self.assertIsNone(resolve_zone(self.d,'Export','France','','RE'))

    def test_money(self):
        self.assertEqual(amounts(173,26.4,10),[173,45.67,218.67,240.54,21.87])
        self.assertEqual(amounts(100,10,20,'Marge op verkoop'),[100,10,110,137.5,27.5])
        with self.assertRaises(ValueError): amounts(100,0,100,'Marge op verkoop')

    def test_dimensions(self):
        line={'Aantal':2,'Lengte cm':120,'Breedte cm':80,'Hoogte cm':100,'Kg per stuk':100}
        self.assertEqual(shipment([line],True)[2],384)
        with self.assertRaises(ValueError): shipment([line],False)

if __name__=='__main__': unittest.main()
