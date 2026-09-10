from django.contrib import admin

from client.contact.models import MessageContact


@admin.register(MessageContact)
class MessageContactAdmin(admin.ModelAdmin):
    list_display = ("nom", "email", "telephone", "traite", "date_creation")
    list_filter = ("traite", "date_creation")
    search_fields = ("nom", "email", "telephone", "message")
    list_editable = ("traite",)
    readonly_fields = ("nom", "email", "telephone", "message", "date_creation")
    date_hierarchy = "date_creation"

    def has_add_permission(self, request):
        return False
