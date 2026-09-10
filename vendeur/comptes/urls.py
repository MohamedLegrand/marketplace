from django.urls import path

from . import views

app_name = "comptes_vendeur"

urlpatterns = [
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", views.Connexion.as_view(), name="connexion"),
    path("deconnexion/", views.Deconnexion.as_view(), name="deconnexion"),
    path("mot-de-passe/", views.ChangerMotDePasse.as_view(), name="mot_de_passe"),
    path("profil/", views.profil, name="profil"),
    path("onboarding/identite/", views.onboarding_identite, name="identite"),
    path("onboarding/forfait/", views.onboarding_forfait, name="forfait"),
    path("onboarding/paiement/", views.onboarding_paiement, name="paiement"),
    path("", views.tableau_de_bord, name="tableau_de_bord"),
]
