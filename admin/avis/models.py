from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Avis(models.Model):
    """Avis (note + commentaire) depose par un acheteur sur un produit OU une
    boutique, apres reception d'une commande livree.

    Table SQL : "avis".
    """

    class Statut(models.TextChoices):
        PUBLIE = "publie", "Publie"
        MASQUE = "masque", "Masque par l'administrateur"

    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="avis", verbose_name="auteur", db_column="auteur_id",
    )
    commande = models.ForeignKey(
        "commandes.Commande", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="avis", verbose_name="commande liee", db_column="commande_id",
    )
    produit = models.ForeignKey(
        "produits.Produit", on_delete=models.CASCADE, null=True, blank=True,
        related_name="avis", verbose_name="produit", db_column="produit_id",
    )
    boutique = models.ForeignKey(
        "boutiques.Boutique", on_delete=models.CASCADE, null=True, blank=True,
        related_name="avis", verbose_name="boutique", db_column="boutique_id",
    )

    note = models.PositiveSmallIntegerField(
        "note", validators=[MinValueValidator(1), MaxValueValidator(5)], db_column="note"
    )
    commentaire = models.TextField("commentaire", blank=True, db_column="commentaire")
    statut = models.CharField(
        "statut", max_length=10, choices=Statut.choices,
        default=Statut.PUBLIE, db_column="statut",
    )

    date_creation = models.DateTimeField("cree le", auto_now_add=True, db_column="date_creation")
    date_modification = models.DateTimeField("modifie le", auto_now=True, db_column="date_modification")

    class Meta:
        db_table = "avis"
        verbose_name = "avis"
        verbose_name_plural = "avis"
        ordering = ["-date_creation"]
        constraints = [
            models.UniqueConstraint(
                fields=["auteur", "produit"], condition=models.Q(produit__isnull=False),
                name="unique_avis_par_produit",
            ),
            models.UniqueConstraint(
                fields=["auteur", "boutique"], condition=models.Q(boutique__isnull=False),
                name="unique_avis_par_boutique",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(produit__isnull=False, boutique__isnull=True)
                    | models.Q(produit__isnull=True, boutique__isnull=False)
                ),
                name="avis_cible_unique",
            ),
        ]

    def __str__(self):
        return f"{self.note}/5 - {self.cible}"

    @property
    def cible(self):
        return self.produit or self.boutique

    def clean(self):
        super().clean()
        if bool(self.produit_id) == bool(self.boutique_id):
            raise ValidationError("Un avis porte sur un produit OU une boutique.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._recalculer_cible()

    def delete(self, *args, **kwargs):
        cible = self.cible
        super().delete(*args, **kwargs)
        from admin.avis.services import recalculer_agregats

        if cible is not None:
            recalculer_agregats(cible)

    def _recalculer_cible(self):
        from admin.avis.services import recalculer_agregats

        recalculer_agregats(self.cible)

    def publier(self):
        self.statut = self.Statut.PUBLIE
        self.save()

    def masquer(self):
        self.statut = self.Statut.MASQUE
        self.save()
