from django import forms

from admin.boutiques.models import Boutique, ZoneLivraison
from admin.categories.models import Categorie


class BoutiqueForm(forms.ModelForm):
    class Meta:
        model = Boutique
        fields = (
            "nom",
            "logo",
            "description",
            "categorie",
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
        self.fields["categorie"].queryset = Categorie.objects.filter(
            type=Categorie.Type.BOUTIQUE, actif=True
        )
        self.fields["categorie"].required = True


class ZoneLivraisonForm(forms.ModelForm):
    class Meta:
        model = ZoneLivraison
        fields = ("nom", "tarif", "delai_estime", "actif")
