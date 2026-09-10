from django.conf import settings
from django.db import models


class AdresseLivraison(models.Model):
    """Adresse de livraison enregistree par un acheteur.

    Table SQL : "adresse_livraison".
    """

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="adresses",
        verbose_name="client",
        db_column="client_id",
    )
    libelle = models.CharField(
        "libelle", max_length=50, help_text="Ex. : Domicile, Bureau.", db_column="libelle"
    )
    nom_destinataire = models.CharField("nom du destinataire", max_length=150, db_column="nom_destinataire")
    telephone = models.CharField("telephone", max_length=20, db_column="telephone")
    ville = models.CharField("ville", max_length=100, db_column="ville")
    quartier = models.CharField("quartier", max_length=120, blank=True, db_column="quartier")
    details = models.CharField(
        "precisions (rue, reperes...)", max_length=255, blank=True, db_column="details"
    )
    par_defaut = models.BooleanField("adresse par defaut", default=False, db_column="par_defaut")

    date_creation = models.DateTimeField("creee le", auto_now_add=True, db_column="date_creation")
    date_modification = models.DateTimeField("modifiee le", auto_now=True, db_column="date_modification")

    class Meta:
        db_table = "adresse_livraison"
        verbose_name = "adresse de livraison"
        verbose_name_plural = "adresses de livraison"
        ordering = ["-par_defaut", "-date_creation"]

    def __str__(self):
        return f"{self.libelle} - {self.ville}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.par_defaut:
            AdresseLivraison.objects.filter(client=self.client).exclude(pk=self.pk).update(
                par_defaut=False
            )
