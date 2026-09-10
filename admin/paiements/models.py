from django.db import models


class Paiement(models.Model):
    """Paiement encaisse (Cash-In) via l'agregateur HR-Skills Pay.

    Un paiement se rattache soit a une commande, soit a un abonnement.
    Statut initial "en_attente" (PENDING), puis "reussi" / "echoue" selon le
    retour de l'API (webhook ou polling).

    Table SQL : "paiement".
    """

    class Type(models.TextChoices):
        COMMANDE = "commande", "Commande"
        ABONNEMENT = "abonnement", "Abonnement"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        REUSSI = "reussi", "Reussi"
        ECHOUE = "echoue", "Echoue"
        BLOQUE = "bloque", "Bloque (revision AML)"
        REMBOURSE = "rembourse", "Rembourse"

    type = models.CharField("type", max_length=12, choices=Type.choices, db_column="type")
    commande = models.ForeignKey(
        "commandes.Commande", on_delete=models.CASCADE, null=True, blank=True,
        related_name="paiements", verbose_name="commande", db_column="commande_id",
    )
    abonnement = models.ForeignKey(
        "abonnements.Abonnement", on_delete=models.CASCADE, null=True, blank=True,
        related_name="paiements", verbose_name="abonnement", db_column="abonnement_id",
    )

    montant = models.PositiveIntegerField("montant (XAF)", db_column="montant")
    frais = models.PositiveIntegerField("frais agregateur (XAF)", default=0, db_column="frais")
    montant_net = models.PositiveIntegerField("montant net (XAF)", default=0, db_column="montant_net")
    devise = models.CharField("devise", max_length=3, default="XAF", db_column="devise")

    operateur = models.CharField("operateur", max_length=20, db_column="operateur")
    telephone = models.CharField("telephone payeur", max_length=20, db_column="telephone")

    statut = models.CharField(
        "statut", max_length=12, choices=Statut.choices,
        default=Statut.EN_ATTENTE, db_column="statut",
    )
    idempotency_key = models.CharField("cle d'idempotence", max_length=64, unique=True, db_column="idempotency_key")
    reference_externe = models.CharField("reference agregateur", max_length=100, blank=True, db_column="reference_externe")
    transaction_id = models.CharField("transaction id agregateur", max_length=64, blank=True, db_column="transaction_id")
    reponse_brute = models.JSONField("derniere reponse API", default=dict, blank=True, db_column="reponse_brute")

    date_creation = models.DateTimeField("cree le", auto_now_add=True, db_column="date_creation")
    date_modification = models.DateTimeField("modifie le", auto_now=True, db_column="date_modification")
    date_confirmation = models.DateTimeField("confirme le", null=True, blank=True, db_column="date_confirmation")

    class Meta:
        db_table = "paiement"
        verbose_name = "paiement"
        verbose_name_plural = "paiements"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.reference_externe or self.idempotency_key[:8]} ({self.get_statut_display()})"

    @property
    def objet(self):
        return self.commande or self.abonnement

    @property
    def reussi(self):
        return self.statut == self.Statut.REUSSI
