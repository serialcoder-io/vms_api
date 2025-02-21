from typing import Optional, Dict, Any
# from django.contrib.auth import authenticate
from .utils import logs_audit_action
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.permissions import SAFE_METHODS
from vms_app.models import (
    Voucher, Client,
    VoucherRequest,
    User, Company, Shop, Redemption, AuditTrails
)

class UserSerializer(serializers.ModelSerializer):
    """Create, update, delete, view all users or one user."""
    password = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ['date_joined', 'id']

    def __init__(self, *args, **kwargs):
        super(UserSerializer, self).__init__(*args, **kwargs)
        # Exclude password field if the request method is SAFE (GET, HEAD, OPTIONS)
        request = self.context.get('request')
        if request and request.method in SAFE_METHODS:
            self.fields.pop('password')

    def validate(self, data):
        """Validate that username and email are unique."""
        user_instance = self.instance  # Get the current instance (None for creation)

        # Check uniqueness of username only if it's being updated or created
        username = data.get('username')
        if username and User.objects.filter(username=username).exclude(
                id=user_instance.id if user_instance else None).exists():
            raise serializers.ValidationError({"username": "Username already exists."})

        # Check uniqueness of email only if it's being updated or created
        email = data.get('email')
        if email:
            # If the instance is not None (i.e., it's an update), check if email is different
            if user_instance and email != user_instance.email:
                if User.objects.filter(email=email).exclude(id=user_instance.id).exists():
                    raise serializers.ValidationError({"email": "A user with that email already exists."})
            # If the instance is None (i.e., it's creation), check if email is unique
            elif not user_instance and User.objects.filter(email=email).exists():
                raise serializers.ValidationError({"email": "A user with that email already exists."})

        return data

    def update(self, instance, validated_data):
        """Update user details."""
        # Remove password field before update unless explicitly provided
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', None)  # Pop groups if provided
        user_permissions = validated_data.pop('user_permissions', None)  # Pop user_permissions if provided
        instance = super().update(instance, validated_data)

        # Update password if it's provided
        if password:
            instance.set_password(password)
            instance.save()

        # Update groups if provided
        if groups:
            instance.groups.set(groups)

        # Update user_permissions if provided
        if user_permissions:
            instance.user_permissions.set(user_permissions)
        user = self.context['request'].user
        desctiption = f"updated data for {user.username}"
        logs_audit_action(instance, AuditTrails.AuditTrailsAction.UPDATE, desctiption, user)
        return instance

    def create(self, validated_data):
        """Create a new user and ensure uniqueness of username and email."""
        password = validated_data.pop('password')  # Password is required, so no need to check for None
        groups = validated_data.pop('groups', None)
        user_permissions = validated_data.pop('user_permissions', None)

        # Create user and set password
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Assign groups and permissions after saving
        if groups:
            user.groups.set(groups)
        if user_permissions:
            user.user_permissions.set(user_permissions)
        desctiption = f"added new user {user.username}"
        authenticated_user = self.context['request'].user
        logs_audit_action(user, AuditTrails.AuditTrailsAction.ADD, desctiption, authenticated_user)
        return user

    @staticmethod
    def validate_unique_fields(data):
        """Check uniqueness of username and email for creation."""
        if User.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError({"username": "Username already exists."})
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "A user with that email already exists."})


class CurrentUserSerializer(serializers.ModelSerializer):
    """Serializer for retrieving the current user's basic details."""

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email"]
        read_only_fields = ['date_joined', 'id']


shop_supervisor_permissions = [
    'add_redemption',
    'change_voucher',
    'view_voucher',
    'view_redemption'
]

class RegisterUserSerializer(serializers.ModelSerializer):
    """Create an account for a supervisor."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('company', 'first_name', 'last_name', 'username', 'email', 'password')
        read_only_fields = ['date_joined', 'id']

    def validate(self, data):
        """Validate that username and email are unique."""
        UserSerializer.validate_unique_fields(data)
        return data

    def create(self, validated_data):
        # Ensure password is provided
        password = validated_data.get('password')
        if not password:
            raise serializers.ValidationError({"password": "Password is required."})

        # Hash the password before saving
        validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # Hash the password
        # Create and assign the user to the 'shop_supervisor' group
        user.save()
        group, created = Group.objects.get_or_create(name='shop_supervisor')
        user.groups.add(group)
        user.save()

        for codename in shop_supervisor_permissions:
            permission = Permission.objects.get(codename=codename)
            user.user_permissions.add(permission)  # add the permissions to the user

        # Sauvegarder les changements
        user.save()
        return user


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


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
        # Ensure the instance is updated with the correct database values after creation
        instance = super().create(validated_data)
        instance.refresh_from_db()
        return instance

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
    vouchers = VoucherSerializer(many=True, read_only=True)
    class Meta:
        model = VoucherRequest
        fields = [
              "id", "request_ref",
              "request_status",
              "date_time_recorded",
              "date_time_approved",
              "approved_by",
              "quantity_of_vouchers",
              "description",
              "vouchers"
            ]
        read_only_fields = ['date_time_recorded', 'request_ref', 'id']

    def create(self, validated_data):
        # Ensure the instance is updated with the correct database values after creation
        instance = super().create(validated_data)
        instance.refresh_from_db()
        return instance


class ClientListSerializer(serializers.ModelSerializer):
    """serializer for client list"""
    class Meta:
        model = Client
        fields = "__all__"
        read_only_fields = ['id']


class ClientCrudSerializer(serializers.ModelSerializer):
    """serializer for client crud"""
    # client requests
    client_voucher_requests = VoucherRequestListSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "firstname",
            "lastname",
            "email",
            "contact",
            "logo",
            "client_voucher_requests"
        ]
        read_only_fields = ['id']


"""
@Todo: call logs_action_action in every serializer after insert, update and delete
@Todo: write all tests
@Todo: finish reset password feature
@Todo: finish active account feature
"""