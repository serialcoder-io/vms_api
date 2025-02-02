# from django.db.models import Max
# from django.db.models.lookups import Exact
# from django.shortcuts import redirect
# from django.shortcuts import render
# from rest_framework.exceptions import ValidationError
from django.db import IntegrityError, DatabaseError
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
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
    UserSerializer,
    RegisterUserSerializer,
    ClientListSerializer,
    VoucherRequestListSerializer,
    VoucherRequestCrudSerializer,
    VoucherSerializer,
    CompanySerializer,
    ShopSerializer,
    ClientCrudSerializer, RedemptionSerializer,
)
from .models import (
    User, Client,
    VoucherRequest,
    Voucher, Shop,
    Company, Redemption,
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
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['email']
    filterset_fields = ['company']
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


class VoucherRequestListView(generics.ListAPIView):
    """
        created, read, update, delete Voucher_requests:
        view only for authenticated users with right permissions
    """
    queryset = VoucherRequest.objects.all()
    serializer_class = VoucherRequestListSerializer
    pagination_class = VoucherRequestPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['=request_ref']
    filterset_fields = ['request_status']
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]


class VoucherRequestCrudView(generics.GenericAPIView):
    queryset = VoucherRequest.objects.all()
    serializer_class = VoucherRequestCrudSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]

    def get_object(self):
        """ Find a VoucherRequest by id """
        pk = self.kwargs.get('pk')
        if not pk:
            raise NotFound(detail="VoucherRequest ID not provided")
        try:
            return self.queryset.get(pk=pk)
        except VoucherRequest.DoesNotExist:
            raise NotFound(detail="VoucherRequest not found")

    def get(self, request, *args, **kwargs):
        voucher_request = self.get_object()
        serializer = self.serializer_class(voucher_request)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        pending_status = VoucherRequest.RequestStatus.PENDING
        approved_status = VoucherRequest.RequestStatus.APPROVED
        voucher_request = self.get_object()
        serializer = self.get_serializer(voucher_request, data=request.data, partial=True)
        if serializer.is_valid():
            new_request_status = serializer.validated_data.get('request_status')
            try:
                # Update the status of related vouchers
                voucher_request.update_related_vouchers_status(new_request_status)
                if new_request_status == approved_status and voucher_request.request_status == pending_status:
                    # If the request is approved, set the approval timestamp and
                    # associate the action with the approving user
                    serializer.validated_data["date_time_approved"] = timezone.now()
                    serializer.validated_data["approved_by"] = request.user
                else:
                    # Prevent changing the status if the voucher request is already approved/rejected
                    return Response(
                        {
                            "detail": f"This voucher request is already {voucher_request.request_status}. You cannot modify it."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            except IntegrityError:
                # Handle integrity issues, such as foreign key constraints or unique constraints
                return Response(
                    {"detail": "There was a data integrity issue."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            except DatabaseError:
                # Handle general database issues, such as connection problems
                return Response(
                    {"detail": "A database error occurred."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            except Exception as e:
                # Catch all other unexpected errors
                return Response(
                    {"detail": f"An unexpected error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Save changes and return the updated data
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Return validation errors if the serializer is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        voucher_request = self.get_object()
        voucher_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VoucherRequestCreateView(generics.CreateAPIView):
    queryset = VoucherRequest.objects.all()
    serializer_class = VoucherRequestCrudSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]
    def post(self, request, *args, **kwargs):
        """
        Create a new VoucherRequest
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        """
        Save the voucher request with the user who created it
        """
        serializer.save(recorded_by=self.request.user)


class ClientListView(generics.ListAPIView):
    """display a list of all clients"""
    queryset = Client.objects.all()
    serializer_class = ClientListSerializer
    filter_backends = [filters.SearchFilter]
    pagination_class = ClientsPagination
    search_fields = ['email']
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions
    ]


class ClientCRUDView(generics.GenericAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientCrudSerializer
    filter_backends = [filters.SearchFilter]
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


class ClientCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientCrudSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions
    ]
    def post(self, request, *args, **kwargs):
        """
            Add a new client
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoucherViewSet(viewsets.ModelViewSet):
    """
        created, read, update, delete Vouchers:
        view only for authenticated users with right permissions
    """
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    pagination_class = VoucherPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['=voucher_ref']
    filterset_fields = ['voucher_status']
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['company_name']
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]


class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['company']
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissions
    ]


class RedemptionViewSet(viewsets.ModelViewSet):
    queryset = Redemption.objects.all()
    serializer_class = RedemptionSerializer
    permission_classes = [permissions.IsAuthenticated, DjangoModelPermissions]


@permission_classes([permissions.IsAuthenticated])
@api_view(["POST"])
def redeem_voucher(request, voucher_id, *args, **kwargs):
    if request.method == "POST":
        try:
            voucher = Voucher.objects.get(pk=voucher_id)
            # a voucher can be redeemed only if the status is 'issued'
            if voucher.voucher_status != Voucher.VoucherStatus.ISSUED:
                return Response(
                    {"details": "Voucher must have the status 'ISSUED' to be redeemed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if "shop_id" not in request.data:
                return Response(
                    {"details": "The 'shop_id' field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # check if there is a shop with the id provided in request.data
            shop = Shop.objects.get(pk=request.data["shop_id"])
            till_no = request.data.get("till_no")

            # redeem the voucher
            voucher.redeem(user=request.user, shop=shop, till_no=till_no)

            # response when the voucher was redeemed successfully
            redemption = {
                "redeemed_on": voucher.redemption.redemption_date,
                "redeemed_at": f"{voucher.redemption.shop.company.company_name} {voucher.redemption.shop.location}",
            }
            return Response(
                {
                    "details": f"Voucher '{voucher.voucher_ref}' was redeemed successfully.",
                    "voucher_info": {
                        "voucher_ref": voucher.voucher_ref,
                        "amount": voucher.amount,
                        "redemption": redemption,
                    },
                },
                status=status.HTTP_201_CREATED
            )
        except Voucher.DoesNotExist:
            return Response({"details": "Voucher not found."}, status=status.HTTP_404_NOT_FOUND)
        except Shop.DoesNotExist:
            return Response({"details": "Shop not found."}, status=status.HTTP_404_NOT_FOUND)
        except KeyError as e:
            return Response({"details": f"Missing field: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"details": "Invalid request method."}, status=status.HTTP_400_BAD_REQUEST)


