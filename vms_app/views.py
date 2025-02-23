from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError, DatabaseError
from django.shortcuts import render
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.exceptions import NotFound
from rest_framework.permissions import (IsAdminUser, IsAuthenticated, AllowAny)
from rest_framework import ( filters, generics, viewsets, status)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .permissions import (
    RedeemVoucherPermissions,
    IsMemberOfCompanyOrAdminUser,
    CustomDjangoModelPermissions
)

from vms_app.serializers import (
    UserSerializer, VoucherSerializer,
    VoucherRequestListSerializer,
    VoucherRequestCrudSerializer,
    CompanySerializer, ShopSerializer,
    ClientCrudSerializer, ClientListSerializer,
    RedemptionSerializer, PermissionsListSerializer,
    GroupCustomSerializer, AuditTrailsSerializer,
)
from .models import (
    User, Client,
    VoucherRequest,
    Voucher, Shop,
    Company, Redemption, AuditTrails,
)
from .paginations import (
    VoucherRequestPagination,
    VoucherPagination,
    ClientsPagination, UserPagination
)


class UserViewSet(viewsets.ModelViewSet):
    """created, read, update, delete users:
    view only for authenticated users with right permissions
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['email']
    filterset_fields = ['company']
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]


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
       IsAuthenticated,
       CustomDjangoModelPermissions
    ]


class VoucherRequestCrudView(generics.GenericAPIView):
    queryset = VoucherRequest.objects.all()
    serializer_class = VoucherRequestCrudSerializer
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
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

    @extend_schema(
        responses={
            200: OpenApiResponse(description="modified", response=VoucherRequestCrudSerializer),
            400: OpenApiResponse(
                description="Bad request: When the status is 'pending', the request can only be"
                " modified to 'paid' or 'rejected'. When the status is 'paid', it can only be modified to "
                "'rejected' or 'approved'. Once the status is 'approved' or 'rejected', it cannot be modified."),
            403: OpenApiResponse(description="Forbiden"),
            401: OpenApiResponse(description="Non authorize(not authenticated)"),
        }
    )
    def put(self, request, *args, **kwargs):
        pending_status = VoucherRequest.RequestStatus.PENDING
        approved_status = VoucherRequest.RequestStatus.APPROVED
        paid_status = VoucherRequest.RequestStatus.PAID
        rejected_status = VoucherRequest.RequestStatus.REJECTED
        voucher_request = self.get_object()
        serializer = self.get_serializer(voucher_request, data=request.data, partial=True)
        if serializer.is_valid():
            new_request_status = serializer.validated_data.get('request_status')
            current_status = voucher_request.request_status
            connot_be_modified = (current_status == approved_status or current_status == rejected_status or
                  (current_status == paid_status and new_request_status  == pending_status) )
            try:
                if current_status == paid_status and new_request_status == approved_status:
                    # If the request is approved, set the approval timestamp and
                    # associate the action with the approving user
                    serializer.validated_data["date_time_approved"] = timezone.now()
                    serializer.validated_data["approved_by"] = request.user
                elif current_status == pending_status and new_request_status == approved_status:
                    return Response(
                        {
                            "detail": f"The request must be in 'Paid' status before it can be approved."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                elif connot_be_modified:
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
        IsAuthenticated,
        CustomDjangoModelPermissions
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
    search_fields = ['=email']
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]


class ClientCRUDView(generics.GenericAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientCrudSerializer
    filter_backends = [filters.SearchFilter]
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
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
        IsAuthenticated,
        CustomDjangoModelPermissions
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
    filterset_fields = [
        'voucher_status', 'redemption__shop',
        'redemption__redemption_date'
    ]
    permission_classes = [
        IsAuthenticated,
        IsMemberOfCompanyOrAdminUser,
    ]


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['company_name']
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()

class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['company']
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()


class RedemptionViewSet(viewsets.ModelViewSet):
    queryset = Redemption.objects.all()
    serializer_class = RedemptionSerializer
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]


class RedeemVoucherView(generics.GenericAPIView):
    serializer_class = VoucherSerializer
    queryset = Voucher.objects.all()
    permission_classes = [
        IsAuthenticated,
        RedeemVoucherPermissions
    ]

    @extend_schema(
        request=VoucherSerializer,
        responses={201: VoucherSerializer}
    )
    def post(self, request, *args, **kwargs):
        try:
            voucher = self.get_object()
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
            return Response({"details": "Sorry something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupCustomSerializer
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]

class PermissionListViewSet(generics.ListAPIView):
    """
        This view allows listing all the permissions available in the application.
        Only authenticated users who have view_permission permission can access it.

        This view is read-only (GET). To create, update, or delete permissions,
        a user with the appropriate administrative permissions must log into the Django admin interface.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionsListSerializer
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]


class AuditTrailsViewset(viewsets.ModelViewSet):
    queryset = AuditTrails.objects.all()
    serializer_class = AuditTrailsSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

def password_reset_view(request, uidb64, token):
    context = {"uidb64": uidb64, "token": token}
    return render(request, 'reset_password.html', context)


def account_activation(request, uidb64, token):
    context = {"uidb64": uidb64, "token": token}
    return render(request, 'account_activation.html', context)


def password_reset_success_view(request):
    return render(request, 'password_reset_success.html')