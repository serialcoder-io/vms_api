import base64
from typing import Optional, Dict, Any
from urllib.parse import urljoin
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError

from drf_spectacular.utils import extend_schema_field

from .utils import logs_audit_action, validate_and_format_date
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.permissions import SAFE_METHODS
from vms_app.models import (
    Voucher, VoucherRequest, Client, User,
    Company, Shop, Redemption, AuditTrail
)

class UserSerializer(serializers.ModelSerializer):
    """Create, update, delete, and view users."""
    password = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(required=False)
    permissions = serializers.SerializerMethodField()
    user_groups = serializers.SerializerMethodField()
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, required=False, write_only=True
    )
    user_permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), many=True, required=False, write_only=True
    )

    class Meta:
        model = User
        fields = [
            "id", "last_login", "first_name", "last_name", "username", "email",
            "password", "is_staff", "is_active", "is_superuser", "company",
            "permissions", "user_groups", "groups", "user_permissions"
        ]
        read_only_fields = ['date_joined', 'id', 'last_login']

    def get_permissions(self, obj):
        return [permission.codename for permission in obj.user_permissions.all()]

    def get_user_groups(self, obj):
        return [group.name for group in obj.groups.all()]

    def __init__(self, *args, **kwargs):
        super(UserSerializer, self).__init__(*args, **kwargs)
        # Exclude password field if the request method is SAFE (GET, HEAD, OPTIONS)
        request = self.context.get('request')
        if request and request.method in SAFE_METHODS:
            self.fields.pop('password')

    def validate(self, data):
        """Validate that username and emails are unique."""
        # Validation de l'unicité du username et de l'emails
        self.validate_unique_fields(data)
        return data

    def validate_unique_fields(self, data):
        """Check uniqueness of username and emails for creation or update."""
        user_instance = self.instance  # Get the current instance (None for creation)

        username = data.get('username')
        if username:
            if User.objects.filter(username=username).exclude(id=user_instance.id if user_instance else None).exists():
                raise serializers.ValidationError({"username": "Username already exists."})

        email = data.get('emails')
        if email:
            if user_instance and email != user_instance.email:
                if User.objects.filter(email=email).exclude(id=user_instance.id).exists():
                    raise serializers.ValidationError({"emails": "A user with that emails already exists."})
            elif not user_instance and User.objects.filter(email=email).exists():
                raise serializers.ValidationError({"emails": "A user with that emails already exists."})

    def update(self, instance, validated_data):
        """Update user details."""
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', None)
        user_permissions = validated_data.pop('user_permissions', None)

        instance = super().update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save()
        if groups:
            instance.groups.set(groups)
        if user_permissions:
            instance.user_permissions.set(user_permissions)
        return instance

    def create(self, validated_data):
        """Create a new user and ensure uniqueness of username and emails."""
        password = validated_data.pop('password')
        groups = validated_data.pop('groups', None)
        user_permissions = validated_data.pop('user_permissions', None)

        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()

        if groups:
            user.groups.set(groups)
        if user_permissions:
            user.user_permissions.set(user_permissions)
        return user


class CurrentUserSerializer(serializers.ModelSerializer):
    """Serializer for retrieving the current user's basic details."""

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email", "last_login"]
        read_only_fields = ['date_joined', 'id', 'last_login']


shop_supervisor_permissions = [
    'change_voucher',
    'redeem_voucher',
    'view_voucher',
    'view_redemption'
]

class RegisterUserSerializer(serializers.ModelSerializer):
    """Create an account for a supervisor."""

    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('id', 'company', 'first_name', 'last_name', 'username', 'email', 'password')
        read_only_fields = ['date_joined', 'id','last_login']

    def validate(self, data):
        """Validate that username and emails are unique."""
        # Appelez la méthode validate_unique_fields en passant les données de validation
        self.validate_unique_fields(data)
        return data

    def validate_unique_fields(self, data):
        """Check uniqueness of username and emails for creation."""
        username = data.get('username')
        email = data.get('email')

        # Vérifier l'unicité du nom d'utilisateur
        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Username already exists."})

        # Vérifier l'unicité de l'emails
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "A user with that emails already exists."})

    def create(self, validated_data):
        """Create a new user."""
        password = validated_data.get('password')
        if not password:
            raise serializers.ValidationError({"password": "Password is required."})

        validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)

        # Sauvegarder l'utilisateur
        user.save()

        # Ajouter l'utilisateur au groupe 'shop_supervisor'
        group, created = Group.objects.get_or_create(name='Shop')
        user.groups.add(group)

        # Assigner les permissions du shop_supervisor
        for codename in shop_supervisor_permissions:
            permission = Permission.objects.get(codename=codename)
            user.user_permissions.add(permission)

        user.save()
        return user


class CompanySerializer(serializers.ModelSerializer):
    prefix = serializers.CharField(required=False)
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'company_name', 'prefix', 'logo']

    def get_logo(self, obj):
        try:
            if obj.company_logo:
                return base64.b64encode(obj.company_logo).decode('utf-8')
        except Exception as e:
            # Log error and continue gracefully
            print(f"[Error] Invalid logo encoding for Company {obj.id}: {e}")
        return None

    def create(self, validated_data):
        logo_b64 = self.initial_data.get('logo')
        if logo_b64:
            try:
                validated_data["company_logo"] = base64.b64decode(logo_b64)
            except Exception:
                raise serializers.ValidationError({"logo": "Invalid Base64 string for logo."})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        logo_b64 = self.initial_data.get('logo')
        if logo_b64:
            try:
                instance.company_logo = base64.b64decode(logo_b64)
            except Exception:
                raise serializers.ValidationError({"logo": "Invalid Base64 string for logo."})

        instance.company_name = validated_data.get('company_name', instance.company_name)
        instance.prefix = validated_data.get('prefix', instance.prefix)

        instance.save()
        return instance



class ShopSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True
    )
    class Meta:
        model = Shop
        fields = ['id', 'location', 'address', 'company', 'company_id']
        read_only_fields = ['id', 'company']


class RedemptionSerializer(serializers.ModelSerializer):
    redeemed_on = serializers.DateTimeField(source='redemption_date', read_only=True)  # Fetch redemption_date
    redeemed_by = serializers.CharField(source='user.username', read_only=True)  # Fetch user's username
    redeemed_at = serializers.SerializerMethodField()  # Correct usage of SerializerMethodField

    class Meta:
        model = Redemption
        fields = ["id", "redeemed_on", "till_no", "redeemed_by", "redeemed_at", "voucher"]

    @extend_schema_field(str)
    def get_redeemed_at(self, obj):
        # Access the related `shop` object and combine company_name and location
        return f"{obj.shop.company.company_name} {obj.shop.location}"


class VoucherSerializer(serializers.ModelSerializer):
    redemption = serializers.SerializerMethodField()
    class Meta:
        model = Voucher
        fields = [
            "id", "voucher_ref",
            "amount",
            "voucher_request",
            "date_time_created",
            "expiry_date",
            "extention_date",
            "voucher_status",
            "redemption"
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        if 'expiry_date' in validated_data:
            validated_data['expiry_date'] = validate_and_format_date(validated_data['expiry_date'])

            # Validate and format the extention_date only if it is not empty or None
        if 'extention_date' in validated_data and validated_data['extention_date']:
            validated_data['extention_date'] = validate_and_format_date(validated_data['extention_date'])
        # Ensure the instance is updated with the correct database values after creation
        instance = super().create(validated_data)
        instance.refresh_from_db()
        return instance

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_redemption(self, obj)-> Optional[Dict[str, Any]]:
        # Retrieve the redemption related to the voucher if available
        try:
            redemption = obj.redemption
            if redemption:
                return RedemptionSerializer(redemption).data
        except Redemption.DoesNotExist:
            return None


class VoucherRequestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoucherRequest
        fields = "__all__"
        read_only_fields = ['date_time_recorded', 'request_ref', 'id']


class VoucherRequestCrudSerializer(serializers.ModelSerializer):
    request_doc_pdf = serializers.FileField(required=False)
    request_doc_pdf_url = serializers.SerializerMethodField()
    pop_doc_pdf = serializers.FileField(required=False, allow_null=True)
    payment_remarks = serializers.CharField(required=False, allow_blank=True)
    date_time_paid = serializers.DateTimeField(required=False)

    class Meta:
        model = VoucherRequest
        fields = [
            "id", "request_ref", "client", "company",  # <- ADD company
            "request_status", "amount",
            "date_time_recorded", "quantity_of_vouchers",
            "validity_periode", "date_time_approved", "approved_by",
            "request_doc_pdf", "request_doc_pdf_url",
            "pop_doc_pdf", "payment_remarks", "date_time_paid",
        ]
        read_only_fields = ['date_time_recorded', 'request_ref', 'id']

    def get_request_doc_pdf_url(self, obj):
        if obj.request_doc_pdf and hasattr(obj.request_doc_pdf, 'url'):
            base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
            return urljoin(base_url, obj.request_doc_pdf.url)
        return None

    def create(self, validated_data):
        try:
            # Ensure the instance is updated with the correct database values after creation
            validated_data["request_status"] = "pending"
            instance = super().create(validated_data)
            # Create provisional vouchers
            quantity = validated_data.get('quantity_of_vouchers', 0)
            for i in range(quantity):
                Voucher.objects.create(
                    voucher_request=instance,
                    voucher_status=Voucher.VoucherStatus.PROVISIONAL,
                    amount=instance.amount
                )

            instance.refresh_from_db()
            return instance
        except IntegrityError as e:
            raise serializers.ValidationError({"detail": f"Database integrity error: {str(e)}"})


    def update(self, instance, validated_data):
        # 🛡️ Defensive check to prevent saving a memoryview
        file = validated_data.get("request_doc_pdf")
        if file and not isinstance(file, UploadedFile):
            validated_data.pop("request_doc_pdf")

        return super().update(instance, validated_data)

class ClientListSerializer(serializers.ModelSerializer):
    """serializer for client list"""
    class Meta:
        model = Client
        fields = ['id', 'clientname', 'email', 'contact', 'brn', 'vat', 'nic', 'iscompany', 'logo']
        read_only_fields = ['id']

    def get_logo(self, obj):
        if obj.logo:
            return base64.b64encode(obj.logo).decode('utf-8')
        return ""

class ClientCrudSerializer(serializers.ModelSerializer):
    client_voucher_requests = VoucherRequestListSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = [
            "id", "iscompany", "clientname", "vat", "brn", "nic",
            "email", "contact", "logo", "client_voucher_requests"
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        logo_b64 = self.initial_data.get('logo')
        if logo_b64:
            try:
                validated_data['logo'] = base64.b64decode(logo_b64)
            except Exception:
                raise serializers.ValidationError({'logo': 'Invalid Base64 string'})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        logo_b64 = self.initial_data.get('logo')
        if logo_b64:
            try:
                validated_data['logo'] = base64.b64decode(logo_b64)
            except Exception:
                raise serializers.ValidationError({'logo': 'Invalid Base64 string'})
        return super().update(instance, validated_data)


class PermissionsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename"]
        read_only_fields = ['id']


class GroupCustomSerializer(serializers.ModelSerializer):
    """Serializer for the list of groups with hyperlinking"""
    permissions = PermissionsListSerializer(many=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']
        read_only_fields = ['id']

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_permissions(self, obj):
        return [permission.codename for permission in obj.user_permissions.all()]


class AuditTrailsSerializer(serializers.ModelSerializer):
    executed_by = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = AuditTrail
        fields = ["id", "datetime", "action", "table_name", "object_id", "description", "executed_by"]
        read_only_fields = ["id", "datetime", "action", "table_name", "object_id", "description", "user"]

"""
4) @Todo: call logs_action_action in every serializer after insert, update and delete
6) @Todo: write all tests
"""