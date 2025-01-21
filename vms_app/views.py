from django.shortcuts import render

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from vms_app.serializers import UsersSerializer, RegisterUserSerializer
from rest_framework import viewsets, permissions #, status
# from django_filters.rest_framework import DjangoFilterBackend
from .models import User
# from .paginations import UsersPagination

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserRegisterView(GenericAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)