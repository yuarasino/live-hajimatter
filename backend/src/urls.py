from django.urls import path

from src.views import home, index

urlpatterns = [
    path("", index, name="index"),
    path("home/", home, name="home"),
]
