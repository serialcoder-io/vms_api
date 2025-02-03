"""
URL configuration for vms_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from djoser.views import UserViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path('vms/', include('vms_app.urls')),
    # Pour récupérer et mettre à jour les infos du user connecté
    path('vms/auth/users/me/', UserViewSet.as_view({'get': 'me', 'put': 'me'}), name='user-me'),

    # Pour réinitialiser le mot de passe
    path('vms/auth/password_reset/', UserViewSet.as_view({'post': 'reset_password'}), name='password-reset'),
    path('vms/auth/password_reset_confirm/', UserViewSet.as_view({'post': 'reset_password_confirm'}), name='password-reset-confirm'),

    # Pour changer le mot de passe (quand l'utilisateur est authentifié)
    path('vms/auth/password_change/', UserViewSet.as_view({'post': 'set_password'}), name='password-change'),
]
