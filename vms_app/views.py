from django.db.models import Max
# from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
# from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    filters,
    generics,
    viewsets,
    permissions, status
)

from vms_app.serializers import (
    UsersSerializer,
    RegisterUserSerializer,
    ClientListSerializer,
    VoucherRequestSerializer,
    VoucherSerializer,
    CompanySerializer,
    ShopSerializer,
    ClientDetailsSerializer
)
from .models import (
    User, Client,
    VoucherRequest,
    Voucher, Shop,
    Company,
)
from .paginations import (
    VoucherRequestPagination,
    VoucherPagination,
    ClientsPagination
)


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


class UserRegisterView(generics.GenericAPIView):
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


class ClientListView(generics.ListAPIView):
    """display a list of all clients"""
    queryset = Client.objects.all()
    serializer_class = ClientListSerializer
    filter_backends = [filters.SearchFilter]
    pagination_class = ClientsPagination
    search_fields = ['email', 'id']
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions
    ]


class ClientCRUDView(generics.GenericAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientDetailsSerializer

    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions
    ]
    def get_object(self):
        """ find a client by id """
        try:
            return self.queryset.get(pk=self.kwargs['pk'])
        except Client.DoesNotExist:
            raise NotFound(detail="client not found")

    def get(self, request, *args, **kwargs):
        client = self.get_object()
        serializer = self.get_serializer(client)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        client = self.get_object()
        serializer = self.get_serializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        client = self.get_object()
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    search_fields = ['company_name', 'id']
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]


class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    search_fields = ['id']
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