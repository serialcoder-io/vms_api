from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    UserRegisterView,
    ClientViewSet,
    VoucherViewSet,
    VoucherRequestViewSet,
    CompanyViewSet,
    ShopViewSet
)

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('clients', ClientViewSet)
router.register('vouchers', VoucherViewSet)
router.register('voucher_requests', VoucherRequestViewSet)
router.register('companies', CompanyViewSet)
router.register('shops', ShopViewSet)

from django.urls import path, include
from . import views
urlpatterns = [
    path('', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('latest_id/', views.get_latest_id, name="latest_id")
]