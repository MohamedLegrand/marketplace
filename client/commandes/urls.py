from django.urls import path

from . import views

app_name = "commandes_client"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("checkout/", views.checkout, name="checkout"),
    path("<str:reference>/", views.detail, name="detail"),
    path("<str:reference>/confirmation/", views.confirmation, name="confirmation"),
    path("<str:reference>/payer/", views.payer, name="payer"),
    path("<str:reference>/paiement/", views.paiement_suivi, name="paiement_suivi"),
    path("<str:reference>/paiement/verifier/", views.paiement_verifier, name="paiement_verifier"),
    path("<str:reference>/annuler/", views.annuler, name="annuler"),
]
