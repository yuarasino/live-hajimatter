from django.contrib import admin
from django.contrib.auth.views import logout_then_login
from django.urls import include, path

urlpatterns = [
    path("__admin__/", admin.site.urls),
    path("", include("social_django.urls")),
    path("logout/", logout_then_login, name="logout"),
    path("", include("src.urls")),
]
