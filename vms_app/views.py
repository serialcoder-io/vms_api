from django.db.models import Max
# from django.shortcuts import render

from rest_framework.decorators import api_view
# from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework import viewsets, permissions #, status
# from rest_framework.viewsets import ViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from vms_app.serializers import (
    UsersSerializer,
    RegisterUserSerializer,
    ClientSerializer,
    VoucherRequestSerializer,
    VoucherSerializer
)

from .models import User, Client, VoucherRequest, Voucher
from .paginations import VoucherRequestPagination, VoucherPagination


class UserViewSet(viewsets.ModelViewSet):
    """created, read, update, delete users:
    view only for authenticated users with right permissions
    """
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions
    ]


class ClientViewSet(viewsets.ModelViewSet):
    """created, read, update, delete Clients information:
    view only for authenticated users with right permissions
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'id']
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions
    ]


class UserRegisterView(GenericAPIView):
    """create an account for supervisor"""
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class VoucherRequestViewSet(viewsets.ModelViewSet):
    """
        created, read, update, delete Voucher_requests:
        view only for authenticated users with right permissions
    """
    queryset = VoucherRequest.objects.all()
    serializer_class = VoucherRequestSerializer
    pagination_class = VoucherRequestPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['request_ref', 'id']
    filterset_fields = ['request_status', 'date_time_recorded']
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

class VoucherViewSet(viewsets.ModelViewSet):
    """
        created, read, update, delete Vouchers:
        view only for authenticated users with right permissions
    """
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    pagination_class = VoucherPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['voucher_ref', 'id']
    filterset_fields = ['voucher_status', 'date_time_created']
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]

@api_view(['GET'])
def get_latest_id(request):
    latest_id = User.objects.aggregate(Max('id'))['id__max']
    return Response(
        {
            "latest_id": latest_id
        }
    )