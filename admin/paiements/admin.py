from django.contrib import admin

from admin.paiements.models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        "reference_externe", "type", "statut", "montant", "frais",
        "operateur", "telephone", "date_creation", "date_confirmation",
    )
    list_filter = ("statut", "type", "operateur")
    search_fields = ("reference_externe", "transaction_id", "telephone",
                     "commande__reference", "abonnement__vendeur__email")
    date_hierarchy = "date_creation"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
