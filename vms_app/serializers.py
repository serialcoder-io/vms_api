from rest_framework import serializers
from vms_app.models import User


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(UsersSerializer, self).__init__(*args, **kwargs)

        # exlude password field if the request method is get
        request = self.context.get('request')
        if request and request.method == 'GET':
            self.fields.pop('password')
