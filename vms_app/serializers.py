from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.permissions import SAFE_METHODS
from vms_app.models import User, Client, VoucherRequest, Voucher


class UsersSerializer(serializers.ModelSerializer):
    """create, update, delete, view all users or one user"""
    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(UsersSerializer, self).__init__(*args, **kwargs)
        # exlude password field if the request method is "GET or HEAD or OPTIONS"
        request = self.context.get('request')
        if request and request.method in SAFE_METHODS:
            self.fields.pop('password')

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class RegisterUserSerializer(serializers.ModelSerializer):
    """create an account for supervisor"""
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password')
        read_only_fields = 'date_joined'

    def validate(self, data):
        """validate username and email if username or email already exists, reaise an error"""
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already exists")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with that email already exists."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')  # extract password
        user = User(**validated_data)
        user.set_password(password) # hash password
        group, created = Group.objects.get_or_create(name='shop_supervisor')
        user.groups.add(group)
        user.save()
        return user


class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = "__all__"


class VoucherRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = VoucherRequest
        fields = "__all__"
        read_only_fields = ['date_time_recorded']


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = "__all__"
        read_only_fields = ['created_at']