from django.urls import path, include
from . import views
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
)

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('vouchers', VoucherViewSet)
router.register('companies', CompanyViewSet)
router.register('shops', ShopViewSet)

app_name = 'vms_app'
urlpatterns = [
    path("vms_api/", include(router.urls)),

    # token views
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # register view
    path("vms_api/register/", UserRegisterView.as_view(), name="register"),

    # views related to client model
    path("vms_api/clients/", ClientListView.as_view(), name="clients-list"),
    path("vms_api/clients/<int:pk>/", ClientCRUDView.as_view(), name="client-details"),
    path("vms_api/clients/add/", ClientCreateView.as_view(), name="new-client"),

    # views related to voucher_request model
    path("vms_api/voucher_requests/", VoucherRequestListView.as_view(), name="requests-list"),
    path("vms_api/voucher_requests/<int:pk>/", VoucherRequestCrudView.as_view(), name="requests-details"),
    path("vms_api/voucher_requests/add/", VoucherRequestCreateView.as_view(), name="new-request"),
    path('latest_id/', views.get_latest_id, name="latest_id")
]