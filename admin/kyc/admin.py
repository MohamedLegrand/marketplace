from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.shortcuts import render
from django.utils.html import format_html

from admin.kyc.models import DossierKYC, JournalKYC


class JournalKYCInline(admin.TabularInline):
    model = JournalKYC
    extra = 0
    can_delete = False
    fields = ("date", "action", "administrateur", "ancien_statut", "nouveau_statut", "motif")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DossierKYC)
class DossierKYCAdmin(admin.ModelAdmin):
    list_display = ("vendeur", "nom_complet", "type_piece", "numero_piece", "statut", "date_soumission", "decide_par")
    list_filter = ("statut", "type_piece")
    search_fields = ("vendeur__email", "nom_complet", "numero_piece", "raison_sociale")
    date_hierarchy = "date_soumission"
    ordering = ("-date_soumission",)
    inlines = (JournalKYCInline,)
    actions = ("valider_dossiers", "rejeter_dossiers")

    readonly_fields = (
        "vendeur",
        "nom_complet",
        "date_naissance",
        "type_piece",
        "numero_piece",
        "raison_sociale",
        "apercu_recto",
        "apercu_verso",
        "apercu_selfie",
        "lien_rccm",
        "date_soumission",
        "date_decision",
        "decide_par",
        "date_creation",
        "date_modification",
    )
    fieldsets = (
        ("Identite declaree", {
            "fields": ("vendeur", "nom_complet", "date_naissance", "type_piece", "numero_piece"),
        }),
        ("Documents", {
            "fields": ("apercu_recto", "apercu_verso", "apercu_selfie"),
        }),
        ("Entreprise", {
            "fields": ("raison_sociale", "lien_rccm"),
        }),
        ("Decision", {
            "fields": ("statut", "motif_rejet", "date_soumission", "date_decision", "decide_par"),
        }),
        ("Dates", {"fields": ("date_creation", "date_modification")}),
    )

    # --- apercus documents -------------------------------------------------
    @admin.display(description="piece - recto")
    def apercu_recto(self, obj):
        return self._image(obj.piece_recto)

    @admin.display(description="piece - verso")
    def apercu_verso(self, obj):
        return self._image(obj.piece_verso)

    @admin.display(description="selfie")
    def apercu_selfie(self, obj):
        return self._image(obj.selfie)

    @admin.display(description="registre de commerce")
    def lien_rccm(self, obj):
        if obj.registre_commerce:
            return format_html('<a href="{}" target="_blank">Ouvrir le document</a>', obj.registre_commerce.url)
        return "-"

    @staticmethod
    def _image(champ):
        if champ:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="max-height:180px;border:1px solid #ccc"></a>',
                champ.url,
            )
        return "-"

    # --- actions ---------------------------------------------------------
    @admin.action(description="Valider les dossiers selectionnes")
    def valider_dossiers(self, request, queryset):
        cibles = queryset.exclude(statut=DossierKYC.Statut.VALIDE)
        for dossier in cibles:
            dossier.valider(request.user)
        self.message_user(request, f"{cibles.count()} dossier(s) KYC valide(s).")

    @admin.action(description="Rejeter les dossiers selectionnes (avec motif)")
    def rejeter_dossiers(self, request, queryset):
        if request.POST.get("confirmer"):
            motif = request.POST.get("motif", "").strip()
            if not motif:
                self.message_user(request, "Le motif de rejet est obligatoire.", level=messages.ERROR)
            else:
                for dossier in queryset:
                    dossier.rejeter(request.user, motif)
                self.message_user(request, f"{queryset.count()} dossier(s) KYC rejete(s).", level=messages.WARNING)
                return None

        contexte = {
            **self.admin_site.each_context(request),
            "titre": "Confirmer le rejet des dossiers KYC",
            "dossiers": queryset,
            "action": "rejeter_dossiers",
            "selection": request.POST.getlist(ACTION_CHECKBOX_NAME),
            "opts": self.model._meta,
        }
        return render(request, "admin/kyc/action_motif.html", contexte)


@admin.register(JournalKYC)
class JournalKYCAdmin(admin.ModelAdmin):
    list_display = ("date", "dossier", "action", "administrateur", "ancien_statut", "nouveau_statut")
    list_filter = ("action", "date")
    search_fields = ("dossier__vendeur__email", "motif")
    date_hierarchy = "date"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
