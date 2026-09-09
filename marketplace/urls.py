"""Configuration des URL du projet marketplace."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

# Personnalisation des titres du back-office.
admin.site.site_header = "Administration - Marketplace"
admin.site.site_title = "Marketplace"
admin.site.index_title = "Gestion de la plateforme"

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
