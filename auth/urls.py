import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path(f'{os.environ.get("SERVICE_NAME", "auth")}/admin', admin.site.urls),
    path(f'{os.environ.get("SERVICE_NAME", "auth")}/api/', include('user.urls')),
    path(f'{os.environ.get("SERVICE_NAME", "auth")}/stripe/', include('payments.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
