from django.urls import path

from . import views

app_name = "boutiques_vendeur"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("creer/", views.creer, name="creer"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/modifier/", views.modifier, name="modifier"),
    path("<int:pk>/soumettre/", views.soumettre, name="soumettre"),
    path("<int:pk>/zones/ajouter/", views.zone_creer, name="zone_creer"),
    path("<int:pk>/zones/<int:zone_pk>/modifier/", views.zone_modifier, name="zone_modifier"),
    path("<int:pk>/zones/<int:zone_pk>/supprimer/", views.zone_supprimer, name="zone_supprimer"),
]
