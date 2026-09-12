from django.conf import settings
from django.db import models, transaction
from django.db.models import F
from django.utils.crypto import get_random_string


class Commande(models.Model):
    """Commande passee par un acheteur aupres d'une boutique.

    Un panier ne contenant qu'une boutique, une commande = une boutique.
    Les informations produit et adresse sont figees a l'achat.

    Table SQL : "commande".
    """

    class Statut(models.TextChoices):
        EN_ATTENTE_PAIEMENT = "en_attente_paiement", "En attente de paiement"
        CONFIRMEE = "confirmee", "Confirmee"
        EN_PREPARATION = "en_preparation", "En preparation"
        EXPEDIEE = "expediee", "Expediee"
        LIVREE = "livree", "Livree"
        ANNULEE = "annulee", "Annulee"

    reference = models.CharField("reference", max_length=20, unique=True, db_column="reference")
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="commandes", verbose_name="client", db_column="client_id",
    )
    boutique = models.ForeignKey(
        "boutiques.Boutique", on_delete=models.PROTECT,
        related_name="commandes", verbose_name="boutique", db_column="boutique_id",
    )

    # Adresse de livraison figee
    adresse_nom = models.CharField("destinataire", max_length=150, db_column="adresse_nom")
    adresse_telephone = models.CharField("telephone", max_length=20, db_column="adresse_telephone")
    adresse_ville = models.CharField("ville", max_length=100, db_column="adresse_ville")
    adresse_quartier = models.CharField("quartier", max_length=120, blank=True, db_column="adresse_quartier")
    adresse_details = models.CharField("precisions", max_length=255, blank=True, db_column="adresse_details")

    zone_nom = models.CharField("zone de livraison", max_length=100, blank=True, db_column="zone_nom")
    frais_livraison = models.PositiveIntegerField("frais de livraison (XAF)", default=0, db_column="frais_livraison")
    sous_total = models.PositiveIntegerField("sous-total (XAF)", default=0, db_column="sous_total")
    total = models.PositiveIntegerField("total (XAF)", default=0, db_column="total")

    statut = models.CharField(
        "statut", max_length=20, choices=Statut.choices,
        default=Statut.EN_ATTENTE_PAIEMENT, db_column="statut",
    )
    date_creation = models.DateTimeField("passee le", auto_now_add=True, db_column="date_creation")
    date_modification = models.DateTimeField("modifiee le", auto_now=True, db_column="date_modification")

    class Meta:
        db_table = "commande"
        verbose_name = "commande"
        verbose_name_plural = "commandes"
        ordering = ["-date_creation"]

    def __str__(self):
        return self.reference

    def save(self, *args, **kwargs):
        if not self.reference:
            ref = "CMD-" + get_random_string(8).upper()
            while Commande.objects.filter(reference=ref).exists():
                ref = "CMD-" + get_random_string(8).upper()
            self.reference = ref
        super().save(*args, **kwargs)

    @property
    def nb_articles(self):
        return sum(l.quantite for l in self.lignes.all())

    @property
    def annulable_par_client(self):
        return self.statut in (self.Statut.EN_ATTENTE_PAIEMENT, self.Statut.CONFIRMEE)

    def changer_statut(self, auteur, nouveau, commentaire=""):
        ancien = self.statut
        self.statut = nouveau
        self.save(update_fields=["statut", "date_modification"])
        SuiviCommande.objects.create(
            commande=self, auteur=auteur, ancien_statut=ancien,
            nouveau_statut=nouveau, commentaire=commentaire,
        )

    @transaction.atomic
    def annuler(self, auteur, commentaire=""):
        if self.statut == self.Statut.ANNULEE:
            return
        from admin.produits.models import MouvementStock, Produit, VarianteProduit

        for ligne in self.lignes.all():
            if ligne.variante_id:
                VarianteProduit.objects.filter(pk=ligne.variante_id).update(
                    stock=F("stock") + ligne.quantite
                )
            elif ligne.produit_id:
                Produit.objects.filter(pk=ligne.produit_id).update(
                    stock=F("stock") + ligne.quantite
                )
            if ligne.produit_id:
                MouvementStock.objects.create(
                    produit_id=ligne.produit_id,
                    variante_id=ligne.variante_id,
                    type_mouvement=MouvementStock.Type.ANNULATION,
                    quantite=ligne.quantite,
                    montant=ligne.prix_unitaire * ligne.quantite,
                    commande=self,
                    auteur=auteur if getattr(auteur, "pk", None) else None,
                )
        self.changer_statut(auteur, self.Statut.ANNULEE, commentaire or "Commande annulee")


class LigneCommande(models.Model):
    """Ligne d'une commande : instantane d'un produit/variante achete.

    Table SQL : "ligne_commande".
    """

    commande = models.ForeignKey(
        Commande, on_delete=models.CASCADE, related_name="lignes",
        verbose_name="commande", db_column="commande_id",
    )
    produit = models.ForeignKey(
        "produits.Produit", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lignes_commande", verbose_name="produit", db_column="produit_id",
    )
    variante = models.ForeignKey(
        "produits.VarianteProduit", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lignes_commande", verbose_name="variante", db_column="variante_id",
    )
    designation = models.CharField("designation", max_length=250, db_column="designation")
    prix_unitaire = models.PositiveIntegerField("prix unitaire (XAF)", db_column="prix_unitaire")
    quantite = models.PositiveIntegerField("quantite", db_column="quantite")

    class Meta:
        db_table = "ligne_commande"
        verbose_name = "ligne de commande"
        verbose_name_plural = "lignes de commande"
        ordering = ["id"]

    def __str__(self):
        return f"{self.designation} x{self.quantite}"

    @property
    def sous_total(self):
        return self.prix_unitaire * self.quantite


class SuiviCommande(models.Model):
    """Historique des changements de statut d'une commande.

    Table SQL : "suivi_commande".
    """

    commande = models.ForeignKey(
        Commande, on_delete=models.CASCADE, related_name="suivis",
        verbose_name="commande", db_column="commande_id",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="suivis_commande", verbose_name="auteur", db_column="auteur_id",
    )
    ancien_statut = models.CharField(
        "ancien statut", max_length=20, blank=True,
        choices=Commande.Statut.choices, db_column="ancien_statut",
    )
    nouveau_statut = models.CharField(
        "nouveau statut", max_length=20, blank=True,
        choices=Commande.Statut.choices, db_column="nouveau_statut",
    )
    commentaire = models.TextField("commentaire", blank=True, db_column="commentaire")
    date = models.DateTimeField("date", auto_now_add=True, db_column="date")

    class Meta:
        db_table = "suivi_commande"
        verbose_name = "suivi de commande"
        verbose_name_plural = "suivis de commande"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.commande.reference} : {self.nouveau_statut}"
