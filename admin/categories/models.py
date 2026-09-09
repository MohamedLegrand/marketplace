from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Categorie(models.Model):
    """Categorie de boutique ou de produit, definie par l'administrateur.

    - ``type`` distingue les categories de boutiques de celles de produits ;
    - ``parent`` permet une hierarchie (categorie / sous-categorie).

    Table SQL : "categorie".
    """

    class Type(models.TextChoices):
        BOUTIQUE = "boutique", "Categorie de boutique"
        PRODUIT = "produit", "Categorie de produit"

    nom = models.CharField("nom", max_length=100, db_column="nom")
    slug = models.SlugField("slug", max_length=120, unique=True, blank=True, db_column="slug")
    description = models.TextField("description", blank=True, db_column="description")
    type = models.CharField(
        "type", max_length=10, choices=Type.choices, default=Type.PRODUIT, db_column="type"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="enfants",
        verbose_name="categorie parente",
        null=True,
        blank=True,
        db_column="parent_id",
    )
    actif = models.BooleanField("active", default=True, db_column="actif")
    ordre = models.PositiveSmallIntegerField("ordre d'affichage", default=0, db_column="ordre")

    date_creation = models.DateTimeField("creee le", auto_now_add=True, db_column="date_creation")
    date_modification = models.DateTimeField("modifiee le", auto_now=True, db_column="date_modification")

    class Meta:
        db_table = "categorie"
        verbose_name = "categorie"
        verbose_name_plural = "categories"
        ordering = ["type", "ordre", "nom"]
        constraints = [
            models.UniqueConstraint(fields=["type", "nom"], name="unique_nom_par_type_categorie"),
        ]

    def __str__(self):
        if self.parent_id:
            return f"{self.parent} > {self.nom}"
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.type}-{self.nom}")
            self.slug = base
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.parent_id:
            if self.parent_id == self.pk:
                raise ValidationError("Une categorie ne peut pas etre sa propre parente.")
            if self.parent.type != self.type:
                raise ValidationError("La categorie parente doit etre du meme type.")
            # Empeche les cycles sur une hierarchie simple.
            ancetre = self.parent
            while ancetre is not None:
                if ancetre.pk == self.pk:
                    raise ValidationError("Hierarchie de categories circulaire.")
                ancetre = ancetre.parent
