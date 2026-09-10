from django.urls import path

from . import views

app_name = "panier"

urlpatterns = [
    path("", views.voir, name="voir"),
    path("ajouter/", views.ajouter, name="ajouter"),
    path("modifier/", views.modifier, name="modifier"),
    path("retirer/", views.retirer, name="retirer"),
    path("vider/", views.vider, name="vider"),
]
