from django.contrib import admin, messages

from admin.produits.models import PhotoProduit, Produit, VarianteProduit


class PhotoProduitInline(admin.TabularInline):
    model = PhotoProduit
    extra = 0
    fields = ("image", "principale", "ordre")


class VarianteProduitInline(admin.TabularInline):
    model = VarianteProduit
    extra = 0
    fields = ("libelle", "prix", "stock", "actif")


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("nom", "boutique", "categorie", "prix", "stock_total", "actif", "masque_par_admin")
    list_filter = ("masque_par_admin", "actif", "categorie")
    search_fields = ("nom", "boutique__nom", "boutique__proprietaire__email")
    autocomplete_fields = ("boutique", "categorie")
    readonly_fields = ("slug", "date_creation", "date_modification")
    inlines = (PhotoProduitInline, VarianteProduitInline)
    actions = ("masquer", "reafficher")

    @admin.display(description="stock total")
    def stock_total(self, obj):
        return obj.stock_total

    @admin.action(description="Masquer les produits selectionnes")
    def masquer(self, request, queryset):
        n = queryset.update(masque_par_admin=True)
        self.message_user(request, f"{n} produit(s) masque(s).", level=messages.WARNING)

    @admin.action(description="Reafficher les produits selectionnes")
    def reafficher(self, request, queryset):
        n = queryset.update(masque_par_admin=False)
        self.message_user(request, f"{n} produit(s) reaffiche(s).")
