from django.urls import path
from .views import *


urlpatterns = [
    path('api/register', RegisterView.as_view()),
    path('api/user', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })),
    path('api/login', LoginView.as_view()),
    path('api/jwks.json', json_token),
    path('api/refresh-tokens', RefreshTokensView.as_view()),
    path('api/сurrencies', CurrencyList.as_view()),
    path('api/user_settings', UserSettingsView.as_view({
        'put': 'update',
        'get': 'get'
    })),
]
