import base64
import json
import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError, DatabaseError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.timezone import localtime
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied
from rest_framework.permissions import (IsAdminUser, IsAuthenticated, AllowAny)
from rest_framework import (filters, generics, viewsets, status)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.files.uploadedfile import UploadedFile

# from rest_framework.generics import ListCreateAPIView
# from .models import VoucherRequest
# from .serializers import VoucherRequestCrudSerializer
import logging

logger = logging.getLogger(__name__)

from .utils import logs_audit_action
from .permissions import (
    RedeemVoucherPermissions,
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
    User, Client, Shop,
    VoucherRequest, Voucher,
    Company, Redemption, AuditTrail,
)
from .paginations import (
    VoucherRequestPagination, VoucherPagination,
    ClientsPagination, UserPagination
)


class UserViewSet(viewsets.ModelViewSet):
    """created, read, update, delete users:
    view only for authenticated users with rights permissions
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['emails']
    filterset_fields = ['company']
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        new_user = User.objects.get(pk=response.data['id'])  # Récupérer l'objet créé à partir de la réponse
        description = f"Added new user: \n username: '{new_user.email}'\n email: '{new_user.email}'"
        authenticated_user = request.user

        # Log the audit action for creation
        logs_audit_action(
            instance=new_user,
            action=AuditTrail.AuditTrailsAction.ADD,
            description=description,
            user=authenticated_user
        )

        return response

    def update(self, request, *args, **kwargs):
        # old user data before update
        user = self.get_object()
        old_data = UserSerializer(user).data
        old_data.pop('password', None)

        # update
        response = super().update(request, *args, **kwargs)
        # new user_data
        new_data = UserSerializer(user).data
        new_data.pop('password', None)

        # format logs
        description = (
            f"Updated user:\nBefore:\n{json.dumps(old_data, indent=4)}\n"
            f"After:\n{json.dumps(new_data, indent=4)}"
        )
        authenticated_user = request.user

        # Log the audit action for update
        logs_audit_action(
            instance=user,
            action=AuditTrail.AuditTrailsAction.UPDATE,
            description=description,
            user=authenticated_user
        )
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        description = f"Deleted user '{instance.username}'"
        authenticated_user = request.user

        # Log the audit action before deletion
        logs_audit_action(instance, AuditTrail.AuditTrailsAction.DELETE, description, authenticated_user)

        # Proceed with deletion
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@permission_classes(IsAuthenticated)
def get_user_perms(request, pk):
    try:
        user = User.objects.get(pk=pk)
        user_perms = Permission.objects.filter(user=user).values_list('codename', flat=True)
        group_perms = Permission.objects.filter(group__user=user).values_list('codename', flat=True)
        all_perms = list(set(user_perms) | set(group_perms))  # Combine permissions
        return JsonResponse({
            'current_user_permissions': all_perms,
        })
    except User.DoesNotExist:
        return JsonResponse({"detail": "user doesn't exist", }, status=404)


class VoucherRequestListView(generics.ListAPIView):
    """
        created, read, update, delete Voucher_requests:
        view only for authenticated users with rights permissions
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
            validated_data = serializer.validated_data

            # ✅ Remove invalid or memoryview files before save
            for field in ["request_doc_pdf", "pop_doc_pdf"]:
                if field in validated_data:
                    file_candidate = validated_data[field]
                    if not isinstance(file_candidate, UploadedFile):
                        validated_data.pop(field)

            new_request_status = validated_data.get('request_status')
            current_status = voucher_request.request_status

            cannot_be_modified = (
                    current_status == approved_status or
                    current_status == rejected_status or
                    (current_status == paid_status and new_request_status == pending_status)
            )

            try:
                if current_status == paid_status and new_request_status == approved_status:
                    validated_data["date_time_approved"] = timezone.now()
                    validated_data["approved_by"] = request.user
                    description = f"Approved voucher_request: {voucher_request.request_ref}."
                    logs_audit_action(
                        voucher_request,
                        AuditTrail.AuditTrailsAction.UPDATE,
                        description, request.user
                    )

                elif current_status == pending_status and new_request_status == approved_status:
                    return Response(
                        {
                            "detail": "The request must be in 'Paid' status before it can be approved."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                elif cannot_be_modified:
                    return Response(
                        {
                            "detail": f"This voucher request is already {voucher_request.request_status}. You cannot modify it."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            except IntegrityError:
                return Response(
                    {"detail": "There was a data integrity issue."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            except DatabaseError:
                return Response(
                    {"detail": "A database error occurred."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            except Exception as e:
                return Response(
                    {"detail": f"An unexpected error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            if hasattr(voucher_request, "request_doc_pdf") and isinstance(voucher_request.request_doc_pdf, memoryview):
                voucher_request.request_doc_pdf = None

            if hasattr(voucher_request, "pop_doc_pdf") and isinstance(voucher_request.pop_doc_pdf, memoryview):
                voucher_request.pop_doc_pdf = None

            # ✅ Use validated_data directly to update and bypass bad file input
            serializer.update(voucher_request, validated_data)

            if current_status != new_request_status:
                description = (
                    f"change voucher request {voucher_request.request_ref} from "
                    f"{current_status} to {new_request_status}."
                )
                logs_audit_action(
                    voucher_request,
                    AuditTrail.AuditTrailsAction.UPDATE,
                    description, request.user
                )

            return Response(self.serializer_class(voucher_request).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        voucher_request = self.get_object()
        description = f"Deleted voucher request: ' {voucher_request.request_ref}'"
        authenticated_user = request.user

        # Log the audit action before deletion
        logs_audit_action(voucher_request, AuditTrail.AuditTrailsAction.DELETE, description, authenticated_user)

        # Proceed with deletion
        voucher_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def flatten_querydict(querydict):
    return {k: v[0] if isinstance(v, list) else v for k, v in querydict.lists()}


class VoucherRequestCreateView(generics.CreateAPIView):
    queryset = VoucherRequest.objects.all()
    serializer_class = VoucherRequestCrudSerializer
    permission_classes = [
        IsAuthenticated,
        CustomDjangoModelPermissions
    ]

    def post(self, request, *args, **kwargs):
        try:
            data = flatten_querydict(request.data)
            files = {k: request.FILES.getlist(k)[0] for k in request.FILES}
            serializer = self.get_serializer(data={**data, **files})

            if serializer.is_valid():
                try:
                    self.perform_create(serializer)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    return Response({"detail": f"Storage error: {str(e)}"}, status=500)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            import traceback
            traceback.print_exc()

    def perform_create(self, serializer):
        """
        Save the voucher request with the user who created it
        and log the audit action.
        """
        voucher_request = serializer.save(recorded_by=self.request.user)

        # Loguer l'action d'audit avant la création
        description = f"Created voucher request: {voucher_request.request_ref}"
        authenticated_user = self.request.user
        logs_audit_action(voucher_request, AuditTrail.AuditTrailsAction.ADD, description, authenticated_user)


class ClientListView(generics.ListAPIView):
    """display a list of all clients"""
    queryset = Client.objects.all()
    serializer_class = ClientListSerializer
    filter_backends = [filters.SearchFilter]
    pagination_class = ClientsPagination
    search_fields = ['=emails']
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
        authenticated_user = request.user
        client = self.get_object()
        old_data = ClientCrudSerializer(client).data

        serializer = self.get_serializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            new_data = serializer.data
            description = (
                f"Updated client data:\nBefore:\n{json.dumps(old_data, indent=4)}\n"
                f"After:\n{json.dumps(new_data, indent=4)}"
            )

            # Log the audit action after update
            logs_audit_action(client, AuditTrail.AuditTrailsAction.UPDATE, description, authenticated_user)

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        client = self.get_object()
        description = f"Deleted client: 'fullname: ' {client.clientname} {client.lastname}'; email: ' {client.email}'"
        authenticated_user = request.user

        # Log the audit action before deletion
        logs_audit_action(client, AuditTrail.AuditTrailsAction.DELETE, description, authenticated_user)

        # Proceed with deletion
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
            Add a new client and log the audit action
        """
        authenticated_user = request.user
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Perform the creation of the client
            self.perform_create(serializer)

            # Retrieve the created client instance
            client = serializer.instance

            # Description for the audit log
            description = f"Added new client: fullname: {client.clientname};\n email: {client.email}"

            # Log the audit action
            logs_audit_action(client, AuditTrail.AuditTrailsAction.ADD, description, authenticated_user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoucherViewSet(viewsets.ModelViewSet):
    """
        created, read, update, delete Vouchers:
        view only for authenticated users with rights permissions
    """
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    pagination_class = VoucherPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['=voucher_ref']
    filterset_fields = [
        'voucher_status', 'redemption__shop',
        'redemption__redemption_date', "voucher_request"
    ]
    permission_classes = [
        IsAuthenticated, CustomDjangoModelPermissions
    ]

    def get_object(self):
        """ find a client by id """
        try:
            return self.queryset.get(pk=self.kwargs['pk'])
        except Client.DoesNotExist:
            raise NotFound(detail="client not found")

    def destroy(self, request, *args, **kwargs):
        voucher = self.get_object()
        description = f"Deleted voucher: {voucher.voucher_ref}"
        authenticated_user = request.user

        # Log the audit action before deletion
        logs_audit_action(voucher, AuditTrail.AuditTrailsAction.DELETE, description, authenticated_user)

        # Proceed with deletion
        self.perform_destroy(voucher)

        # Optionally, if you want to handle any post-deletion actions
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['company_name']

    def perform_create(self, serializer):
        company = serializer.save()
        logs_audit_action(
            instance=company,
            action=AuditTrail.AuditTrailsAction.ADD,
            description=f"Added new company: '{company.company_name}'",
            user=self.request.user
        )

    def update(self, request, *args, **kwargs):
        company_before_update = self.get_object()
        old_company_name = company_before_update.company_name
        # save changes
        response = super().update(request, *args, **kwargs)

        company_after_update = self.get_object()
        new_company_name = company_after_update.company_name

        # check in the name changed
        if old_company_name != new_company_name:
            description = f"Updated company, changed company_name.\n from '{old_company_name}' to '{new_company_name}'"
        else:
            description = f"Updated company: {new_company_name}"

        authenticated_user = request.user

        # Log the audit action for update
        logs_audit_action(
            instance=company_after_update,
            action=AuditTrail.AuditTrailsAction.UPDATE,
            description=description,
            user=authenticated_user
        )

        return response

    def destroy(self, request, *args, **kwargs):
        company = self.get_object()
        description = f"Deleted company: '{company.company_name}'"
        authenticated_user = request.user

        # Log the audit action before deletion
        logs_audit_action(company, AuditTrail.AuditTrailsAction.DELETE, description, authenticated_user)

        # Proceed with deletion
        self.perform_destroy(company)
        return Response(status=status.HTTP_204_NO_CONTENT)


# this view only returns a list of all companies without authentication
# (necessary to allow mobile app users to set up the app(select the company))
class CompanyList(generics.ListAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [AllowAny]


# this view only returns a list of all shops without authentication
# (necessary to allow mobile app users to set up the app(select the shop))
class ShopList(generics.ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    filterset_fields = ['company']
    permission_classes = [AllowAny]


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
        authenticated_user = request.user
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
            redemption_date = localtime(redemption["redeemed_on"])
            formatted_date = redemption_date.strftime('%d %b %Y, %H:%M')
            # log audit for after redemption
            description = (
                f"Redemption for voucher: {voucher.voucher_ref}.\n redeemed at: "
                f" {redemption['redeemed_at']}.\n On '{formatted_date}'"
            )
            logs_audit_action(voucher.redemption, AuditTrail.AuditTrailsAction.ADD, description, authenticated_user)
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
        except NotAuthenticated as e:
            return Response(
                {"details": "Authentication required. Please log in to continue."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        except PermissionDenied as e:
            return Response(
                {"details": "You do not have permission to redeem this voucher."},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response({"details": f"Sorry something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    queryset = AuditTrail.objects.all()
    serializer_class = AuditTrailsSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUser, CustomDjangoModelPermissions
    ]


def password_reset_confirm(request, uidb64, token):
    context = {"uidb64": uidb64, "token": token}
    return render(request, 'reset_password_form.html', context)


def password_reset_send_email(request):
    url = f"{settings.BASE_URL}/vms/auth/users/reset_password/"
    if request.method == "POST":
        email = request.POST["email"]
        post_email = requests.post(url, {"email": email})
        status_code = post_email.status_code
        if status_code == 204:
            context = {"success_message": "We've sent you an email, please check your inbox"}
            return render(request, "reset_password_send_email.html", context)
        else:
            response = post_email.json()
            context = {"error_message": response[0]}
            print(context)
            return render(request, "reset_password_send_email.html", context)
    else:
        return render(request, "reset_password_send_email.html")


def password_reset_success_view(request):
    return render(request, 'password_reset_success.html')


@login_required(login_url="/vms/login/")
def approve_request_view(request, request_ref):
    try:
        voucher_request = VoucherRequest.objects.get(request_ref=request_ref)
    except VoucherRequest.DoesNotExist:
        return render(request, 'admin/404.html')

    requester = voucher_request.client if voucher_request.client else None

    if request.method == "POST":
        validity_period = request.POST.get("validity_periode")
        validity_type = request.POST.get("validity_type")
        if validity_period and validity_type:
            try:
                voucher_request.validity_period = validity_period
                voucher_request.validity_type = validity_type
                voucher_request.request_status = "approved"
                voucher_request.approved_by = request.user
                voucher_request.save()
                return redirect("/vms/request_approved_success/")
            except Exception as e:
                context = {
                    "error_message": "Sorry, something went wrong. Please try again later.",
                    "voucher_request": voucher_request,
                    "requester": requester,
                }
                return render(request, 'approve_request.html', context)
        else:
            context = {
                "error_message": "Please fill in all required fields.",
                "voucher_request": voucher_request,
                "requester": requester,
            }
            return render(request, 'approve_request.html', context)

    context = {"voucher_request": voucher_request, "requester": requester}
    return render(request, 'approve_request.html', context)


@login_required(login_url="/vms/login/")
def request_approved_success_view(request):
    """succes page after a voucher request was approved"""
    return render(request, 'request_approved_success.html')


def not_found_view(request):
    return render(request, 'admin/404.html')


@login_required(login_url="/vms/login/")
def index(request):
    return redirect('swagger-ui')


def login_view(request):
    # Get the next URL (the URL the user wanted to access before being redirected to the login page)
    """
        login view that redirect to the swagger ui doc or
        view voucher_request approval view depending on param 'next'
    """
    next_url = request.GET.get('next', '/')
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_post = request.POST.get('next', '/')
            return redirect(next_post)
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password.",
                "next": next_url
            })
    else:
        return render(request, "login.html", {"next": next_url})


def logout_view(request):
    if request.method == "POST":
        next_url = request.POST.get('next_url', '/')
        logout(request)
        return redirect(next_url)
    logout(request)
    return redirect("/")


def test_pdf(request):
    return render(request, "voucher_pdf_template.html")


"""
@Todo: reset password in admin and login view for documentation
@Approve voucher request in browser
"""
