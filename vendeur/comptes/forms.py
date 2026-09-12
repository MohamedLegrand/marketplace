from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from admin.kyc.models import DossierKYC

User = get_user_model()


class InscriptionVendeurForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "telephone")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte existe deja avec cette adresse e-mail.")
        return email

    def clean(self):
        donnees = super().clean()
        p1, p2 = donnees.get("password1"), donnees.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les deux mots de passe ne correspondent pas.")
        if p1:
            validate_password(p1)
        return donnees

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.VENDEUR
        user.username = User.generer_username(user.email)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfilVendeurForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "telephone")
        labels = {
            "first_name": "Prenom",
            "last_name": "Nom",
            "telephone": "Numero de telephone",
        }

    def clean_telephone(self):
        tel = (self.cleaned_data.get("telephone") or "").strip()
        if not tel:
            raise forms.ValidationError("Le numero de telephone est obligatoire.")
        qs = User.objects.filter(telephone=tel).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ce numero est deja utilise par un autre compte.")
        return tel


class DossierKYCForm(forms.ModelForm):
    class Meta:
        model = DossierKYC
        fields = (
            "nom_complet",
            "date_naissance",
            "type_piece",
            "numero_piece",
            "piece_recto",
            "piece_verso",
            "selfie",
            "raison_sociale",
            "registre_commerce",
        )
        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"}),
        }
        help_texts = {
            "piece_verso": "Facultatif pour un passeport.",
            "selfie": "Photo de vous tenant votre piece, visage et piece lisibles.",
            "raison_sociale": "A renseigner si vous vendez au nom d'une entreprise.",
            "registre_commerce": "RCCM - uniquement pour les entreprises.",
        }
