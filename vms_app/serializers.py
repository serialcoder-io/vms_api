from rest_framework import serializers
from vms_app.models import User, Client


class UsersSerializer(serializers.ModelSerializer):
    """create, update, delete, view all users or one user"""
    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(UsersSerializer, self).__init__(*args, **kwargs)

        # exlude password field if the request method is "GET"
        request = self.context.get('request')
        if request and request.method == 'GET':
            self.fields.pop('password')


class RegisterUserSerializer(serializers.ModelSerializer):
    """create an account"""

    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password')

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
        user.save()
        return user


class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = "__all__"