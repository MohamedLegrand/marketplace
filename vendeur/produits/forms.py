from django import forms

from admin.categories.models import Categorie
from admin.produits.models import PhotoProduit, Produit, VarianteProduit


class ProduitForm(forms.ModelForm):
    """Categorie geree "a la main" (hors ModelForm) pour proposer un choix
    "Autres" ou le vendeur precise lui-meme sa categorie : elle est alors
    creee automatiquement et rejoint la liste proposee pour les futurs
    produits (meme principe que pour la creation de boutique)."""

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
        model = Produit
        fields = ("nom", "description", "prix", "stock", "actif")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        help_texts = {"stock": "Ignore si le produit a des variantes."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = Categorie.objects.filter(type=Categorie.Type.PRODUIT, actif=True)
        choix = [(str(c.pk), c.nom) for c in categories]
        choix.append((self.AUTRE, "Autres…"))
        self.fields["categorie_choix"].choices = choix
        if self.instance and self.instance.pk and self.instance.categorie_id:
            self.fields["categorie_choix"].initial = str(self.instance.categorie_id)
        self.order_fields([
            "nom", "description", "categorie_choix", "autre_categorie",
            "prix", "stock", "actif",
        ])

    def clean(self):
        donnees = super().clean()
        choix = donnees.get("categorie_choix")
        autre = (donnees.get("autre_categorie") or "").strip()
        if choix == self.AUTRE and not autre:
            self.add_error("autre_categorie", "Precisez le nom de votre categorie.")
        return donnees

    def save(self, commit=True):
        produit = super().save(commit=False)
        choix = self.cleaned_data.get("categorie_choix")
        if choix == self.AUTRE:
            nom = self.cleaned_data["autre_categorie"].strip()
            categorie, _ = Categorie.objects.get_or_create(
                type=Categorie.Type.PRODUIT, nom=nom, defaults={"actif": True},
            )
        else:
            categorie = Categorie.objects.filter(pk=choix, type=Categorie.Type.PRODUIT).first()
        produit.categorie = categorie
        if commit:
            produit.save()
        return produit


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


class AjoutStockForm(forms.Form):
    """Reapprovisionnement : ajoute une quantite au stock du produit (ou
    d'une de ses variantes) et laisse une trace dans l'historique des
    mouvements de stock."""

    variante = forms.ModelChoiceField(queryset=VarianteProduit.objects.none(), required=False)
    quantite = forms.IntegerField(label="Quantite a ajouter", min_value=1)
    note = forms.CharField(label="Note (optionnel)", max_length=200, required=False)

    def __init__(self, *args, produit=None, **kwargs):
        super().__init__(*args, **kwargs)
        if produit is not None:
            self.fields["variante"].queryset = produit.variantes.all()
