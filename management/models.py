from django.db import models
from django.contrib.auth.models import AbstractUser
import datetime
import uuid
from django.core.exceptions import ObjectDoesNotExist
from .validators import phone_number_validator


# Create your models here.


class Apartment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.IntegerField(unique=True, verbose_name="Numer mieszkania", help_text="Apartment number.")
    area = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Powierzchnia mieszkania",
                               help_text="Apartment surface area.")
    acc_number = models.IntegerField(verbose_name="Nr konta do przelewów")

    class Meta:
        ordering = ('number',)

    def create_new_apartment_balance(self):
        obj = ApartmentBalance.objects.create(apartment=self,
                                              date=datetime.date.today(),
                                              title='Bilans otwarcia',
                                              type_of_transaction='BO',
                                              amount=0)

    @property
    def get_latest_balance(self):
        if self.apartmentbalance_set.all():
            return self.apartmentbalance_set.latest('id')
        self.create_new_apartment_balance()
        return self.apartmentbalance_set.latest('id')

    @property
    def get_latest_water_readouts(self):
        return self.waterreadouts_set.latest('readout_date')

    @property
    def get_latest_occupancy(self):
        return self.occupancy_set.latest('start_date')

    @property
    def get_latest_parking_card(self):
        return self.parkingcard_set.latest('start_date')

    @property
    def get_latest_big_family_card(self):
        return self.bigfamilycard_set.latest('start_date')

    def __str__(self):
        return f"{self.number}"


class TypesOfTransaction(models.Model):
    type = models.CharField(max_length=200)


class Balance(models.Model):
    TYPES_OF_TRANSACTION = (
        ("BO", "Bilans otwarcia"),
        ("BANK", "Bank"),
        ("COMPENSATION", "Kompensata"),
        ("HWCH", "CO/CW"),
        ("CORRECTION", "Korekta"),
    )

    date = models.DateTimeField(verbose_name="Data transakcji")
    title = models.CharField(max_length=200, verbose_name="Tytuł")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota")
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bilans")
    type_of_transaction = models.CharField(max_length=30, choices=TYPES_OF_TRANSACTION, verbose_name="Typ transakcji")

    class Meta:
        abstract = True


class ApartmentBalance(Balance):
    apartment = models.ForeignKey(Apartment, on_delete=models.PROTECT, verbose_name="Mieszkanie")

    def save(self, *args, **kwargs):
        try:
            prev_balance = ApartmentBalance.objects.filter(apartment=self.apartment).latest('id')
            self.balance = prev_balance.balance + self.amount
        except ObjectDoesNotExist:
            self.balance = self.amount

        return super(ApartmentBalance, self).save(*args, **kwargs)

    def add_to_association_balance(self):
        return AssociationBalance.objects.create(date=self.date,
                                                 title=self.title,
                                                 amount=self.amount,
                                                 type_of_transaction=self.type_of_transaction)

    def __str__(self):
        return f"Mieszkanie: {self.apartment} Kwota ostatniej transakcji: {self.amount}  Balans po operacji:{self.balance}"


class AssociationBalance(Balance):
    description = models.CharField(max_length=200, verbose_name="Opis", blank=True, null=True)
    counterparty = models.CharField(max_length=200, verbose_name="Kontrahent")

    def save(self, *args, **kwargs):
        try:
            prev_balance = AssociationBalance.objects.all().latest('id')
            self.balance = prev_balance.balance + self.amount
        except ObjectDoesNotExist:
            self.balance = self.amount

        return super(AssociationBalance, self).save(*args, **kwargs)


class ApartmentUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.IntegerField(verbose_name="Numer telefonu", null=True, validators=(phone_number_validator,))
    apartment = models.ForeignKey(Apartment, on_delete=models.SET_NULL, null=True, verbose_name="Mieszkanie")

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Fees(models.Model):
    period = models.DateField(verbose_name="Okres")
    maintenance_fee = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Opłata eksploatacyjna ",
                                          help_text="Maintenance fee per m2.")
    repair_fund = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Fundusz remontowy",
                                      help_text="Repair found per m2.")
    central_heating = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Centralne ogrzewanie",
                                          help_text="Central heating per m2.")
    cold_water = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Zimna woda",
                                     help_text="Cold water per m3.")
    hot_water = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Ciepła woda",
                                    help_text="Hot water per m3")
    garbage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Śmieci",
                                  help_text="Garbage fee per tenant")
    parking_fee = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Opłata parkingowa")

    def __str__(self):
        return f"{self.period}"


class WaterReadouts(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.PROTECT, verbose_name="Mieszkanie")
    readout_date = models.DateField(verbose_name="Data odczytu")
    hot_water_readout = models.IntegerField(verbose_name="Ciepła woda")
    cold_water_readout = models.IntegerField(verbose_name="Zimna woda")
    new_cold_water_meter = models.BooleanField(verbose_name="Nowy licznik zimnej wody", default=False)
    new_hot_water_meter = models.BooleanField(verbose_name="Nowy licznik ciepłej wody", default=False)

    def __str__(self):
        return f"{self.apartment} - {self.readout_date}"

    @property
    def get_hot_water_readout(self):
        return self.hot_water_readout

    @property
    def get_cold_water_readout(self):
        return self.cold_water_readout

    @property
    def get_water_readout(self):
        """:returns: cold_water, hot_water """
        return self.cold_water_readout, self.hot_water_readout


class Occupancy(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.PROTECT, verbose_name="Mieszkanie")
    start_date = models.DateField(verbose_name="Od")
    occupants = models.IntegerField(verbose_name="Ilość mieszkańców")

    def __str__(self):
        return f"{self.apartment} - {self.occupants}: {self.start_date}"


class ParkingCard(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.PROTECT, verbose_name="Mieszkanie")
    start_date = models.DateField(verbose_name="Od")
    number_of_cards = models.IntegerField(verbose_name="Ilość kart parkingowych")


class BigFamilyCard(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.PROTECT, verbose_name="Mieszkanie")
    start_date = models.DateField(verbose_name="Od")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota")


class CentralHeatingSurcharge(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.PROTECT, verbose_name="Mieszkanie")
    start_date = models.DateField(verbose_name="Od")
    end_date = models.DateField(verbose_name="Do")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota")
    amount_per_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name="Kwota miesięczna")

    @property
    def number_of_payments(self):
        return (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month) + 1

    @property
    def last_payment(self):
        return self.amount - (self.number_of_payments - 1) * self.amount_per_month

    def save(self, *args, **kwargs):
        self.amount_per_month = self.amount / self.number_of_payments
        return super(CentralHeatingSurcharge, self).save(*args, **kwargs)

    def __str__(self):
        return f"Mieszkanie nr.:{self.apartment} Do zapłaty: {self.amount}"
