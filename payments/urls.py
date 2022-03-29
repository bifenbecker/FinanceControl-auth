from django.urls import path
from .views import *


urlpatterns = [
    path('stripe-config', stripe_config),
    path('success', success),
    path('cancel', cancel),
    path('set-subscription', StripeViews.as_view({
        'post': 'post'
    })),
]
