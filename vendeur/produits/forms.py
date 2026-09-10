from django import forms

from admin.categories.models import Categorie
from admin.produits.models import PhotoProduit, Produit, VarianteProduit


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ("nom", "description", "categorie", "prix", "stock", "actif")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        help_texts = {"stock": "Ignore si le produit a des variantes."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].queryset = Categorie.objects.filter(
            type=Categorie.Type.PRODUIT, actif=True
        )


class PhotoProduitForm(forms.ModelForm):
    class Meta:
        model = PhotoProduit
        fields = ("image", "principale")


class VarianteProduitForm(forms.ModelForm):
    """Formulaire complet (page d'edition d'une variante)."""

    class Meta:
        model = VarianteProduit
        fields = ("libelle", "prix", "stock", "actif")


class VarianteAjoutForm(forms.ModelForm):
    """Ajout rapide depuis la fiche produit : la variante est active par defaut
    (modele : actif=True)."""

    class Meta:
        model = VarianteProduit
        fields = ("libelle", "prix", "stock")
