from django.contrib import admin

# Register your models here.
from .models import VoucherRequest, Voucher, Client, User, AuditTrails

class VoucherRequestAdmin(admin.ModelAdmin):
    list_display = ['request_ref', 'date_time_recorded', 'quantity_of_vouchers']

    def save_model(self, request, obj, form, change):
        # associate signed  user to the voucherrequest when he creates new request
        if not obj.recorded_by:
            obj.recorded_by = request.user
        obj.save()


class VoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_ref', 'date_time_created', 'amount']


class ClientAdmin(admin.ModelAdmin):
    list_display = ['firstname', 'lastname', 'email']


class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email']

class AuditTrailsAdmin(admin.ModelAdmin):
    list_display = ['user__username', 'action', 'table_name', 'datetime']


admin.site.register(VoucherRequest, VoucherRequestAdmin)
admin.site.register(Voucher, VoucherAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(AuditTrails, AuditTrailsAdmin)