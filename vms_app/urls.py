from django.urls import path, include
# from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    UserViewSet,
    # UserRegisterView,
    VoucherViewSet,
    VoucherRequestListView,
    VoucherRequestCrudView,
    VoucherRequestCreateView,
    CompanyViewSet,
    ShopViewSet,
    ClientListView,
    ClientCRUDView,
    ClientCreateView,
    RedemptionViewSet,
    RedeemVoucherView,
    password_reset_view,
    password_reset_success_view, account_activation, GroupViewSet, PermissionListViewSet
)

router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'users', UserViewSet)
router.register(r'vouchers', VoucherViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'shops', ShopViewSet)
router.register(r'redemptions', RedemptionViewSet)

app_name = 'vms_app'
urlpatterns = [
    path("api/", include(router.urls)),

    # ------------------------- authentication ------------------------

    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/reset_password/<str:uidb64>/<str:token>/", password_reset_view, name="password_reset"),
    path("auth/reset_password_success/", password_reset_success_view, name="password_reset_success"),
    path("auth/activate/<str:uidb64>/<str:token>/", account_activation, name="activate_account"),
    path("auth/permissions/", PermissionListViewSet.as_view(), name="permissions"),

    # -------- urls related to client model ----------
    path("api/clients/", ClientListView.as_view(), name="clients_list"),
    path("api/clients/<int:pk>/", ClientCRUDView.as_view(), name="client_details"),
    path("api/clients/add/", ClientCreateView.as_view(), name="new_client"),

    # -------- urls related to voucher_request model ----------
    path("api/voucher_requests/", VoucherRequestListView.as_view(), name="requests_list"),
    path("api/voucher_requests/<int:pk>/", VoucherRequestCrudView.as_view(), name="request_details"),
    path("api/voucher_requests/add/", VoucherRequestCreateView.as_view(), name="new_request"),

    #------------------- Redeem voucher -------------------------------
    path("api/vouchers/<int:pk>/redeem/",  RedeemVoucherView.as_view(), name="redeem_voucher"),

]