from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Fil de discussion avec l'assistant IA d'analyse globale, un par
    administrateur (chaque membre de l'equipe garde son propre historique).

    Contrairement a l'assistant vendeur (une boutique a la fois), celui-ci
    analyse l'integralite des boutiques de la plateforme.

    Table SQL : "conversation_ia_admin".
    """

    administrateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_ia_admin",
        verbose_name="administrateur",
        db_column="administrateur_id",
    )
    date_creation = models.DateTimeField(
        "creee le", auto_now_add=True, db_column="date_creation"
    )
    date_modification = models.DateTimeField(
        "modifiee le", auto_now=True, db_column="date_modification"
    )

    class Meta:
        db_table = "conversation_ia_admin"
        verbose_name = "conversation IA (admin)"
        verbose_name_plural = "conversations IA (admin)"
        ordering = ["-date_modification"]

    def __str__(self):
        return f"Conversation IA admin - {self.administrateur}"


class MessageIA(models.Model):
    """Un tour de la conversation (question de l'admin ou reponse de l'IA).

    Table SQL : "message_ia_admin".
    """

    class Role(models.TextChoices):
        UTILISATEUR = "utilisateur", "Administrateur"
        ASSISTANT = "assistant", "Assistant IA"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="conversation",
        db_column="conversation_id",
    )
    role = models.CharField(
        "role", max_length=12, choices=Role.choices, db_column="role"
    )
    contenu = models.TextField("contenu", db_column="contenu")
    date_creation = models.DateTimeField(
        "envoye le", auto_now_add=True, db_column="date_creation"
    )

    class Meta:
        db_table = "message_ia_admin"
        verbose_name = "message IA (admin)"
        verbose_name_plural = "messages IA (admin)"
        ordering = ["date_creation"]

    def __str__(self):
        return f"{self.get_role_display()} : {self.contenu[:40]}"
