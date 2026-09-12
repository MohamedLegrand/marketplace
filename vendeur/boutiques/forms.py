from django import forms

from admin.boutiques.models import Boutique, ZoneLivraison
from admin.categories.models import Categorie


class BoutiqueForm(forms.ModelForm):
    """Categorie geree "a la main" (hors ModelForm) pour proposer un choix
    "Autres" ou le vendeur precise lui-meme sa categorie : elle est alors
    creee automatiquement et rejoint la liste proposee aux futurs vendeurs."""

    AUTRE = "autre"

    categorie_choix = forms.ChoiceField(
        label="Categorie",
        choices=(),
        required=True,
    )
    autre_categorie = forms.CharField(
        label="Precisez votre categorie",
        max_length=100,
        required=False,
    )

    class Meta:
        model = Boutique
        fields = (
            "nom",
            "logo",
            "description",
            "telephone",
            "email",
            "adresse",
            "ville",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = Categorie.objects.filter(type=Categorie.Type.BOUTIQUE, actif=True)
        choix = [(str(c.pk), c.nom) for c in categories]
        choix.append((self.AUTRE, "Autres…"))
        self.fields["categorie_choix"].choices = choix
        if self.instance and self.instance.pk and self.instance.categorie_id:
            self.fields["categorie_choix"].initial = str(self.instance.categorie_id)
        self.order_fields([
            "nom", "logo", "description", "categorie_choix", "autre_categorie",
            "telephone", "email", "adresse", "ville",
        ])

    def clean(self):
        donnees = super().clean()
        choix = donnees.get("categorie_choix")
        autre = (donnees.get("autre_categorie") or "").strip()
        if choix == self.AUTRE and not autre:
            self.add_error("autre_categorie", "Precisez le nom de votre categorie.")
        return donnees

    def save(self, commit=True):
        boutique = super().save(commit=False)
        choix = self.cleaned_data.get("categorie_choix")
        if choix == self.AUTRE:
            nom = self.cleaned_data["autre_categorie"].strip()
            categorie, _ = Categorie.objects.get_or_create(
                type=Categorie.Type.BOUTIQUE,
                nom=nom,
                defaults={"actif": True},
            )
        else:
            categorie = Categorie.objects.filter(
                pk=choix, type=Categorie.Type.BOUTIQUE
            ).first()
        boutique.categorie = categorie
        if commit:
            boutique.save()
        return boutique


class ZoneLivraisonForm(forms.ModelForm):
    class Meta:
        model = ZoneLivraison
        fields = ("nom", "tarif", "delai_estime", "actif")
