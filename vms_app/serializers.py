from rest_framework import serializers
from vms_app.models import User

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password"]