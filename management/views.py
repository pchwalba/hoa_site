from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, ListView, CreateView, UpdateView
from django.views.generic import View
from django.views.generic.edit import FormMixin

from .forms import *
from .models import *
from .utils import calculate_fees, import_water_readouts, html_to_pdf

# Create your views here.
DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'


class SelectApartmentYearFormMixin(FormMixin):
    """adds form for selecting apartment and year in tables"""
    form_class = AdminSelectApartmentYearForm

    def get_initial(self):
        initial = {
            'apartment': self.request.GET.get('apartment'),
            'year': self.request.GET.get('year'),
        }
        return initial


class AdminStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff


class MyLoginView(LoginView):

    def get_success_url(self):
        return reverse_lazy('overview')

    def form_invalid(self, form):
        messages.error(self.request, "Niepoprawny login lub hasło")
        return super().form_invalid(form)


class MyRegisterView(SuccessMessageMixin, CreateView):
    template_name = "register.html"
    form_class = RegisterForm
    success_message = "Konto utworzone pomyślnie. Skontaktuj się z administratorem w celu aktywacji."

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_active = False
        self.object.save()
        return super(MyRegisterView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('base')


class Overview(LoginRequiredMixin, TemplateView):
    template_name = "overview.html"


class WaterReadoutsAdminView(AdminStaffRequiredMixin, SelectApartmentYearFormMixin, ListView):
    template_name = "water-readouts.html"

    def get_queryset(self):
        if self.request.GET.get('apartment') == '0' or not self.request.GET.get('apartment'):
            queryset = Apartment.objects.all()
            queryset = [query.get_latest_water_readouts for query in queryset]
        else:
            queryset = WaterReadouts.objects.filter(apartment__number=self.request.GET.get('apartment'),
                                                    readout_date__year=self.request.GET.get('year'))
        return queryset


class WaterReadoutsView(LoginRequiredMixin, ListView):
    template_name = "water-readouts.html"
    model = WaterReadouts

    def get_queryset(self):
        queryset = [self.request.user.apartment.get_latest_water_readouts]

        return queryset


class WaterReadoutsCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = WaterReadouts
    template_name = "form-template-menu-on-the-left.html"
    form_class = WaterReadoutsForm
    success_message = "Odczyt wody dodany pomyślnie."
    success_url = reverse_lazy('water-readouts')

    def get_initial(self, **kwargs):
        user = self.request.user
        initial = {'readout_date': datetime.date.today()}
        if user.is_staff:
            initial['apartment'] = Apartment.objects.get(number=self.kwargs.get('apartment_number'))
            return initial

        initial['apartment'] = user.apartment
        return initial


class WaterReadoutsEdit(AdminStaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = WaterReadouts
    template_name = "form-template-menu-on-the-left.html"
    form_class = WaterReadoutsForm
    success_message = "Odczyt wody zmodyfikowany pomyślnie."
    success_url = reverse_lazy('water-readouts')


class FeesView(LoginRequiredMixin, DetailView):
    model = Fees
    template_name = "fees-overview.html"

    def get_object(self, queryset=None):
        obj = Fees.objects.latest('period')
        return obj


class FeesCreate(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Fees
    template_name = 'fees-create.html'
    form_class = FeesForm
    success_message = "Opłaty dodane pomyślnie."

    def get_initial(self):
        initial = Fees.objects.values().latest('period')
        initial.pop('id')
        initial['period'] = datetime.date.today()
        return initial

    def get_success_url(self):
        return reverse_lazy('fees')


class FeesHistoryView(AdminStaffRequiredMixin, ListView):
    model = Fees
    template_name = 'fees-history.html'
    queryset = Fees.objects.all().order_by('-period')
    paginate_by = 20


class AdminSummaryView(AdminStaffRequiredMixin, FormMixin, ListView):
    template_name = 'admin-summary.html'
    queryset = Apartment.objects.all()
    form_class = AdminSummaryForm

    def get_queryset(self):

        if self.request.POST.get('only_not_paid'):
            queryset = Apartment.objects.all()
            qs = [obj.get_latest_balance for obj in queryset if obj.get_latest_balance.balance > 0]
        else:
            queryset = Apartment.objects.all()
            qs = [obj.get_latest_balance for obj in queryset]

        return qs

    def post(self, request):
        self.object_list = self.get_queryset()
        context = self.get_context_data(object=self.object_list)
        return self.render_to_response(context)


class AdminYearlySummaryView(AdminStaffRequiredMixin, SelectApartmentYearFormMixin, ListView):
    template_name = 'admin-yearly-summary.html'

    def get_queryset(self):
        if self.request.GET.get('year'):
            queryset = WaterReadouts.objects.filter(readout_date__year=self.request.GET.get('year'),
                                                    apartment__number=self.request.GET.get('apartment'))
        else:
            queryset = WaterReadouts.objects.filter(readout_date__year='2023', apartment__number=1)
        if self.request.GET.get('start_date'):
            queryset = queryset.filter(readout_date__month__gte=self.request.GET.get('start_date'))
        if self.request.GET.get('end_date'):
            queryset = queryset.filter(readout_date__month__lte=self.request.GET.get('end_date'))

        queryset = (calculate_fees(readout.apartment, readout.id) for readout in queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(AdminYearlySummaryView, self).get_context_data()
        context['number_of_apartments'] = Apartment.objects.all().count()
        context['balance'] = Apartment.objects.get(number=self.request.GET.get('apartment')).get_latest_balance
        return context


class GenerateYearlySummaryPdf(AdminStaffRequiredMixin, View):
    def get_queryset(self):
        if self.request.GET.get('year'):
            queryset = WaterReadouts.objects.filter(readout_date__year=self.request.GET.get('year'),
                                                    apartment__number=self.request.GET.get('apartment'))
        else:
            queryset = WaterReadouts.objects.filter(readout_date__year=2023, apartment__number=1)
        if self.request.GET.get('start_date'):
            queryset = queryset.filter(readout_date__month__gte=self.request.GET.get('start_date'))
        if self.request.GET.get('end_date'):
            queryset = queryset.filter(readout_date__month__lte=self.request.GET.get('end_date'))

        queryset = [calculate_fees(readout.apartment, readout.id) for readout in queryset]
        return queryset

    def get(self, request, *args, **kwargs):
        context = {'data': self.get_queryset(),
                   'balance': Apartment.objects.get(number=self.request.GET.get('apartment')).get_latest_balance,
                   'apartment': self.request.GET.get('apartment')}
        open('templates/temp.html', "w", encoding='utf-8').write(render_to_string('summary-template.html', context))

        # Converting the HTML template into a PDF file
        pdf = html_to_pdf('temp.html')

        # rendering the template
        return HttpResponse(pdf, content_type='application/pdf')


class SummaryView(LoginRequiredMixin, FormMixin, DetailView):
    template_name = 'summary.html'
    form_class = SummaryForm

    def get_form_kwargs(self):
        kwargs = super(SummaryView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_object(self, queryset=None):
        date = None
        if self.request.method == 'POST':
            date = self.request.POST.get('readout_dates')
        user = self.request.user
        obj = calculate_fees(user.apartment, date)
        return obj

    def post(self, request):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class CalculatePayments(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "form-template-menu-on-the-left.html"
    form_class = CalculatePaymentsForm
    success_message = "Bilans został zaktualizowany"
    success_url = reverse_lazy('')

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        apartments = Apartment.objects.all()
        for apartment in apartments:
            balance = calculate_fees(apartment)
            ApartmentBalance.objects.create(apartment=apartment,
                                            date=cleaned_data['date'],
                                            title=cleaned_data['title'],
                                            amount=balance['total'],
                                            type_of_transaction=cleaned_data['type_of_transaction']
                                            )
        messages.success(self.request, "Bilans został zaktualizowany.")
        return HttpResponseRedirect(reverse_lazy('admin-summary'))


class ApartmentBalanceView(AdminStaffRequiredMixin, FormMixin, ListView):
    template_name = 'apartment-balance.html'
    form_class = ApartmentBalanceHistoryForm
    paginate_by = 40

    def get_initial(self):
        initial = {'apartment': self.request.GET.get('apartment'),
                   'start_date': self.request.GET.get('start_date'),
                   'end_date': self.request.GET.get('end_date'),
                   'type_of_transaction': self.request.GET.get('type_of_transaction')}
        return initial

    def get_queryset(self):
        queryset = ApartmentBalance.objects.all().order_by('-id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        apartment = self.request.GET.get('apartment')
        type_of_transaction = self.request.GET.get('type_of_transaction')
        if apartment:
            queryset = queryset.filter(apartment__number=apartment)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if type_of_transaction:
            queryset = queryset.filter(type_of_transaction=type_of_transaction)
        return queryset

    def post(self, request):
        self.object_list = self.get_queryset()
        context = self.get_context_data(object=self.object_list)
        return self.render_to_response(context)


class ApartmentBalanceCreate(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = ApartmentBalance
    form_class = ApartmentBalanceForm
    template_name = 'form-template-menu-on-the-left.html'
    success_message = 'Dodano pomyślnie'
    success_url = reverse_lazy('admin-summary')

    def get_initial(self, **kwargs):
        initial = {'apartment': Apartment.objects.get(number=self.kwargs.get('apartment_number')),
                   'date': datetime.date.today()}
        return initial


class CalculateSinglePayment(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = ApartmentBalanceForm
    template_name = 'calculate-single-payment.html'
    success_message = 'Opłata dodana pomyślnie'
    success_url = reverse_lazy('admin-summary')

    def get_initial(self, **kwargs):
        obj = self.get_object()
        initial = {'apartment': Apartment.objects.get(number=self.kwargs.get('apartment_number')),
                   'date': datetime.date.today(),
                   'amount': f"{obj['total']:.2f}"}
        return initial

    def get_context_data(self, **kwargs):
        context = super(CalculateSinglePayment, self).get_context_data(**kwargs)
        context['fees'] = self.get_object()
        return context

    def get_object(self, queryset=None):
        obj = calculate_fees(apt=Apartment.objects.get(number=self.kwargs.get('apartment_number')))
        return obj


class AssociationBalanceView(AdminStaffRequiredMixin, FormMixin, ListView):
    template_name = 'association-balance.html'
    model = AssociationBalance
    form_class = TransactionHistoryForm

    def get_initial(self):
        initial = {'apartment': self.request.GET.get('apartment'),
                   'start_date': self.request.GET.get('start_date'),
                   'end_date': self.request.GET.get('end_date'),
                   'type_of_transaction': self.request.GET.get('type_of_transaction')}
        return initial

    def get_queryset(self):
        queryset = AssociationBalance.objects.all().order_by('-id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        type_of_transaction = self.request.GET.get('type_of_transaction')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if type_of_transaction:
            queryset = queryset.filter(type_of_transaction=type_of_transaction)
        return queryset


class AssociationBalanceCreate(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = AssociationBalance
    form_class = AssociationBalanceForm
    AssociationFormSet = modelformset_factory(model=AssociationBalance, form=AssociationBalanceForm, extra=3)
    template_name = 'form-multiple.html'
    success_message = 'Dodano pomyślnie'

    def get_context_data(self, **kwargs):
        if self.request.POST:
            formset = self.AssociationFormSet(self.request.POST)
            context = {}
        else:
            context = super(AssociationBalanceCreate, self).get_context_data(**kwargs)
            formset = self.AssociationFormSet(queryset=AssociationBalance.objects.none())

        context['formset'] = formset
        return context

    def post(self, request, *args, **kwargs):
        formset = self.AssociationFormSet(request.POST)
        if formset.is_valid():
            return self.form_valid(formset)
        else:
            return self.form_invalid(formset)

    def get_success_url(self):
        return reverse_lazy('association-balance')


class CentralHeatingSurchargeView(AdminStaffRequiredMixin, SelectApartmentYearFormMixin, ListView):
    model = CentralHeatingSurcharge
    template_name = 'central-heating-surcharge-list.html'

    def get_queryset(self):
        if self.request.GET.get('year'):
            if self.request.GET.get('apartment') == '':
                queryset = CentralHeatingSurcharge.objects.all()
            else:
                queryset = CentralHeatingSurcharge.objects.filter(start_date__year=self.request.GET.get('year'),
                                                                  apartment__number=self.request.GET.get('apartment'))
        else:
            queryset = CentralHeatingSurcharge.objects.filter(start_date__year=datetime.date.today().year).order_by(
                'apartment')
        return queryset


class CentralHeatingSurchargeCreate(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = CentralHeatingSurcharge
    form_class = CentralHeatingSurchargeCreateForm
    template_name = 'form-template-menu-on-the-left.html'
    success_url = reverse_lazy('central-heating-surcharge')

    def get_success_message(self, cleaned_data):
        return f"Dopłata dla mieszkania nr. {self.object.apartment.number} została dodana pomyślnie."

    def get_initial(self, **kwargs):
        if self.kwargs.get('apartment_number'):
            initial = {'apartment': Apartment.objects.get(number=self.kwargs.get('apartment_number')), }
            return initial


class CentralHeatingSurchargeEdit(AdminStaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CentralHeatingSurcharge
    form_class = CentralHeatingSurchargeCreateForm
    template_name = 'form-template-menu-on-the-left.html'
    success_url = reverse_lazy('central-heating-surcharge')

    def get_success_message(self, cleaned_data):
        return f"Dopłata dla mieszkania nr. {self.object.apartment.number} została edytowana pomyślnie."


class ParkingCardView(AdminStaffRequiredMixin, SelectApartmentYearFormMixin, ListView):
    model = ParkingCard
    template_name = 'parking-cards.html'

    def get_queryset(self):
        if self.request.GET.get('apartment'):
            queryset = ParkingCard.objects.filter(apartment__number=self.request.GET.get('apartment')).order_by(
                '-start_date')
            if self.request.GET.get('year'):
                queryset = queryset.filter(start_date__year=self.request.GET.get('year'))
        else:
            queryset = ParkingCard.objects.all().order_by('apartment__number')
            if self.request.GET.get('year'):
                queryset = queryset.filter(start_date__year=self.request.GET.get('year'))
        return queryset


class ParkingCardEdit(AdminStaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ParkingCard
    form_class = ParkingCardForm
    success_message = "Karta edytowana pomyślnie."
    success_url = reverse_lazy('parking-card')
    template_name = 'form-template-menu-on-the-left.html'


class ParkingCardCreate(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = ParkingCard
    form_class = ParkingCardForm
    success_message = "Karta dodana pomyślnie."
    success_url = reverse_lazy('parking-card')
    template_name = 'form-template-menu-on-the-left.html'

    def get_initial(self, **kwargs):
        if self.kwargs.get('apartment_number'):
            initial = {'apartment': Apartment.objects.get(number=self.kwargs.get('apartment_number'))}
            return initial


class BigFamilyCardView(AdminStaffRequiredMixin, SelectApartmentYearFormMixin, ListView):
    model = BigFamilyCard
    template_name = 'big-family-cards.html'

    def get_queryset(self):
        if self.request.GET.get('apartment'):
            queryset = BigFamilyCard.objects.filter(apartment__number=self.request.GET.get('apartment')).order_by(
                'start_date')
            if self.request.GET.get('year'):
                queryset = queryset.filter(start_date__year=self.request.GET.get('year'))
        else:
            queryset = BigFamilyCard.objects.all()
            if self.request.GET.get('year'):
                queryset = queryset.filter(start_date__year=self.request.GET.get('year'))
        return queryset


class BigFamilyCardEdit(AdminStaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ParkingCard
    form_class = BigFamilyCardForm
    success_message = "Karta edytowana pomyślnie."
    success_url = reverse_lazy('big-family-card')
    template_name = 'form-template-menu-on-the-left.html'


class BigFamilyCardCreate(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = ParkingCard
    form_class = BigFamilyCardForm
    success_message = "Karta dodana pomyślnie."
    success_url = reverse_lazy('big-family-card')
    template_name = 'form-template-menu-on-the-left.html'

    def get_initial(self, **kwargs):
        if self.kwargs.get('apartment_number'):
            initial = {'apartment': Apartment.objects.get(number=self.kwargs.get('apartment_number'))}
            return initial


class OccupancyView(AdminStaffRequiredMixin, SelectApartmentYearFormMixin, ListView):
    model = Occupancy
    template_name = 'occupancy.html'

    def get_queryset(self):
        if self.request.GET.get('year'):
            if self.request.GET.get('apartment') == '':
                queryset = Occupancy.objects.filter(start_date__year=self.request.GET.get('year'))

            else:
                queryset = Occupancy.objects.filter(start_date__year=self.request.GET.get('year'),
                                                    apartment__number=self.request.GET.get('apartment')).order_by(
                    "apartment")
        else:
            queryset = [apartment.get_latest_occupancy for apartment in Apartment.objects.all()]
        return queryset


class OccupancyCreate(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Occupancy
    template_name = 'form-template-menu-on-the-left.html'
    form_class = OccupancyForm
    success_message = "Liczba mieszkańców dodana pomyślnie"
    success_url = reverse_lazy('occupancy')

    def get_initial(self, **kwargs):
        initial = {'start_date': datetime.date.today()}
        if self.kwargs.get('apartment_number'):
            initial['apartment'] = Apartment.objects.get(number=self.kwargs.get('apartment_number'))

        return initial


class OccupancyEdit(AdminStaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Occupancy
    template_name = 'form-template-menu-on-the-left.html'
    form_class = OccupancyForm
    success_message = "Liczba mieszkańców zmieniona pomyślnie"
    success_url = reverse_lazy('occupancy')


class WaterReadoutsImport(AdminStaffRequiredMixin, SuccessMessageMixin, View):
    template_name = 'water-readouts-import.html'
    form_class = WaterReadoutsImportForm
    success_message = "Liczniki zostały zaimportowane pomyślnie"
    success_url = reverse_lazy('admin-water-readouts')

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data.get('file')
            import_water_readouts(data)
            messages.success(self.request, self.success_message)
            return HttpResponseRedirect(reverse_lazy('admin-water-readouts'))
        else:
            return render(request, self.template_name, {'form': form})
