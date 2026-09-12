from django.contrib import admin

from .models import Conversation, MessageIA


class MessageInline(admin.TabularInline):
    model = MessageIA
    extra = 0
    readonly_fields = ("role", "contenu", "date_creation")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("boutique", "date_creation", "date_modification")
    search_fields = ("boutique__nom", "boutique__proprietaire__email")
    readonly_fields = ("boutique", "date_creation", "date_modification")
    inlines = [MessageInline]

    def has_add_permission(self, request):
        return False
