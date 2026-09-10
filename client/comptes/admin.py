from django.contrib import admin

from client.comptes.models import AdresseLivraison


@admin.register(AdresseLivraison)
class AdresseLivraisonAdmin(admin.ModelAdmin):
    list_display = ("libelle", "client", "nom_destinataire", "ville", "par_defaut", "date_creation")
    list_filter = ("ville", "par_defaut")
    search_fields = ("client__email", "nom_destinataire", "telephone", "ville")
    autocomplete_fields = ("client",)
