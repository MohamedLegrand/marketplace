"""Configuration des URL du projet marketplace."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Personnalisation des titres du back-office.
admin.site.site_header = "Administration - Marketplace"
admin.site.site_title = "Marketplace"
admin.site.index_title = "Gestion de la plateforme"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("vendeur/boutiques/<int:boutique_pk>/equipe/", include("vendeur.roles.urls")),
    path("vendeur/boutiques/<int:boutique_pk>/produits/", include("vendeur.produits.urls")),
    path("vendeur/boutiques/", include("vendeur.boutiques.urls")),
    path("vendeur/", include("vendeur.comptes.urls")),
    path("panier/", include("client.panier.urls")),
    path("", include("client.catalogue.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
