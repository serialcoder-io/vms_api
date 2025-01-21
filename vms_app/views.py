from django.shortcuts import render

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from vms_app.serializers import UsersSerializer
from rest_framework import viewsets #, permissions, status
# from django_filters.rest_framework import DjangoFilterBackend
from .models import User
# from .paginations import UsersPagination

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
