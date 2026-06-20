from django.urls import path

from . import views

app_name = "game"

urlpatterns = [
    path("", views.home, name="home"),
    path("run/start/", views.start_run, name="start_run"),
    path("run/abandon/", views.abandon_run, name="abandon_run"),
    path("battle/", views.battle, name="battle"),
    path("battle/roll/", views.battle_roll, name="battle_roll"),
    path("battle/action/", views.battle_action, name="battle_action"),
    path("battle/skill/", views.choose_skill, name="choose_skill"),
]
