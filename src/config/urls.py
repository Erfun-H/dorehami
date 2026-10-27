from django.contrib import admin
from django.urls import include, path

from events.views import home

import os

urlpatterns = [
    path(os.getenv("DJANGO_ADMIN_PATH", "admin/"), admin.site.urls),
    path("", home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("events/", include("events.urls")),
]
