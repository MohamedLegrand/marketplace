from django.urls import path

from . import views

app_name = "avis_client"

urlpatterns = [
    path("", views.mes_avis, name="mes_avis"),
    path("produit/<int:produit_pk>/", views.noter_produit, name="noter_produit"),
    path("boutique/<int:boutique_pk>/", views.noter_boutique, name="noter_boutique"),
    path("<int:pk>/supprimer/", views.supprimer, name="supprimer"),
]
