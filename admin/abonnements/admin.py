from django.contrib import admin, messages

from admin.abonnements.models import Abonnement, Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "prix",
        "duree_jours",
        "max_boutiques",
        "max_roles",
        "delegation_roles",
        "ia_analyse_ventes",
        "actif",
        "ordre",
    )
    list_editable = ("prix", "actif", "ordre")
    list_filter = ("actif", "delegation_roles", "ia_analyse_ventes")
    search_fields = ("nom",)
    prepopulated_fields = {"slug": ("nom",)}
    fieldsets = (
        ("Identite", {"fields": ("nom", "slug", "description", "ordre", "actif")}),
        ("Tarif", {"fields": ("prix", "duree_jours")}),
        ("Quotas et fonctionnalites", {
            "fields": ("max_boutiques", "max_roles", "delegation_roles", "ia_analyse_ventes"),
            "description": "Un quota vide = illimite.",
        }),
    )


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = (
        "vendeur",
        "plan",
        "statut",
        "montant",
        "date_debut",
        "date_fin",
        "jours_restants_affiche",
        "actif_affiche",
    )
    list_filter = ("statut", "plan")
    search_fields = ("vendeur__email", "vendeur__username", "reference_paiement")
    autocomplete_fields = ("vendeur", "plan")
    readonly_fields = ("montant", "date_debut", "date_fin", "date_creation", "date_modification")
    actions = ("activer_paiement", "renouveler_periode", "marquer_expire", "annuler_abonnements")

    @admin.display(description="jours restants")
    def jours_restants_affiche(self, obj):
        return obj.jours_restants

    @admin.display(boolean=True, description="actif ?")
    def actif_affiche(self, obj):
        return obj.est_actif

    @admin.action(description="Activer (paiement confirme)")
    def activer_paiement(self, request, queryset):
        for ab in queryset:
            ab.activer()
        self.message_user(request, f"{queryset.count()} abonnement(s) active(s).")

    @admin.action(description="Renouveler d'une periode")
    def renouveler_periode(self, request, queryset):
        for ab in queryset:
            ab.activer()
        self.message_user(request, f"{queryset.count()} abonnement(s) renouvele(s).")

    @admin.action(description="Marquer comme expire")
    def marquer_expire(self, request, queryset):
        n = queryset.update(statut=Abonnement.Statut.EXPIRE)
        self.message_user(request, f"{n} abonnement(s) expire(s).", level=messages.WARNING)

    @admin.action(description="Annuler")
    def annuler_abonnements(self, request, queryset):
        n = queryset.update(statut=Abonnement.Statut.ANNULE)
        self.message_user(request, f"{n} abonnement(s) annule(s).", level=messages.WARNING)
