from django.contrib import admin

# Register your models here.
from .models import VoucherRequest, Client

class VoucherRequestAdmin(admin.ModelAdmin):
    list_display = ['request_ref', 'date_time_recorded', 'quantity_of_vouchers']

    def save_model(self, request, obj, form, change):
        # associate signed  user to the voucherrequest when he creates new request
        if not obj.recorded_by:
            obj.recorded_by = request.user
        obj.save()


class ClientAdmin(admin.ModelAdmin):
    list_display = ['firstname', 'lastname', 'email']


admin.site.register(VoucherRequest, VoucherRequestAdmin)
admin.site.register(Client, ClientAdmin)