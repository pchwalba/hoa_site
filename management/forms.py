from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import WaterReadouts, Apartment, Fees, ApartmentUser, Balance, ApartmentBalance, CentralHeatingSurcharge, \
    ParkingCard, Occupancy, BigFamilyCard, AssociationBalance
from .validators import file_extension_validator


class AdminSummaryForm(forms.Form):
    only_not_paid = forms.BooleanField(required=False, )
    fields = {"only_not_paid"}


class AdminSelectApartmentYearForm(forms.Form):
    qs = WaterReadouts.objects.dates('readout_date', 'year')
    qs = qs[1:]
    years = [(value.year, value.year) for value in qs]
    years.insert(0, (None, "Wszystkie"))
    qs = Apartment.objects.values('number').all()
    apartments = [(nr['number'], nr['number']) for nr in qs]
    apartments.insert(0, (None, "Wszystkie"))
    months = [(month, month) for month in range(1, 13)]
    months.insert(0, (None, "-----"))
    apartment = forms.ChoiceField(required=False, choices=apartments)
    start_date = forms.ChoiceField(required=False, choices=months)
    end_date = forms.ChoiceField(required=False, choices=months)
    year = forms.ChoiceField(required=False, choices=years)

    fields = {'apartment', 'year', 'start_date', 'end_date'}


class SummaryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(SummaryForm, self).__init__(*args, **kwargs)
        self.fields['readout_dates'].queryset = WaterReadouts.objects.filter(
            apartment=self.request.user.apartment).order_by('readout_date')

    class Meta:
        model = WaterReadouts
        fields = {'readout_dates'}

    readout_dates = forms.ModelChoiceField(queryset=None)


class RegisterForm(UserCreationForm):
    class Meta:
        model = ApartmentUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone']


class WaterReadoutsForm(forms.ModelForm):
    class Meta:
        model = WaterReadouts
        fields = ['apartment', 'readout_date', 'cold_water_readout', 'new_cold_water_meter', 'hot_water_readout',
                  'new_hot_water_meter', ]
        widgets = {'readout_date': forms.TextInput(attrs={'type': 'date'})}


class FeesForm(forms.ModelForm):
    class Meta:
        model = Fees
        fields = '__all__'
        widgets = {'period': forms.TextInput(attrs={'type': 'date'}), }


class TransactionHistoryForm(forms.Form):
    types_of_transaction = list(Balance.TYPES_OF_TRANSACTION)
    types_of_transaction.insert(0, (None, "Dowolny"))
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    type_of_transaction = forms.ChoiceField(required=False, choices=types_of_transaction)
    fields = ['start_date', 'end_date', 'type_of_transaction']


class ApartmentBalanceHistoryForm(TransactionHistoryForm):
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.values_list('number', flat=True), required=False)
    fields = ['apartment', 'start_date', 'end_date', 'type_of_transaction']


class AssociationBalanceHistoryForm(TransactionHistoryForm):
    fields = ['start_date', 'end_date', 'type_of_transaction']


class AssociationBalanceForm(forms.ModelForm):
    class Meta:
        model = AssociationBalance
        fields = ['date', 'type_of_transaction', 'title', 'amount']
        widgets = {'date': forms.TextInput(attrs={'type': 'datetime-local'})}


class ApartmentBalanceForm(forms.ModelForm):
    class Meta:
        model = ApartmentBalance
        fields = ['apartment', 'date', 'type_of_transaction', 'title', 'amount']


class CalculatePaymentsForm(ApartmentBalanceForm):
    class Meta:
        model = ApartmentBalance
        fields = ['date', 'type_of_transaction', 'title']
        widgets = {'date': forms.TextInput(attrs={'type': 'date'}), }


class CentralHeatingSurchargeCreateForm(forms.ModelForm):
    class Meta:
        model = CentralHeatingSurcharge
        fields = ['apartment', 'start_date', 'end_date', 'amount']
        widgets = {'start_date': forms.TextInput(attrs={'type': 'date'}),
                   'end_date': forms.TextInput(attrs={'type': 'date'})}


class ParkingCardForm(forms.ModelForm):
    class Meta:
        model = ParkingCard
        fields = ['apartment', 'start_date', 'number_of_cards']
        widgets = {'start_date': forms.TextInput(attrs={'type': 'date'})}


class OccupancyForm(forms.ModelForm):
    class Meta:
        model = Occupancy
        fields = ['apartment', 'start_date', 'occupants']
        widgets = {'start_date': forms.TextInput(attrs={'type': 'date'})}


class BigFamilyCardForm(forms.ModelForm):
    class Meta:
        model = BigFamilyCard
        fields = ['apartment', 'start_date', 'amount']
        widgets = {'start_date': forms.TextInput(attrs={'type': 'date'})}


class WaterReadoutsImportForm(forms.Form):
    file = forms.FileField(validators=[file_extension_validator])
    fields = {'file'}
