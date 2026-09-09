from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.shortcuts import render
from django.utils import timezone

from admin.boutiques.models import Boutique, JournalModeration, RoleBoutique


class JournalModerationInline(admin.TabularInline):
    model = JournalModeration
    extra = 0
    can_delete = False
    fields = ("date", "action", "administrateur", "ancien_statut", "nouveau_statut", "motif")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class RoleBoutiqueInline(admin.TabularInline):
    model = RoleBoutique
    extra = 0
    fields = ("utilisateur", "type_role", "libelle", "actif")
    autocomplete_fields = ("utilisateur",)


@admin.register(Boutique)
class BoutiqueAdmin(admin.ModelAdmin):
    list_display = ("nom", "proprietaire", "categorie", "ville", "statut", "date_soumission")
    list_filter = ("statut", "categorie", "ville")
    search_fields = ("nom", "proprietaire__email", "email", "telephone")
    date_hierarchy = "date_creation"
    ordering = ("-date_creation",)
    inlines = (RoleBoutiqueInline, JournalModerationInline)
    actions = ("valider", "reactiver", "rejeter", "suspendre", "bannir")

    readonly_fields = (
        "slug",
        "date_soumission",
        "date_decision",
        "decide_par",
        "date_creation",
        "date_modification",
    )
    fieldsets = (
        ("Boutique", {"fields": ("nom", "slug", "proprietaire", "categorie", "logo", "description")}),
        ("Coordonnees", {"fields": ("telephone", "email", "adresse", "ville")}),
        ("Moderation", {"fields": ("statut", "motif_rejet", "date_soumission", "date_decision", "decide_par")}),
        ("Dates", {"fields": ("date_creation", "date_modification")}),
    )

    # ------------------------------------------------------------------
    # Actions sans motif
    # ------------------------------------------------------------------
    @admin.action(description="Valider (approuver) les boutiques selectionnees")
    def valider(self, request, queryset):
        from admin.kyc.services import kyc_valide

        cibles = queryset.filter(statut__in=[Boutique.Statut.EN_ATTENTE, Boutique.Statut.REJETEE])
        approuvees, bloquees = 0, []
        for boutique in cibles:
            if not kyc_valide(boutique.proprietaire):
                bloquees.append(boutique.nom)
                continue
            boutique.appliquer_decision(
                request.user, Boutique.Statut.APPROUVEE, JournalModeration.Action.VALIDATION
            )
            approuvees += 1
        if approuvees:
            self.message_user(request, f"{approuvees} boutique(s) approuvee(s).")
        if bloquees:
            self.message_user(
                request,
                "KYC non valide, boutiques non approuvees : " + ", ".join(bloquees),
                level=messages.ERROR,
            )

    @admin.action(description="Reactiver les boutiques suspendues")
    def reactiver(self, request, queryset):
        cibles = queryset.filter(statut=Boutique.Statut.SUSPENDUE)
        for boutique in cibles:
            boutique.appliquer_decision(
                request.user, Boutique.Statut.APPROUVEE, JournalModeration.Action.REACTIVATION
            )
        self.message_user(request, f"{cibles.count()} boutique(s) reactivee(s).")

    # ------------------------------------------------------------------
    # Actions avec motif obligatoire (page intermediaire)
    # ------------------------------------------------------------------
    @admin.action(description="Rejeter les boutiques selectionnees")
    def rejeter(self, request, queryset):
        return self._action_avec_motif(
            request, queryset, Boutique.Statut.REJETEE, JournalModeration.Action.REJET, "rejeter"
        )

    @admin.action(description="Suspendre les boutiques selectionnees")
    def suspendre(self, request, queryset):
        return self._action_avec_motif(
            request, queryset, Boutique.Statut.SUSPENDUE, JournalModeration.Action.SUSPENSION, "suspendre"
        )

    @admin.action(description="Bannir definitivement les boutiques selectionnees")
    def bannir(self, request, queryset):
        return self._action_avec_motif(
            request, queryset, Boutique.Statut.BANNIE, JournalModeration.Action.BANNISSEMENT, "bannir"
        )

    def _action_avec_motif(self, request, queryset, nouveau_statut, action, libelle):
        if request.POST.get("confirmer"):
            motif = request.POST.get("motif", "").strip()
            if not motif:
                self.message_user(request, "Le motif est obligatoire.", level=messages.ERROR)
            else:
                for boutique in queryset:
                    boutique.appliquer_decision(request.user, nouveau_statut, action, motif)
                self.message_user(request, f"{queryset.count()} boutique(s) : {libelle} effectue.")
                return None

        contexte = {
            **self.admin_site.each_context(request),
            "titre": f"Confirmer : {libelle}",
            "libelle": libelle,
            "action": request.POST.get("action"),
            "boutiques": queryset,
            "selection": request.POST.getlist(ACTION_CHECKBOX_NAME),
            "opts": self.model._meta,
        }
        return render(request, "admin/boutiques/action_motif.html", contexte)


@admin.register(RoleBoutique)
class RoleBoutiqueAdmin(admin.ModelAdmin):
    list_display = ("libelle", "type_role", "boutique", "utilisateur", "actif", "date_creation")
    list_filter = ("type_role", "actif")
    search_fields = ("libelle", "boutique__nom", "utilisateur__email")
    autocomplete_fields = ("boutique", "utilisateur")


@admin.register(JournalModeration)
class JournalModerationAdmin(admin.ModelAdmin):
    list_display = ("date", "boutique", "action", "administrateur", "ancien_statut", "nouveau_statut")
    list_filter = ("action", "date")
    search_fields = ("boutique__nom", "administrateur__email", "motif")
    date_hierarchy = "date"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
