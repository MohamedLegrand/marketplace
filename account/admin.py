from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from account.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "username",
        "role",
        "is_active",
        "is_staff",
        "date_creation",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "username", "telephone")
    ordering = ("-date_creation",)
    actions = ("desactiver_comptes", "reactiver_comptes")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "telephone")}),
        ("Role et permissions", {
            "fields": (
                "role",
                "is_active",
                "motif_desactivation",
                "date_desactivation",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Dates", {"fields": ("last_login", "date_joined", "date_creation", "date_modification")}),
    )
    readonly_fields = (
        "last_login",
        "date_joined",
        "date_desactivation",
        "date_creation",
        "date_modification",
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "role", "password1", "password2"),
        }),
    )

    @admin.action(description="Desactiver les comptes selectionnes")
    def desactiver_comptes(self, request, queryset):
        n = 0
        for utilisateur in queryset:
            utilisateur.desactiver()
            n += 1
        self.message_user(request, f"{n} compte(s) desactive(s).", level=messages.WARNING)

    @admin.action(description="Reactiver les comptes selectionnes")
    def reactiver_comptes(self, request, queryset):
        n = 0
        for utilisateur in queryset:
            utilisateur.reactiver()
            n += 1
        self.message_user(request, f"{n} compte(s) reactive(s).")
