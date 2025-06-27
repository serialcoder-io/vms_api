from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.hashers import make_password

from .models import (
    VoucherRequest, Shop,
    Voucher, Client, User,
    AuditTrail, Company,
    Redemption
)
from .utils import validate_and_format_date

class VoucherInline(admin.StackedInline):
    model = Voucher
    extra = 0
class VoucherRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_ref', 'request_status',
        'date_time_recorded', 'quantity_of_vouchers'
    ]
    readonly_fields = [
        'id', 'request_ref',
        'date_time_recorded',
        'date_time_approved',
        'approved_by', 'recorded_by'
    ]
    list_filter = ['request_status']
    list_per_page = 10
    inlines = [VoucherInline]
    search_fields = ["request_ref"]
    actions = [
        "reject_selected_voucher_requests",
        "approve_selected_voucher_requests",
        "paid_selected_voucher_requests"
    ]

    def save_model(self, request, obj, form, change):
        if change:
            old_status = form.initial.get('request_status', obj.request_status)
            new_status = form.cleaned_data.get('request_status', obj.request_status)
            if old_status == 'paid' and new_status == 'approved':
                obj.approved_by = request.user
        else:
            status = form.cleaned_data.get('request_status', obj.request_status)
            if status != 'pending':
                messages.warning(request, "The request status has been automatically set to 'pending' upon creation.")
                obj.request_status = "pending"
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)

    def reject_selected_voucher_requests(self, request, queryset):
        if queryset.filter(request_status__in=['pending', 'paid']).exists():
            queryset.filter(request_status__in=['pending', 'paid']).update(request_status='rejected')
            self.message_user(request, "Selected voucher requests have been rejected.", level=messages.SUCCESS)
        else:
            self.message_user(
                request,
                "Cannot reject voucher requests that are not 'pending' or 'paid'.",
                level=messages.ERROR
            )

    @admin.action(description="Approve selected requests")
    def approve_selected_voucher_requests(self, request, queryset):
        if queryset.filter(request_status='paid').exists():
            queryset.filter(request_status='paid').update(request_status='approved')
            self.message_user(request, "Selected voucher requests have been approved", level=messages.SUCCESS)
        else:
            self.message_user(
                request,
                "Cannot approve requests that are not 'paid'.",
                level=messages.ERROR
            )

    @admin.action(description="Mark selected requests as paid")
    def paid_selected_voucher_requests(self, request, queryset):
        if queryset.filter(request_status='pending').exists():
            queryset.filter(request_status='pending').update(request_status='paid')
            self.message_user(request, "Selected voucher requests have been paid", level=messages.SUCCESS)
        else:
            self.message_user(
                request,
        "Cannot mark requests as 'paid' that are not 'pending'.",
                level=messages.ERROR
            )


class RedemptionInline(admin.StackedInline):
    model = Redemption
    extra = 0
    readonly_fields = ['user', 'voucher', 'redemption_date', 'shop','till_no']
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_ref', 'date_time_created', 'amount', 'get_redemption_info']
    readonly_fields = ['id', 'voucher_ref', 'voucher_request', 'amount', 'date_time_created']
    search_fields = ['voucher_ref']
    list_filter = ['voucher_status']
    actions = ["generate_bon_pdf"]
    list_per_page = 10
    inlines = [RedemptionInline]

    def save_model(self, request, obj, form, change):
        if obj.expiry_date not in [None, '']:
            obj.expiry_date = validate_and_format_date(obj.expiry_date)

        if obj.extention_date not in [None, '']:
            obj.extention_date = validate_and_format_date(obj.extention_date)
        else:
            obj.extention_date = None

        super().save_model(request, obj, form, change)



class VoucherRequestInline(admin.StackedInline):
    model = VoucherRequest
    extra = 1
class ClientAdmin(admin.ModelAdmin):
    list_display = ['clientname', 'contact', 'email']
    search_fields = ['email']
    readonly_fields = ['id']
    list_per_page = 10
    inlines = [VoucherRequestInline]


User = get_user_model()

class CustomUserChangeForm(forms.ModelForm):
    new_password = forms.CharField(
        label="Nouveau mot de passe",
        required=False,
        widget=forms.PasswordInput,
        help_text="Laissez vide si vous ne voulez pas changer le mot de passe."
    )

    class Meta:
        model = User
        fields = [  # tous les champs sauf 'password'
            'username', 'email', 'first_name', 'last_name',
            'company', 'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions'
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
            self.save_m2m()
        return user

class UserAdmin(admin.ModelAdmin):
    
    form = CustomUserChangeForm
    
    list_display = ['username', 'email']
    list_per_page = 10
    search_fields = ['username', 'email']
    readonly_fields = ['id', 'last_login', 'date_joined']
    fieldsets = (
        ('profile', {
            'fields': (
                'first_name', 'last_name', 'username', 'email', 'company', 'new_password')
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions', 'groups')}),
    )


class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['user__username', 'action', 'table_name', 'datetime']
    readonly_fields = ['id', 'user', 'action', 'table_name', 'datetime', 'description', 'object_id']
    list_per_page = 10

    def has_add_permission(self, request):
        return False


class ShopInline(admin.TabularInline):
    model = Shop
    extra = 1
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['company_name']
    readonly_fields = ['id']
    inlines = [ShopInline]
    list_per_page = 10
    search_fields = ['company_name']


class ShopAdmin(admin.ModelAdmin):
    list_display = ['company__company_name', 'location']
    readonly_fields = ['id']
    list_per_page = 10
    search_fields = ['location']


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message')
    list_filter = ('user', 'content_type', 'action_flag')
    search_fields = ('object_repr', 'change_message')
    readonly_fields = [f.name for f in LogEntry._meta.fields]  # rendre tous les champs en lecture seule
    list_per_page = 10

    def has_add_permission(self, request):
        return False  # empêche l'ajout manuel

    def has_change_permission(self, request, obj=None):
        return False  # empêche la modification


admin.site.register(VoucherRequest, VoucherRequestAdmin)
admin.site.register(Voucher, VoucherAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(AuditTrail, AuditTrailAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Shop, ShopAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
