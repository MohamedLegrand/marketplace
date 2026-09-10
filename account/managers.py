from django.contrib.auth.models import UserManager as BaseUserManager


class UserManager(BaseUserManager):
    """Manager permettant la connexion par e-mail (USERNAME_FIELD = "email")."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email)
        # A defaut de username fourni, on derive un identifiant unique depuis l'e-mail.
        if "username" not in extra_fields:
            base = (email.split("@")[0] or "user")[:140]
            username, suffixe = base, 1
            while self.model.objects.filter(username=username).exists():
                suffixe += 1
                username = f"{base}{suffixe}"
            extra_fields["username"] = username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", self.model.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superutilisateur doit avoir is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
