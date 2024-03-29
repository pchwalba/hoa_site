from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import *

urlpatterns = [
    path('register/', MyRegisterView.as_view(), name='register'),
    path('login/', MyLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('management/overview/', Overview.as_view(), name='overview'),
    path('management/water/', WaterReadoutsView.as_view(), name='water-readouts'),
    path('management/water/admin/', WaterReadoutsAdminView.as_view(), name='admin-water-readouts'),
    path('management/water/admin/import/', WaterReadoutsImport.as_view(), name='admin-water-readouts-import'),
    path('management/water/create/<int:apartment_number>/', WaterReadoutsCreate.as_view(),
         name='water-readouts-create'),
    path('management/water/edit/<int:pk>/', WaterReadoutsEdit.as_view(), name='water-readouts-edit'),
    path('management/water/', WaterReadoutsCreate.as_view(), name='water-readouts-create'),
    path('management/fees/', FeesView.as_view(), name='fees'),
    path('management/fees/add/', FeesCreate.as_view(), name='fees-create'),
    path('management/fees/history/', FeesHistoryView.as_view(), name='fees-history'),
    path('management/summary/admin', AdminSummaryView.as_view(), name='admin-summary'),
    path('management/admin-yearly-summary/', AdminYearlySummaryView.as_view(), name='admin-yearly-summary'),
    path('management/summary/', SummaryView.as_view(), name='summary'),
    path('menagement/calculate-balance/', CalculatePayments.as_view(), name='calculate-balance'),
    path('management/apartment-balance/', ApartmentBalanceView.as_view(), name='apartment-balance'),
    path('management/association-balance/', AssociationBalanceView.as_view(), name='association-balance'),
    path('management/association-balance/create/', AssociationBalanceCreate.as_view(),
         name='association-balance-create'),
    path('management/add-payment/<int:apartment_number>', ApartmentBalanceCreate.as_view(), name='add-payment'),
    path('management/add-payment/calculate-single-payment/<int:apartment_number>', CalculateSinglePayment.as_view(),
         name='calculate-single-payment'),
    path('management/central-heating/', CentralHeatingSurchargeView.as_view(), name='central-heating-surcharge'),
    path('management/central-heating/create/<int:apartment_number>', CentralHeatingSurchargeCreate.as_view(),
         name='central-heating-surcharge-create'),
    path('management/central-heating/create/', CentralHeatingSurchargeCreate.as_view(),
         name='central-heating-surcharge-create'),
    path('management/central-heating/edit/<int:pk>', CentralHeatingSurchargeEdit.as_view(),
         name='central-heating-surcharge-edit'),
    path('management/parking-cards/', ParkingCardView.as_view(), name='parking-card'),
    path('management/parking-cards/edit/<int:pk>', ParkingCardEdit.as_view(), name='parking-card-edit'),
    path('management/parking-cards/create/<int:apartment_number>', ParkingCardCreate.as_view(),
         name='parking-card-create'),
    path('management/parking-cards/create/', ParkingCardCreate.as_view(), name='parking-card-create'),
    path('management/big-family-cards/', BigFamilyCardView.as_view(), name='big-family-card'),
    path('management/big-family-cards/edit/<int:pk>', BigFamilyCardEdit.as_view(), name='big-family-card-edit'),
    path('management/big-family-cards/create/<int:apartment_number>', BigFamilyCardCreate.as_view(),
         name='big-family-card-create'),
    path('management/big-family-cards/create/', BigFamilyCardCreate.as_view(), name='big-family-card-create'),
    path('management/occupancy/', OccupancyView.as_view(), name='occupancy'),
    path('management/occupancy/create/<int:apartment_number>', OccupancyCreate.as_view(), name='occupancy-create'),
    path('management/occupancy/create/', OccupancyCreate.as_view(), name='occupancy-create'),
    path('management/occupancy/edit/<int:pk>', OccupancyEdit.as_view(), name='occupancy-edit'),
    path('pdf/', GenerateYearlySummaryPdf.as_view(), name='generate-pdf')
]
