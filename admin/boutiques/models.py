from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class BoutiqueQuerySet(models.QuerySet):
    def visibles(self):
        """Boutiques approuvees dont le proprietaire a un abonnement actif."""
        return self.filter(
            statut=Boutique.Statut.APPROUVEE,
            proprietaire__abonnements__statut="actif",
            proprietaire__abonnements__date_fin__gte=timezone.now(),
        ).distinct()


class Boutique(models.Model):
    """Boutique creee par un vendeur et validee par un administrateur.

    Table SQL : "boutique".
    """

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EN_ATTENTE = "en_attente", "En attente de validation"
        APPROUVEE = "approuvee", "Approuvee"
        REJETEE = "rejetee", "Rejetee"
        SUSPENDUE = "suspendue", "Suspendue"
        BANNIE = "bannie", "Bannie"

    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="boutiques",
        verbose_name="proprietaire",
        db_column="proprietaire_id",
    )
    nom = models.CharField("nom", max_length=150, db_column="nom")
    slug = models.SlugField("slug", max_length=170, unique=True, db_column="slug")
    logo = models.ImageField(
        "logo",
        upload_to="boutiques/logos/",
        blank=True,
        null=True,
        db_column="logo",
    )
    description = models.TextField("description", db_column="description")
    categorie = models.ForeignKey(
        "categories.Categorie",
        on_delete=models.PROTECT,
        related_name="boutiques",
        verbose_name="categorie",
        null=True,
        blank=True,
        db_column="categorie_id",
    )

    telephone = models.CharField("telephone", max_length=20, db_column="telephone")
    email = models.EmailField("e-mail", db_column="email")
    adresse = models.CharField("adresse", max_length=255, blank=True, db_column="adresse")
    ville = models.CharField("ville", max_length=100, db_column="ville")

    statut = models.CharField(
        "statut",
        max_length=15,
        choices=Statut.choices,
        default=Statut.BROUILLON,
        db_column="statut",
    )
    motif_rejet = models.TextField(
        "motif du rejet / de la sanction", blank=True, db_column="motif_rejet"
    )

    date_soumission = models.DateTimeField(
        "soumise le", null=True, blank=True, db_column="date_soumission"
    )
    date_decision = models.DateTimeField(
        "decision le", null=True, blank=True, db_column="date_decision"
    )
    decide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="boutiques_moderees",
        verbose_name="decidee par",
        null=True,
        blank=True,
        db_column="decide_par_id",
    )

    note_moyenne = models.DecimalField(
        "note moyenne", max_digits=3, decimal_places=2, default=0, db_column="note_moyenne"
    )
    nombre_avis = models.PositiveIntegerField("nombre d'avis", default=0, db_column="nombre_avis")

    date_creation = models.DateTimeField(
        "creee le", auto_now_add=True, db_column="date_creation"
    )
    date_modification = models.DateTimeField(
        "modifiee le", auto_now=True, db_column="date_modification"
    )

    objects = BoutiqueQuerySet.as_manager()

    class Meta:
        db_table = "boutique"
        verbose_name = "boutique"
        verbose_name_plural = "boutiques"
        ordering = ["-date_creation"]

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # A la creation, le vendeur doit avoir un abonnement actif et rester
        # dans le quota de boutiques de son plan.
        if self._state.adding and self.proprietaire_id:
            from admin.abonnements.services import peut_creer_boutique

            autorise, message = peut_creer_boutique(self.proprietaire)
            if not autorise:
                raise ValidationError(message)

    @property
    def est_visible(self):
        """Visible publiquement uniquement si la boutique est approuvee ET si
        son proprietaire a un abonnement actif (blocage en cas de
        non-renouvellement)."""
        if self.statut != self.Statut.APPROUVEE:
            return False
        from admin.abonnements.services import abonnement_actif

        return abonnement_actif(self.proprietaire) is not None

    def soumettre(self):
        """Soumission (ou re-soumission) de la boutique par le vendeur."""
        ancien_statut = self.statut
        self.statut = self.Statut.EN_ATTENTE
        self.motif_rejet = ""
        self.date_soumission = timezone.now()
        self.date_decision = None
        self.decide_par = None
        self.save(update_fields=[
            "statut", "motif_rejet", "date_soumission", "date_decision",
            "decide_par", "date_modification",
        ])
        JournalModeration.objects.create(
            boutique=self,
            administrateur=None,
            action=JournalModeration.Action.SOUMISSION,
            ancien_statut=ancien_statut,
            nouveau_statut=self.statut,
        )

    def appliquer_decision(self, admin_user, nouveau_statut, action, motif=""):
        """Change le statut, horodate la decision et ecrit le journal."""
        ancien_statut = self.statut
        self.statut = nouveau_statut
        self.motif_rejet = motif
        self.date_decision = timezone.now()
        self.decide_par = admin_user
        self.save(update_fields=[
            "statut", "motif_rejet", "date_decision", "decide_par", "date_modification",
        ])
        JournalModeration.objects.create(
            boutique=self,
            administrateur=admin_user,
            action=action,
            motif=motif,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
        )


class JournalModeration(models.Model):
    """Historique des decisions de moderation prises sur une boutique.

    Table SQL : "journal_moderation".
    """

    class Action(models.TextChoices):
        SOUMISSION = "soumission", "Soumission"
        VALIDATION = "validation", "Validation"
        REJET = "rejet", "Rejet"
        SUSPENSION = "suspension", "Suspension"
        REACTIVATION = "reactivation", "Reactivation"
        BANNISSEMENT = "bannissement", "Bannissement"

    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.CASCADE,
        related_name="evenements_moderation",
        verbose_name="boutique",
        db_column="boutique_id",
    )
    administrateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="actions_moderation",
        verbose_name="administrateur",
        db_column="administrateur_id",
    )
    action = models.CharField(
        "action", max_length=15, choices=Action.choices, db_column="action"
    )
    motif = models.TextField("motif", blank=True, db_column="motif")
    ancien_statut = models.CharField(
        "ancien statut", max_length=15, blank=True, db_column="ancien_statut"
    )
    nouveau_statut = models.CharField(
        "nouveau statut", max_length=15, blank=True, db_column="nouveau_statut"
    )
    date = models.DateTimeField("date", auto_now_add=True, db_column="date")

    class Meta:
        db_table = "journal_moderation"
        verbose_name = "evenement de moderation"
        verbose_name_plural = "journal de moderation"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.boutique}"


class RoleBoutique(models.Model):
    """Role delegue par un vendeur a un membre de son equipe pour une boutique
    (caissier, vendeur 1, vendeur 2...). La possibilite d'en creer et leur
    nombre dependent du plan d'abonnement du proprietaire.

    Table SQL : "role_boutique".
    """

    class TypeRole(models.TextChoices):
        GESTIONNAIRE = "gestionnaire", "Gestionnaire"
        VENDEUR = "vendeur", "Vendeur"
        CAISSIER = "caissier", "Caissier"

    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.CASCADE,
        related_name="roles",
        verbose_name="boutique",
        db_column="boutique_id",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roles_boutique",
        verbose_name="utilisateur",
        db_column="utilisateur_id",
    )
    type_role = models.CharField(
        "type de role", max_length=15, choices=TypeRole.choices, db_column="type_role"
    )
    libelle = models.CharField(
        "libelle",
        max_length=50,
        blank=True,
        help_text="Nom affiche, ex. : Vendeur 1.",
        db_column="libelle",
    )

    peut_gerer_produits = models.BooleanField(
        "gerer les produits", default=False, db_column="peut_gerer_produits"
    )
    peut_gerer_stock = models.BooleanField(
        "gerer le stock", default=False, db_column="peut_gerer_stock"
    )
    peut_gerer_commandes = models.BooleanField(
        "gerer les commandes", default=True, db_column="peut_gerer_commandes"
    )
    peut_voir_statistiques = models.BooleanField(
        "voir les statistiques", default=False, db_column="peut_voir_statistiques"
    )

    actif = models.BooleanField("actif", default=True, db_column="actif")
    date_creation = models.DateTimeField(
        "cree le", auto_now_add=True, db_column="date_creation"
    )
    date_modification = models.DateTimeField(
        "modifie le", auto_now=True, db_column="date_modification"
    )

    class Meta:
        db_table = "role_boutique"
        verbose_name = "role de boutique"
        verbose_name_plural = "roles de boutique"
        ordering = ["boutique", "type_role"]
        constraints = [
            models.UniqueConstraint(
                fields=["boutique", "utilisateur"],
                name="unique_role_par_utilisateur_boutique",
            )
        ]

    def __str__(self):
        return f"{self.libelle or self.get_type_role_display()} @ {self.boutique}"

    def clean(self):
        super().clean()
        if self._state.adding and self.boutique_id:
            from admin.abonnements.services import peut_creer_role

            autorise, message = peut_creer_role(self.boutique)
            if not autorise:
                raise ValidationError(message)


class ZoneLivraison(models.Model):
    """Zone de livraison couverte par une boutique et son tarif.

    La logistique est propre a chaque boutique (pas de transporteur central).
    Table SQL : "zone_livraison".
    """

    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.CASCADE,
        related_name="zones_livraison",
        verbose_name="boutique",
        db_column="boutique_id",
    )
    nom = models.CharField("zone", max_length=100, db_column="nom")
    tarif = models.PositiveIntegerField("tarif de livraison (XAF)", default=0, db_column="tarif")
    delai_estime = models.CharField(
        "delai estime",
        max_length=50,
        blank=True,
        help_text="Ex. : 24 a 48 h.",
        db_column="delai_estime",
    )
    actif = models.BooleanField("active", default=True, db_column="actif")
    date_creation = models.DateTimeField(
        "creee le", auto_now_add=True, db_column="date_creation"
    )
    date_modification = models.DateTimeField(
        "modifiee le", auto_now=True, db_column="date_modification"
    )

    class Meta:
        db_table = "zone_livraison"
        verbose_name = "zone de livraison"
        verbose_name_plural = "zones de livraison"
        ordering = ["boutique", "nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["boutique", "nom"], name="unique_zone_par_boutique"
            )
        ]

    def __str__(self):
        return f"{self.nom} ({self.tarif} XAF)"
