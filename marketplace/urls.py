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
    path("vendeur/boutiques/<int:boutique_pk>/commandes/", include("vendeur.commandes.urls")),
    path("vendeur/boutiques/<int:boutique_pk>/assistant/", include("vendeur.assistant.urls")),
    path("vendeur/boutiques/", include("vendeur.boutiques.urls")),
    path("vendeur/", include("vendeur.comptes.urls")),
    path("compte/avis/", include("client.avis.urls")),
    path("compte/", include("client.comptes.urls")),
    path("commande/", include("client.commandes.urls")),
    path("panier/", include("client.panier.urls")),
    path("contact/", include("client.contact.urls")),
    path("", include("client.catalogue.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
