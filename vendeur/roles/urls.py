from django.urls import path

from . import views

app_name = "roles_vendeur"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("ajouter/", views.ajouter, name="ajouter"),
    path("<int:role_pk>/modifier/", views.modifier, name="modifier"),
    path("<int:role_pk>/basculer/", views.basculer_actif, name="basculer"),
    path("<int:role_pk>/retirer/", views.retirer, name="retirer"),
]
