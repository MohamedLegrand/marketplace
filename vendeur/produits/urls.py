from django.urls import path

from . import views

app_name = "produits_vendeur"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("creer/", views.creer, name="creer"),
    path("<int:produit_pk>/", views.detail, name="detail"),
    path("<int:produit_pk>/modifier/", views.modifier, name="modifier"),
    path("<int:produit_pk>/basculer/", views.basculer_actif, name="basculer"),
    path("<int:produit_pk>/supprimer/", views.supprimer, name="supprimer"),
    path("<int:produit_pk>/stock/ajouter/", views.stock_ajouter, name="stock_ajouter"),
    path("<int:produit_pk>/photos/ajouter/", views.photo_ajouter, name="photo_ajouter"),
    path("<int:produit_pk>/photos/<int:photo_pk>/principale/", views.photo_principale, name="photo_principale"),
    path("<int:produit_pk>/photos/<int:photo_pk>/supprimer/", views.photo_supprimer, name="photo_supprimer"),
    path("<int:produit_pk>/variantes/ajouter/", views.variante_ajouter, name="variante_ajouter"),
    path("<int:produit_pk>/variantes/<int:variante_pk>/modifier/", views.variante_modifier, name="variante_modifier"),
    path("<int:produit_pk>/variantes/<int:variante_pk>/supprimer/", views.variante_supprimer, name="variante_supprimer"),
]
