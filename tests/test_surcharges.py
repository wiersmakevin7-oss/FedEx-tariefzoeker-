import unittest
from surcharges import calculate_surcharges, package_dimensions
from rates import amounts, shipment


def line(length=40, width=30, height=20, kg=5, qty=1, **flags):
    return {'Aantal':qty, 'Lengte cm':length, 'Breedte cm':width,
            'Hoogte cm':height, 'Kg per stuk':kg, **flags}


class SurchargesTest(unittest.TestCase):
    def test_normal_and_packaging(self):
        self.assertEqual(calculate_surcharges([line()],False)[:2],(0,0))
        self.assertEqual(calculate_surcharges([line(qty=2, **{'Afwijkende verpakking':True})],False)[:2],(50,50))

    def test_weight_boundaries(self):
        for kg, expected in [(25,0),(25.01,36),(50,36),(50.01,55),(68,55)]:
            with self.subTest(kg=kg):
                self.assertEqual(calculate_surcharges([line(kg=kg)],False)[0],expected)

    def test_dimensions_and_minimum(self):
        self.assertFalse(package_dimensions(line(121,10,10))[0])
        self.assertTrue(package_dimensions(line(122,10,10))[0])
        self.assertFalse(package_dimensions(line(76,76,1))[0])
        self.assertTrue(package_dimensions(line(77,77,1))[0])
        self.assertFalse(package_dimensions(line(100,50,33))[0])
        self.assertTrue(package_dimensions(line(100,50,34))[0])
        self.assertFalse(package_dimensions(line(243,1,1))[1])
        self.assertTrue(package_dimensions(line(244,1,1))[1])
        self.assertFalse(package_dimensions(line(200,33,32))[1])
        self.assertTrue(package_dimensions(line(200,34,32))[1])
        self.assertEqual(shipment([line(122,10,10,qty=2)],False)[2],36)

    def test_volume_and_highest_only(self):
        self.assertTrue(package_dimensions(line(60,60,48))[0])
        self.assertTrue(package_dimensions(line(66,66,66))[1])
        item=line(122,10,10,kg=26,qty=3,**{'Afwijkende verpakking':True})
        total, fuel, details=calculate_surcharges([item],False)
        self.assertEqual((total,fuel,len(details)),(108,108,1))

    def test_freight_service_threshold_and_nonstackable(self):
        item=line(170,80,100,100,qty=2,**{'Niet stapelbaar':True})
        self.assertEqual(calculate_surcharges([item],True,'International Economy Freight')[:2],(510,110))
        self.assertEqual(calculate_surcharges([item],True,'Regional Economy Freight')[:2],(400,0))
        for length, service, expected in [(157,'',0),(158,'',55),(178,'Regional Economy Freight',0),(179,'Regional Economy Freight',55)]:
            self.assertEqual(calculate_surcharges([line(length,80,100,100)],True,service)[0],expected)

    def test_mixed_rows_and_fuel_margin(self):
        self.assertEqual(calculate_surcharges([line(),line(kg=26,qty=2)],False)[0],72)
        self.assertEqual(amounts(100,10,20,extra=255,fuel_extra=55),[100,15.5,370.5,444.6,74.1])
        self.assertEqual(amounts(100,10,20,'Marge op verkoop',255,55),[100,15.5,370.5,463.13,92.63])
