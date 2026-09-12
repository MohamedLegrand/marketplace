from django import forms

from admin.boutiques.models import RoleBoutique

_PERMISSIONS = (
    "peut_gerer_produits",
    "peut_gerer_stock",
    "peut_gerer_commandes",
    "peut_voir_statistiques",
)


class AjoutMembreForm(forms.Form):
    email = forms.EmailField(label="E-mail du membre")
    type_role = forms.ChoiceField(label="Type de role", choices=RoleBoutique.TypeRole.choices)
    libelle = forms.CharField(label="Libelle (ex. : Vendeur 1)", max_length=50, required=False)
    peut_gerer_produits = forms.BooleanField(
        label="Gerer les produits (creer, modifier, mettre en/hors vente)", required=False
    )
    peut_gerer_stock = forms.BooleanField(
        label="Gerer le stock (reapprovisionnement)", required=False
    )
    peut_gerer_commandes = forms.BooleanField(
        label="Gerer les commandes (changer le statut)", required=False, initial=True
    )
    peut_voir_statistiques = forms.BooleanField(
        label="Voir la caisse, les statistiques et generer les rapports PDF", required=False
    )

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def permissions(self):
        return {champ: self.cleaned_data[champ] for champ in _PERMISSIONS}


class RoleForm(forms.ModelForm):
    class Meta:
        model = RoleBoutique
        fields = ("type_role", "libelle", *_PERMISSIONS, "actif")
