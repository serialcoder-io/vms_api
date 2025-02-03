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
    UserRegisterView,
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
    redeem_voucher
)

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('vouchers', VoucherViewSet)
router.register('companies', CompanyViewSet)
router.register('shops', ShopViewSet)
router.register('redemptions', RedemptionViewSet)

app_name = 'vms_app'
urlpatterns = [
    path("api/", include(router.urls)),

    # token views
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # register view
    path("api/register/", UserRegisterView.as_view(), name="register"),

    # views related to client model
    path("api/clients/", ClientListView.as_view(), name="clients_list"),
    path("api/clients/<int:pk>/", ClientCRUDView.as_view(), name="client_details"),
    path("api/clients/add/", ClientCreateView.as_view(), name="new_client"),

    # views related to voucher_request model
    path("api/voucher_requests/", VoucherRequestListView.as_view(), name="requests_list"),
    path("api/voucher_requests/<int:pk>/", VoucherRequestCrudView.as_view(), name="request_details"),
    path("api/voucher_requests/add/", VoucherRequestCreateView.as_view(), name="new_request"),
    path("api/vouchers/<int:voucher_id>/redeem/", redeem_voucher, name="redeem_voucher"),
]