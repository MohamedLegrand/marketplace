from django.urls import path

from . import views

app_name = "commandes_vendeur"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("<int:commande_pk>/", views.detail, name="detail"),
    path("<int:commande_pk>/statut/", views.changer_statut, name="changer_statut"),
]
