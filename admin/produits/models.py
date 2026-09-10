from django.db import models
from django.utils.text import slugify


class ProduitQuerySet(models.QuerySet):
    def disponibles(self):
        """Produits mis en vente et non masques par l'administrateur.
        (Le stock et la visibilite de la boutique se verifient a l'achat.)"""
        return self.filter(actif=True, masque_par_admin=False)


class Produit(models.Model):
    """Produit vendu par une boutique.

    Pas de validation admin (contrairement aux boutiques) : le produit est
    visible des que la boutique l'est. L'admin peut toutefois le masquer.

    Table SQL : "produit".
    """

    boutique = models.ForeignKey(
        "boutiques.Boutique",
        on_delete=models.CASCADE,
        related_name="produits",
        verbose_name="boutique",
        db_column="boutique_id",
    )
    nom = models.CharField("nom", max_length=180, db_column="nom")
    slug = models.SlugField("slug", max_length=200, db_column="slug")
    description = models.TextField("description", db_column="description")
    categorie = models.ForeignKey(
        "categories.Categorie",
        on_delete=models.PROTECT,
        related_name="produits",
        verbose_name="categorie",
        null=True,
        blank=True,
        db_column="categorie_id",
    )
    prix = models.PositiveIntegerField("prix (XAF)", db_column="prix")
    stock = models.PositiveIntegerField(
        "stock (si pas de variantes)", default=0, db_column="stock"
    )
    actif = models.BooleanField("mis en vente par le vendeur", default=True, db_column="actif")
    masque_par_admin = models.BooleanField(
        "masque par l'administrateur", default=False, db_column="masque_par_admin"
    )

    date_creation = models.DateTimeField("cree le", auto_now_add=True, db_column="date_creation")
    date_modification = models.DateTimeField("modifie le", auto_now=True, db_column="date_modification")

    objects = ProduitQuerySet.as_manager()

    class Meta:
        db_table = "produit"
        verbose_name = "produit"
        verbose_name_plural = "produits"
        ordering = ["-date_creation"]
        constraints = [
            models.UniqueConstraint(fields=["boutique", "slug"], name="unique_slug_par_boutique"),
        ]

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nom) or "produit"
            slug, suffixe = base, 1
            qs = Produit.objects.filter(boutique_id=self.boutique_id).exclude(pk=self.pk)
            while qs.filter(slug=slug).exists():
                suffixe += 1
                slug = f"{base}-{suffixe}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def a_variantes(self):
        return self.variantes.exists()

    @property
    def stock_total(self):
        if self.a_variantes:
            return sum(v.stock for v in self.variantes.filter(actif=True))
        return self.stock

    @property
    def disponible(self):
        """Achetable publiquement."""
        if not self.actif or self.masque_par_admin:
            return False
        if not self.boutique.est_visible:
            return False
        return self.stock_total > 0

    @property
    def photo_principale(self):
        return self.photos.filter(principale=True).first() or self.photos.first()


class PhotoProduit(models.Model):
    """Photo d'un produit. Table SQL : "photo_produit"."""

    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="produit",
        db_column="produit_id",
    )
    image = models.ImageField("image", upload_to="produits/photos/", db_column="image")
    principale = models.BooleanField("photo principale", default=False, db_column="principale")
    ordre = models.PositiveSmallIntegerField("ordre", default=0, db_column="ordre")
    date_creation = models.DateTimeField("ajoutee le", auto_now_add=True, db_column="date_creation")

    class Meta:
        db_table = "photo_produit"
        verbose_name = "photo de produit"
        verbose_name_plural = "photos de produit"
        ordering = ["produit", "ordre", "id"]

    def __str__(self):
        return f"Photo #{self.pk} - {self.produit}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.principale:
            PhotoProduit.objects.filter(produit=self.produit).exclude(pk=self.pk).update(
                principale=False
            )


class VarianteProduit(models.Model):
    """Declinaison d'un produit (taille, couleur...) avec son propre stock et,
    au besoin, son propre prix. Table SQL : "variante_produit"."""

    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="variantes",
        verbose_name="produit",
        db_column="produit_id",
    )
    libelle = models.CharField("libelle", max_length=100, help_text="Ex. : Rouge - M", db_column="libelle")
    prix = models.PositiveIntegerField(
        "prix (XAF)", null=True, blank=True,
        help_text="Laisser vide pour utiliser le prix du produit.", db_column="prix",
    )
    stock = models.PositiveIntegerField("stock", default=0, db_column="stock")
    actif = models.BooleanField("active", default=True, db_column="actif")
    date_creation = models.DateTimeField("creee le", auto_now_add=True, db_column="date_creation")
    date_modification = models.DateTimeField("modifiee le", auto_now=True, db_column="date_modification")

    class Meta:
        db_table = "variante_produit"
        verbose_name = "variante de produit"
        verbose_name_plural = "variantes de produit"
        ordering = ["produit", "libelle"]
        constraints = [
            models.UniqueConstraint(fields=["produit", "libelle"], name="unique_libelle_par_produit"),
        ]

    def __str__(self):
        return f"{self.produit} - {self.libelle}"

    @property
    def prix_effectif(self):
        return self.prix if self.prix is not None else self.produit.prix
