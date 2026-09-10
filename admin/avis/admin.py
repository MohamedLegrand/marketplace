from django.contrib import admin, messages

from admin.avis.models import Avis


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ("note", "cible_affichee", "auteur", "statut", "date_creation")
    list_filter = ("statut", "note")
    search_fields = (
        "auteur__email", "commentaire",
        "produit__nom", "boutique__nom",
    )
    date_hierarchy = "date_creation"
    actions = ("masquer_avis", "publier_avis")
    readonly_fields = ("auteur", "commande", "produit", "boutique", "note",
                       "commentaire", "date_creation", "date_modification")

    @admin.display(description="cible")
    def cible_affichee(self, obj):
        return f"produit : {obj.produit}" if obj.produit_id else f"boutique : {obj.boutique}"

    @admin.action(description="Masquer les avis selectionnes")
    def masquer_avis(self, request, queryset):
        n = 0
        for avis in queryset:
            avis.masquer()
            n += 1
        self.message_user(request, f"{n} avis masque(s).", level=messages.WARNING)

    @admin.action(description="Publier les avis selectionnes")
    def publier_avis(self, request, queryset):
        n = 0
        for avis in queryset:
            avis.publier()
            n += 1
        self.message_user(request, f"{n} avis publie(s).")
