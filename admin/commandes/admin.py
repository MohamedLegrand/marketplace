from django.contrib import admin

from admin.commandes.models import Commande, LigneCommande, SuiviCommande


class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    fields = ("designation", "prix_unitaire", "quantite", "sous_total")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class SuiviCommandeInline(admin.TabularInline):
    model = SuiviCommande
    extra = 0
    fields = ("date", "auteur", "ancien_statut", "nouveau_statut", "commentaire")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ("reference", "client", "boutique", "statut", "total", "date_creation")
    list_filter = ("statut", "boutique")
    search_fields = ("reference", "client__email", "adresse_nom", "adresse_telephone")
    date_hierarchy = "date_creation"
    inlines = (LigneCommandeInline, SuiviCommandeInline)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
