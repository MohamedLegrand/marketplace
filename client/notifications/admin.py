from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("destinataire", "titre", "lu", "date_creation")
    list_filter = ("lu",)
    search_fields = ("destinataire__email", "titre", "message")
    readonly_fields = ("destinataire", "titre", "message", "lien", "date_creation")

    def has_add_permission(self, request):
        return False
