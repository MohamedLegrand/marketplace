from django.conf import settings
from django.db import models
from django.utils import timezone


class DossierKYC(models.Model):
    """Dossier de verification d'identite d'un vendeur (Know Your Customer).

    Le vendeur soumet ses pieces ; l'administrateur consulte puis valide ou
    rejette le dossier en indiquant un motif. Un dossier par vendeur.

    Table SQL : "dossier_kyc".
    """

    class TypePiece(models.TextChoices):
        CNI = "cni", "Carte nationale d'identite"
        PASSEPORT = "passeport", "Passeport"
        PERMIS = "permis", "Permis de conduire"

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EN_ATTENTE = "en_attente", "En attente de verification"
        VALIDE = "valide", "Valide"
        REJETE = "rejete", "Rejete"

    vendeur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dossier_kyc",
        verbose_name="vendeur",
        db_column="vendeur_id",
    )

    # Identite declaree
    nom_complet = models.CharField("nom complet (tel que sur la piece)", max_length=150, db_column="nom_complet")
    date_naissance = models.DateField("date de naissance", null=True, blank=True, db_column="date_naissance")
    type_piece = models.CharField("type de piece", max_length=10, choices=TypePiece.choices, db_column="type_piece")
    numero_piece = models.CharField("numero de la piece", max_length=50, db_column="numero_piece")

    # Documents
    piece_recto = models.ImageField("piece - recto", upload_to="kyc/pieces/", db_column="piece_recto")
    piece_verso = models.ImageField("piece - verso", upload_to="kyc/pieces/", blank=True, null=True, db_column="piece_verso")
    selfie = models.ImageField("photo du vendeur tenant la piece", upload_to="kyc/selfies/", blank=True, null=True, db_column="selfie")

    # Volet entreprise (facultatif)
    raison_sociale = models.CharField("raison sociale", max_length=150, blank=True, db_column="raison_sociale")
    registre_commerce = models.FileField(
        "registre de commerce (RCCM)", upload_to="kyc/rccm/", blank=True, null=True, db_column="registre_commerce"
    )

    # Moderation
    statut = models.CharField(
        "statut", max_length=12, choices=Statut.choices, default=Statut.BROUILLON, db_column="statut"
    )
    motif_rejet = models.TextField("motif du rejet", blank=True, db_column="motif_rejet")
    date_soumission = models.DateTimeField("soumis le", null=True, blank=True, db_column="date_soumission")
    date_decision = models.DateTimeField("decision le", null=True, blank=True, db_column="date_decision")
    decide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="dossiers_kyc_traites",
        verbose_name="verifie par",
        null=True,
        blank=True,
        db_column="decide_par_id",
    )

    date_creation = models.DateTimeField("cree le", auto_now_add=True, db_column="date_creation")
    date_modification = models.DateTimeField("modifie le", auto_now=True, db_column="date_modification")

    class Meta:
        db_table = "dossier_kyc"
        verbose_name = "dossier KYC"
        verbose_name_plural = "dossiers KYC"
        ordering = ["-date_soumission", "-date_creation"]

    def __str__(self):
        return f"KYC {self.vendeur} ({self.get_statut_display()})"

    @property
    def est_valide(self):
        return self.statut == self.Statut.VALIDE

    def _appliquer_decision(self, admin_user, nouveau_statut, action, motif=""):
        ancien = self.statut
        self.statut = nouveau_statut
        self.motif_rejet = motif
        self.date_decision = timezone.now()
        self.decide_par = admin_user
        self.save(update_fields=[
            "statut", "motif_rejet", "date_decision", "decide_par", "date_modification",
        ])
        JournalKYC.objects.create(
            dossier=self,
            administrateur=admin_user,
            action=action,
            motif=motif,
            ancien_statut=ancien,
            nouveau_statut=nouveau_statut,
        )

    def valider(self, admin_user):
        self._appliquer_decision(admin_user, self.Statut.VALIDE, JournalKYC.Action.VALIDATION)

    def rejeter(self, admin_user, motif):
        self._appliquer_decision(admin_user, self.Statut.REJETE, JournalKYC.Action.REJET, motif)

    def soumettre(self):
        """Soumission du dossier par le vendeur (depuis l'espace vendeur)."""
        ancien = self.statut
        self.statut = self.Statut.EN_ATTENTE
        self.motif_rejet = ""
        self.date_soumission = timezone.now()
        self.date_decision = None
        self.decide_par = None
        self.save()
        JournalKYC.objects.create(
            dossier=self,
            administrateur=None,
            action=JournalKYC.Action.SOUMISSION,
            ancien_statut=ancien,
            nouveau_statut=self.statut,
        )


class JournalKYC(models.Model):
    """Historique des decisions prises sur un dossier KYC.

    Table SQL : "journal_kyc".
    """

    class Action(models.TextChoices):
        SOUMISSION = "soumission", "Soumission"
        VALIDATION = "validation", "Validation"
        REJET = "rejet", "Rejet"

    dossier = models.ForeignKey(
        DossierKYC,
        on_delete=models.CASCADE,
        related_name="evenements",
        verbose_name="dossier",
        db_column="dossier_id",
    )
    administrateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="actions_kyc",
        verbose_name="administrateur",
        db_column="administrateur_id",
    )
    action = models.CharField("action", max_length=12, choices=Action.choices, db_column="action")
    motif = models.TextField("motif", blank=True, db_column="motif")
    ancien_statut = models.CharField("ancien statut", max_length=12, blank=True, db_column="ancien_statut")
    nouveau_statut = models.CharField("nouveau statut", max_length=12, blank=True, db_column="nouveau_statut")
    date = models.DateTimeField("date", auto_now_add=True, db_column="date")

    class Meta:
        db_table = "journal_kyc"
        verbose_name = "evenement KYC"
        verbose_name_plural = "journal KYC"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.dossier_id}"
