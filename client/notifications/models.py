from django.conf import settings
from django.db import models


class Notification(models.Model):
    """Notification affichee a un acheteur dans son espace (paiement
    confirme, commande livree...). Table SQL : "notification"."""

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="destinataire",
        db_column="destinataire_id",
    )
    titre = models.CharField("titre", max_length=150, db_column="titre")
    message = models.CharField("message", max_length=255, db_column="message")
    lien = models.CharField("lien", max_length=255, blank=True, db_column="lien")
    lu = models.BooleanField("lue", default=False, db_column="lu")
    date_creation = models.DateTimeField("cree le", auto_now_add=True, db_column="date_creation")

    class Meta:
        db_table = "notification"
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.titre} - {self.destinataire}"
