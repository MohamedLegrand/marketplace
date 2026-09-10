from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from client.comptes.models import AdresseLivraison

User = get_user_model()


class InscriptionClientForm(forms.ModelForm):
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
        user.role = User.Role.ACHETEUR
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfilClientForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "telephone")
        labels = {"first_name": "Prenom", "last_name": "Nom", "telephone": "Telephone"}


class AdresseForm(forms.ModelForm):
    class Meta:
        model = AdresseLivraison
        fields = (
            "libelle",
            "nom_destinataire",
            "telephone",
            "ville",
            "quartier",
            "details",
            "par_defaut",
        )
