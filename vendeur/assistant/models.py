from django.db import models


class Conversation(models.Model):
    """Fil de discussion avec l'assistant IA, un par boutique.

    Reserve aux vendeurs dont l'abonnement actif inclut l'analyse IA des
    ventes (``Plan.ia_analyse_ventes``).

    Table SQL : "conversation_ia".
    """

    boutique = models.OneToOneField(
        "boutiques.Boutique",
        on_delete=models.CASCADE,
        related_name="conversation_ia",
        verbose_name="boutique",
        db_column="boutique_id",
    )
    date_creation = models.DateTimeField(
        "creee le", auto_now_add=True, db_column="date_creation"
    )
    date_modification = models.DateTimeField(
        "modifiee le", auto_now=True, db_column="date_modification"
    )

    class Meta:
        db_table = "conversation_ia"
        verbose_name = "conversation IA"
        verbose_name_plural = "conversations IA"
        ordering = ["-date_modification"]

    def __str__(self):
        return f"Conversation IA - {self.boutique.nom}"


class MessageIA(models.Model):
    """Un tour de la conversation (question du vendeur ou reponse de l'IA).

    Table SQL : "message_ia".
    """

    class Role(models.TextChoices):
        UTILISATEUR = "utilisateur", "Vendeur"
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
        db_table = "message_ia"
        verbose_name = "message IA"
        verbose_name_plural = "messages IA"
        ordering = ["date_creation"]

    def __str__(self):
        return f"{self.get_role_display()} : {self.contenu[:40]}"
