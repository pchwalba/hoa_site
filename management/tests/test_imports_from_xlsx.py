from django.test import TestCase, Client
from management.models import WaterReadouts, Apartment
from management.utils import import_water_readouts, calculate_water_usage
import datetime
from openpyxl import load_workbook


class TestWaterReadouts(TestCase):
    def setUp(self):
        self.apartment = Apartment.objects.create(number=1, area=53, acc_number=123456)

        self.water_readouts = WaterReadouts.objects.create(readout_date=datetime.date.today(),
                                                           hot_water_readout=123,
                                                           cold_water_readout=11,
                                                           new_cold_water_meter=False,
                                                           new_hot_water_meter=False,
                                                           apartment=Apartment.objects.get(number=1))

    def test_create_water_readouts(self):
        self.assertIsInstance(self.water_readouts, WaterReadouts)


class TestImportFromXlsx(TestCase):
    def setUp(self):
        self.file = 'test_files/water_22.xlsx'
        for number in range(1, 41):
            Apartment.objects.create(number=number, area=53, acc_number=123456)

    def test_import_from_xlsx(self):
        print(WaterReadouts.objects.count())
        import_water_readouts(self.file)
        print(WaterReadouts.objects.count())
        print(WaterReadouts.objects.filter(apartment__number=40).latest('readout_date').hot_water_readout)


class TestNewWaterMeters(TestCase):
    def setUp(self):
        self.file = 'test_files/water_readouts.xlsx'
        for number in range(1, 41):
            Apartment.objects.create(number=number, area=53, acc_number=123456)

    def test_new_water_meter(self):
        import_water_readouts(self.file)
        water_usage = WaterReadouts.objects.filter(apartment__number=15).order_by('-readout_date')
        hot, cold, x, y = calculate_water_usage(water_usage)
        print(f'Hot water: {hot}, Cold water: {cold}')
        WaterReadouts.objects.create(readout_date=datetime.date.today(),
                                     apartment=Apartment.objects.get(number=15),
                                     new_cold_water_meter=False,
                                     new_hot_water_meter=False,
                                     hot_water_readout=1,
                                     cold_water_readout=2)

        cold, hot, x, y = calculate_water_usage(water_usage)
        print(f'Hot water: {hot}, Cold water: {cold}')
