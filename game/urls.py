from django.urls import path

from . import views

app_name = "game"

urlpatterns = [
    path("", views.home, name="home"),
    path("run/start/", views.start_run, name="start_run"),
]
