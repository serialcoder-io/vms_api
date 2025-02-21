from django.contrib import admin
from .models import VoucherRequest, Voucher, Client, User, AuditTrails
from .utils import validate_and_format_date


class VoucherRequestAdmin(admin.ModelAdmin):
    list_display = ['request_ref', 'date_time_recorded', 'quantity_of_vouchers']

    """def save_model(self, request, obj, form, change):
        try:
            # Ajout de la logique spécifique lors de la modification
            if change:  # Si c'est une modification
                print(f"Modification de l'objet : {obj.request_ref}")
                old_status = form.initial.get('request_status', obj.request_status)
                new_status = form.cleaned_data.get('request_status', obj.request_status)

                # Check if the old status was 'pending' or 'paid' and if the new status is 'approved' or 'rejected'
                if (old_status == 'pending' or old_status == "paid") and new_status in ['approved', 'rejected']:
                    # Update the related vouchers if the status changed from 'pending' or 'paid' to 'approved' or 'rejected'
                    obj.update_related_vouchers_status(new_status)

            else:  # Si c'est une création
                print(f"Création de l'objet : {obj.request_ref}")
                obj.recorded_by = request.user

            # Sauvegarder l'objet après toutes les modifications
            super().save_model(request, obj, form, change)

        except Exception as e:
            # Handle any errors
            raise Exception(f"Error while saving the voucher request: {e}")"""


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