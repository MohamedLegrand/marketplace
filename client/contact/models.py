from django.db import models


class MessageContact(models.Model):
    """Message envoye depuis le formulaire de contact du site public.

    Table SQL : "message_contact".
    """

    nom = models.CharField("nom", max_length=120, db_column="nom")
    email = models.EmailField("e-mail", blank=True, db_column="email")
    telephone = models.CharField("telephone", max_length=20, blank=True, db_column="telephone")
    message = models.TextField("message", db_column="message")
    traite = models.BooleanField("traite", default=False, db_column="traite")
    date_creation = models.DateTimeField("recu le", auto_now_add=True, db_column="date_creation")

    class Meta:
        db_table = "message_contact"
        verbose_name = "message de contact"
        verbose_name_plural = "messages de contact"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.nom} — {self.date_creation:%d/%m/%Y}"
