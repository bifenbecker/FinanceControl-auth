from django.urls import path
from .views import *


urlpatterns = [
    path('register', RegisterView.as_view()),
    path('user', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })),
    path('login', LoginView.as_view()),
    path('jwks.json', json_token),
    path('refresh-tokens', RefreshTokensView.as_view()),
    path('сurrencies', CurrencyList.as_view()),
    path('user_settings', UserSettingsView.as_view({
        'put': 'update',
        'get': 'get'
    }))
]
