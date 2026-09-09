from django.contrib.auth.models import AbstractUser
from django.db import models

from account.managers import UserManager


class User(AbstractUser):
    """Utilisateur de la marketplace.

    Etend le modele Django standard (mot de passe hache, sessions, permissions)
    avec les besoins du cahier des charges :
    - connexion par adresse e-mail ;
    - numero de telephone (inscription par e-mail et/ou telephone) ;
    - un role qui conditionne les droits d'acces ;
    - desactivation / reactivation d'un compte (acheteur ou vendeur) par
      l'administrateur, via le champ standard Django ``is_active``.

    Table SQL : "utilisateur".
    """

    class Role(models.TextChoices):
        ACHETEUR = "acheteur", "Acheteur"
        VENDEUR = "vendeur", "Vendeur"
        ADMIN = "admin", "Administrateur"

    email = models.EmailField("adresse e-mail", unique=True)
    telephone = models.CharField(
        "numero de telephone",
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        db_column="telephone",
    )
    role = models.CharField(
        "role",
        max_length=10,
        choices=Role.choices,
        default=Role.ACHETEUR,
        db_column="role",
    )
    motif_desactivation = models.TextField(
        "motif de la desactivation", blank=True, db_column="motif_desactivation"
    )
    date_desactivation = models.DateTimeField(
        "desactive le", null=True, blank=True, db_column="date_desactivation"
    )
    date_creation = models.DateTimeField(
        "cree le", auto_now_add=True, db_column="date_creation"
    )
    date_modification = models.DateTimeField(
        "modifie le", auto_now=True, db_column="date_modification"
    )

    objects = UserManager()

    # Connexion par e-mail ; le username est genere automatiquement.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "utilisateur"
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ["-date_creation"]

    def __str__(self):
        return self.email or self.username

    @property
    def est_vendeur(self):
        return self.role == self.Role.VENDEUR

    @property
    def est_administrateur(self):
        return self.role == self.Role.ADMIN

    def desactiver(self, motif=""):
        """Desactive le compte : la connexion est immediatement refusee."""
        from django.utils import timezone

        self.is_active = False
        self.motif_desactivation = motif
        self.date_desactivation = timezone.now()
        self.save(update_fields=[
            "is_active", "motif_desactivation", "date_desactivation", "date_modification",
        ])

    def reactiver(self):
        """Reactive le compte et efface le motif de desactivation."""
        self.is_active = True
        self.motif_desactivation = ""
        self.date_desactivation = None
        self.save(update_fields=[
            "is_active", "motif_desactivation", "date_desactivation", "date_modification",
        ])
