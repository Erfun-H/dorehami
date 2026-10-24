from django.urls import include, path

from events.views import home

urlpatterns = [
    path("", home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("events/", include("events.urls")),
]
