from django.urls import path

from . import views

app_name = "comptes_client"

urlpatterns = [
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", views.Connexion.as_view(), name="connexion"),
    path("deconnexion/", views.Deconnexion.as_view(), name="deconnexion"),
    path("mot-de-passe/", views.ChangerMotDePasse.as_view(), name="mot_de_passe"),
    path("", views.tableau_de_bord, name="tableau_de_bord"),
    path("boutiques/", views.boutiques, name="boutiques"),
    path("profil/", views.profil, name="profil"),
    path("adresses/", views.adresses, name="adresses"),
    path("adresses/ajouter/", views.adresse_creer, name="adresse_creer"),
    path("adresses/<int:pk>/modifier/", views.adresse_modifier, name="adresse_modifier"),
    path("adresses/<int:pk>/defaut/", views.adresse_defaut, name="adresse_defaut"),
    path("adresses/<int:pk>/supprimer/", views.adresse_supprimer, name="adresse_supprimer"),
]
