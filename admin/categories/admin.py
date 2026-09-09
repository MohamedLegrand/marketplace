from django.contrib import admin

from admin.categories.models import Categorie


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "type", "parent", "actif", "ordre", "nb_enfants", "date_creation")
    list_filter = ("type", "actif")
    list_editable = ("actif", "ordre")
    search_fields = ("nom", "description")
    prepopulated_fields = {"slug": ("nom",)}
    autocomplete_fields = ("parent",)
    fieldsets = (
        (None, {"fields": ("nom", "slug", "type", "parent", "description")}),
        ("Affichage", {"fields": ("actif", "ordre")}),
    )

    @admin.display(description="sous-categories")
    def nb_enfants(self, obj):
        return obj.enfants.count()
