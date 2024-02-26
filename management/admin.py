from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ApartmentUser, Apartment, Fees, WaterReadouts, Occupancy, ApartmentBalance, ParkingCard, \
    CentralHeatingSurcharge


# Register your models here.

class ApartmentAdmin(admin.ModelAdmin):
    model = Apartment
    ordering = ('number',)

    def get_readonly_fields(self, request, obj=None):
        defaults = super().get_readonly_fields(request, obj=obj)
        if obj:  # if we are updating an object
            defaults = tuple(defaults) + ('number', 'area')  # make sure defaults is a tuple
        return defaults


class ApartmentUserAdmin(UserAdmin):
    model = ApartmentUser
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Other info',
            {
                'fields': (
                    'phone',
                    'apartment',
                )
            }
        )
    )


class OccupancyAdmin(admin.ModelAdmin):
    model = Occupancy
    ordering = ('apartment__number', '-start_date')


class WaterReadoutsAdmin(admin.ModelAdmin):
    model = WaterReadouts
    ordering = ('-readout_date', 'apartment__number')


class FeesAdmin(admin.ModelAdmin):
    model = Fees
    ordering = ('-period',)


admin.site.register(ApartmentUser, ApartmentUserAdmin)
admin.site.register(Apartment, ApartmentAdmin)
admin.site.register(Fees)
admin.site.register(WaterReadouts, WaterReadoutsAdmin)
admin.site.register(Occupancy, OccupancyAdmin)
admin.site.register(ApartmentBalance)
admin.site.register(ParkingCard)
admin.site.register(CentralHeatingSurcharge)
