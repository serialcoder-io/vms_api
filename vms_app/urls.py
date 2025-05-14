from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView
# from . import views
from django.urls import path
#from .views import user_permissions
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    UserViewSet, VoucherViewSet, CompanyViewSet, ShopViewSet,
    VoucherRequestListView, VoucherRequestCrudView, VoucherRequestCreateView,
    ClientListView, ClientCRUDView, ClientCreateView,
    RedemptionViewSet, RedeemVoucherView, AuditTrailsViewset,
    password_reset_confirm, password_reset_success_view,
    GroupViewSet, PermissionListViewSet, approve_request_view, index, login_view, logout_view,
    password_reset_send_email, request_approved_success_view, not_found_view, test_pdf,
)

router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'users', UserViewSet)
router.register(r'vouchers', VoucherViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'shops', ShopViewSet)
router.register(r'redemptions', RedemptionViewSet)
router.register(r'audit-trails', AuditTrailsViewset)

app_name = 'vms_app'
urlpatterns = [
    path('', index, name='index'),
    path("vms/login/", login_view, name='login'),
    path("vms/logout/", logout_view, name='logout'),
    path("vms/api/", include(router.urls)),

    # ------------------------- authentication ------------------------
    path("vms/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("vms/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("vms/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("vms/auth/reset_password/<str:uidb64>/<str:token>/", password_reset_confirm, name="password_reset_confirm"),
    path("vms/auth/reset_password_send_email/", password_reset_send_email, name="reset_password"),
    path("vms/auth/reset_password_success/", password_reset_success_view, name="password_reset_success"),
    path("vms/auth/permissions/", PermissionListViewSet.as_view(), name="permissions"),

    # -------- urls related to client model ----------
    path("vms/api/clients/", ClientListView.as_view(), name="clients_list"),
    path("vms/api/clients/<int:pk>/", ClientCRUDView.as_view(), name="client_details"),
    path("vms/api/clients/add/", ClientCreateView.as_view(), name="new_client"),

    # -------- urls related to voucher_request model ----------
    path("vms/api/voucher_requests/", VoucherRequestListView.as_view(), name="requests_list"),
    path("vms/api/voucher_requests/<int:pk>/", VoucherRequestCrudView.as_view(), name="request_details"),
    path("vms/api/voucher_requests/add/", VoucherRequestCreateView.as_view(), name="new_request"),

    #------------------- Redeem voucher -------------------------------
    path("vms/api/vouchers/<int:pk>/redeem/",  RedeemVoucherView.as_view(), name="redeem_voucher"),
    re_path(r"^vms/approve_request/(?P<request_ref>.+)/$", approve_request_view, name="approve_request_view"),
    path("vms/request_approved_success/", request_approved_success_view, name="request_approved_success"),
    path("vms/not-found/", not_found_view, name="not_found"),
    path("vms/test_pdf/", test_pdf, name="test_pdf")

]