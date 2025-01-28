from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.permissions import SAFE_METHODS
from vms_app.models import (
    Voucher, Client,
    VoucherRequest,
    User, Company, Shop
)


class UsersSerializer(serializers.ModelSerializer):
    """create, update, delete, view all users or one user"""
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ['date_joined', 'id']

    def __init__(self, *args, **kwargs):
        super(UsersSerializer, self).__init__(*args, **kwargs)
        # exlude password field if the request method is "GET or HEAD or OPTIONS"
        request = self.context.get('request')
        if request and request.method in SAFE_METHODS:
            self.fields.pop('password')

    def update(self, instance, validated_data):
        validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        return instance


class RegisterUserSerializer(serializers.ModelSerializer):
    """create an account for supervisor"""
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password')
        read_only_fields = ['date_joined', 'id']

    def validate(self, data):
        """validate username and email if username or email already exists, reaise an error"""
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already exists")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with that email already exists."})
        return data

    def create(self, validated_data):
        # Extract and hash the password before saving
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password) # Hash the password
        # Create and assign the user to the 'shop_supervisor' group
        group, created = Group.objects.get_or_create(name='shop_supervisor')
        user.groups.add(group)
        user.save()
        return user


class VoucherRequestListSerializer(serializers.ModelSerializer):

    class Meta:
        model = VoucherRequest
        fields = "__all__"
        read_only_fields = ['date_time_recorded', 'request_ref', 'id']


class VoucherRequestCrudSerializer(serializers.ModelSerializer):
    vouchers = VoucherRequestListSerializer(many=True, read_only=True)
    class Meta:
        model = VoucherRequest
        fields = [
            "id", "request_ref",
              "request_status",
              "date_time_recorded",
              "date_time_approved",
              "quantity_of_vouchers",
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


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = "__all__"
        read_only_fields = ['date_time_created', 'voucher_ref', 'id']

    def create(self, validated_data):
        # Ensure the instance is updated with the correct database values after creation
        instance = super().create(validated_data)
        instance.refresh_from_db()
        return instance


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"
        read_only_fields = ['id']


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = "__all__"
        read_only_fields = ['id']