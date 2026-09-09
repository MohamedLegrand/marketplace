from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Plan(models.Model):
    """Formule d'abonnement mensuel souscrite par un vendeur.

    Le prix et les quotas sont entierement modifiables par l'administrateur.
    Un quota vide (NULL) signifie "illimite".

    Table SQL : "plan_abonnement".
    """

    nom = models.CharField("nom", max_length=80, unique=True, db_column="nom")
    slug = models.SlugField("slug", max_length=100, unique=True, blank=True, db_column="slug")
    description = models.TextField("description", blank=True, db_column="description")

    prix = models.PositiveIntegerField("prix mensuel (XAF)", db_column="prix")
    duree_jours = models.PositiveIntegerField(
        "duree d'une periode (jours)", default=30, db_column="duree_jours"
    )

    max_boutiques = models.PositiveIntegerField(
        "nombre max de boutiques",
        null=True,
        blank=True,
        help_text="Laisser vide pour un nombre illimite.",
        db_column="max_boutiques",
    )
    max_roles = models.PositiveIntegerField(
        "nombre max de roles delegues",
        null=True,
        blank=True,
        help_text="Laisser vide pour un nombre illimite.",
        db_column="max_roles",
    )
    delegation_roles = models.BooleanField(
        "delegation de roles autorisee", default=True, db_column="delegation_roles"
    )
    ia_analyse_ventes = models.BooleanField(
        "IA d'analyse des ventes incluse", default=False, db_column="ia_analyse_ventes"
    )

    actif = models.BooleanField(
        "propose a la souscription", default=True, db_column="actif"
    )
    ordre = models.PositiveSmallIntegerField(
        "ordre d'affichage", default=0, db_column="ordre"
    )

    date_creation = models.DateTimeField(
        "cree le", auto_now_add=True, db_column="date_creation"
    )
    date_modification = models.DateTimeField(
        "modifie le", auto_now=True, db_column="date_modification"
    )

    class Meta:
        db_table = "plan_abonnement"
        verbose_name = "plan d'abonnement"
        verbose_name_plural = "plans d'abonnement"
        ordering = ["ordre", "prix"]

    def __str__(self):
        return f"{self.nom} ({self.prix} XAF/mois)"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    @property
    def boutiques_illimitees(self):
        return self.max_boutiques is None

    @property
    def roles_illimites(self):
        return self.max_roles is None


class Abonnement(models.Model):
    """Souscription d'un vendeur a un plan. Un abonnement couvre l'ensemble des
    boutiques du vendeur (le plan fixe combien il peut en ouvrir).

    Table SQL : "abonnement".
    """

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente de paiement"
        ACTIF = "actif", "Actif"
        EXPIRE = "expire", "Expire"
        ANNULE = "annule", "Annule"

    vendeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abonnements",
        verbose_name="vendeur",
        db_column="vendeur_id",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="abonnements",
        verbose_name="plan",
        db_column="plan_id",
    )
    statut = models.CharField(
        "statut",
        max_length=12,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
        db_column="statut",
    )
    montant = models.PositiveIntegerField(
        "montant paye (XAF)", default=0, db_column="montant"
    )
    reference_paiement = models.CharField(
        "reference de paiement", max_length=100, blank=True, db_column="reference_paiement"
    )
    date_debut = models.DateTimeField(
        "debut", null=True, blank=True, db_column="date_debut"
    )
    date_fin = models.DateTimeField(
        "echeance", null=True, blank=True, db_column="date_fin"
    )
    date_creation = models.DateTimeField(
        "cree le", auto_now_add=True, db_column="date_creation"
    )
    date_modification = models.DateTimeField(
        "modifie le", auto_now=True, db_column="date_modification"
    )

    class Meta:
        db_table = "abonnement"
        verbose_name = "abonnement"
        verbose_name_plural = "abonnements"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.vendeur} - {self.plan.nom} ({self.get_statut_display()})"

    @property
    def est_actif(self):
        return (
            self.statut == self.Statut.ACTIF
            and self.date_fin is not None
            and self.date_fin >= timezone.now()
        )

    @property
    def jours_restants(self):
        if not self.date_fin:
            return 0
        return max((self.date_fin - timezone.now()).days, 0)

    def activer(self, reference="", duree_jours=None):
        """Confirme le paiement et (re)positionne l'echeance. Un renouvellement
        avant echeance prolonge la periode en cours au lieu de la remplacer."""
        maintenant = timezone.now()
        duree = duree_jours or self.plan.duree_jours
        base = self.date_fin if (self.date_fin and self.date_fin > maintenant) else maintenant
        self.statut = self.Statut.ACTIF
        self.montant = self.plan.prix
        if reference:
            self.reference_paiement = reference
        if not self.date_debut:
            self.date_debut = maintenant
        self.date_fin = base + timedelta(days=duree)
        self.save()

    def annuler(self):
        self.statut = self.Statut.ANNULE
        self.save(update_fields=["statut", "date_modification"])

    def marquer_expire(self):
        self.statut = self.Statut.EXPIRE
        self.save(update_fields=["statut", "date_modification"])
