from django.urls import path

from . import views

app_name = "catalogue"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("connexion/", views.connexion, name="connexion"),
    path("inscription/", views.inscription, name="inscription"),
    path("a-propos/", views.apropos, name="apropos"),
    path("boutiques/", views.accueil, name="accueil"),
    path("b/<slug:boutique_slug>/", views.boutique, name="boutique"),
    path("b/<slug:boutique_slug>/<slug:produit_slug>/", views.produit, name="produit"),
]
