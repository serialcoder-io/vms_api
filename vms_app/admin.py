from django.contrib import admin
from .models import VoucherRequest, Voucher, Client, User, AuditTrails
from .utils import validate_and_format_date, notify_requests_approvers


class VoucherRequestAdmin(admin.ModelAdmin):
    list_display = ['request_ref', 'date_time_recorded', 'quantity_of_vouchers']

    def save_model(self, request, obj, form, change):
        if change:
            old_status = form.initial.get('request_status', obj.request_status)
            new_status = form.cleaned_data.get('request_status', obj.request_status)

            if old_status == 'pending' and new_status == 'paid':
                # Notify(email) all approvers when a voucher-request has been paid
                notify_requests_approvers(obj.id, obj.request_ref)
            elif old_status == 'paid' and new_status == 'approved':
                obj.approved_by = request.user
        else:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


class VoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_ref', 'date_time_created', 'amount']

    def save_model(self, request, obj, form, change):
        # Vérification et formatage de expiry_date si elle n'est ni vide ni null
        if obj.expiry_date not in [None, '']:
            obj.expiry_date = validate_and_format_date(obj.expiry_date)

        # Vérification et formatage de extention_date si elle n'est ni vide ni null
        if obj.extention_date not in [None, '']:
            obj.extention_date = validate_and_format_date(obj.extention_date)
        else:
            # Si extention_date est vide ou None, on la laisse null (None en Python)
            obj.extention_date = None

        # Sauvegarde de l'objet après modification
        super().save_model(request, obj, form, change)



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