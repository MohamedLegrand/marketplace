from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from admin.produits.models import MouvementStock, PhotoProduit, Produit, VarianteProduit
from vendeur.comptes.decorators import acces_boutique_required

from .forms import (
    AjoutStockForm,
    PhotoProduitForm,
    ProduitForm,
    VarianteAjoutForm,
    VarianteProduitForm,
)


def _produit(request, produit_pk):
    return get_object_or_404(Produit, pk=produit_pk, boutique=request.boutique)


def _permissions(request):
    """Permissions de l'utilisateur courant sur la boutique de la requete
    (tout est autorise au proprietaire)."""
    role = request.role_boutique
    if role is None:
        return {"produits": True, "stock": True, "commandes": True, "statistiques": True}
    return {
        "produits": role.peut_gerer_produits,
        "stock": role.peut_gerer_stock,
        "commandes": role.peut_gerer_commandes,
        "statistiques": role.peut_voir_statistiques,
    }


@acces_boutique_required()
def liste(request, boutique_pk):
    boutique = request.boutique
    return render(request, "vendeur/produits/liste.html", {
        "boutique": boutique,
        "produits": boutique.produits.all(),
        "permissions": _permissions(request),
    })


@acces_boutique_required("produits")
def creer(request, boutique_pk):
    boutique = request.boutique
    form = ProduitForm(request.POST or None, instance=Produit(boutique=boutique))
    if request.method == "POST" and form.is_valid():
        produit = form.save()
        messages.success(request, "Produit cree. Ajoutez des photos et, au besoin, des variantes.")
        return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)
    return render(request, "vendeur/produits/form.html", {
        "form": form, "boutique": boutique, "mode": "creer",
    })


@acces_boutique_required("produits")
def modifier(request, boutique_pk, produit_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    form = ProduitForm(request.POST or None, instance=produit)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Produit mis a jour.")
        return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)
    return render(request, "vendeur/produits/form.html", {
        "form": form, "boutique": boutique, "produit": produit, "mode": "modifier",
    })


@acces_boutique_required()
def detail(request, boutique_pk, produit_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    permissions = _permissions(request)
    return render(request, "vendeur/produits/detail.html", {
        "boutique": boutique,
        "produit": produit,
        "photos": produit.photos.all(),
        "variantes": produit.variantes.all(),
        "photo_form": PhotoProduitForm(),
        "variante_form": VarianteAjoutForm(),
        "stock_form": AjoutStockForm(),
        "permissions": permissions,
        "mouvements": produit.mouvements_stock.select_related("variante", "auteur")[:15],
    })


@acces_boutique_required("produits")
def basculer_actif(request, boutique_pk, produit_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    if request.method == "POST":
        produit.actif = not produit.actif
        produit.save(update_fields=["actif", "date_modification"])
        messages.success(request, "Produit " + ("mis en vente." if produit.actif else "retire de la vente."))
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


@acces_boutique_required("produits")
def supprimer(request, boutique_pk, produit_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    if request.method == "POST":
        produit.delete()
        messages.success(request, "Produit supprime.")
        return redirect("produits_vendeur:liste", boutique_pk=boutique.pk)
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


# --- Stock ------------------------------------------------------------------
@acces_boutique_required("stock")
def stock_ajouter(request, boutique_pk, produit_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    if request.method == "POST":
        form = AjoutStockForm(request.POST, produit=produit)
        if form.is_valid():
            quantite = form.cleaned_data["quantite"]
            variante = form.cleaned_data["variante"]
            note = form.cleaned_data["note"]
            if variante:
                variante.stock += quantite
                variante.save(update_fields=["stock", "date_modification"])
            else:
                produit.stock += quantite
                produit.save(update_fields=["stock", "date_modification"])
            MouvementStock.objects.create(
                produit=produit,
                variante=variante,
                type_mouvement=MouvementStock.Type.RESTOCK,
                quantite=quantite,
                auteur=request.user,
                note=note,
            )
            messages.success(request, f"Stock mis a jour (+{quantite}).")
        else:
            messages.error(request, "Formulaire de reapprovisionnement invalide.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


# --- Photos ---------------------------------------------------------------
@acces_boutique_required("produits")
def photo_ajouter(request, boutique_pk, produit_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    if request.method == "POST":
        form = PhotoProduitForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.produit = produit
            photo.save()
            messages.success(request, "Photo ajoutee.")
        else:
            messages.error(request, "Fichier image invalide.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


@acces_boutique_required("produits")
def photo_principale(request, boutique_pk, produit_pk, photo_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    photo = get_object_or_404(PhotoProduit, pk=photo_pk, produit=produit)
    if request.method == "POST":
        photo.principale = True
        photo.save()
        messages.success(request, "Photo principale definie.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


@acces_boutique_required("produits")
def photo_supprimer(request, boutique_pk, produit_pk, photo_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    photo = get_object_or_404(PhotoProduit, pk=photo_pk, produit=produit)
    if request.method == "POST":
        photo.delete()
        messages.success(request, "Photo supprimee.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


# --- Variantes ----------------------------------------------------------
@acces_boutique_required("produits")
def variante_ajouter(request, boutique_pk, produit_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    if request.method == "POST":
        form = VarianteAjoutForm(request.POST)
        if form.is_valid():
            variante = form.save(commit=False)
            variante.produit = produit
            try:
                variante.validate_constraints()
                variante.save()
                messages.success(request, "Variante ajoutee.")
            except ValidationError:
                messages.error(request, "Une variante porte deja ce libelle.")
        else:
            messages.error(request, "Formulaire de variante invalide.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


@acces_boutique_required("produits")
def variante_modifier(request, boutique_pk, produit_pk, variante_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    variante = get_object_or_404(VarianteProduit, pk=variante_pk, produit=produit)
    form = VarianteProduitForm(request.POST or None, instance=variante)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Variante mise a jour.")
        return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)
    return render(request, "vendeur/produits/variante_form.html", {
        "form": form, "boutique": boutique, "produit": produit, "variante": variante,
    })


@acces_boutique_required("produits")
def variante_supprimer(request, boutique_pk, produit_pk, variante_pk):
    boutique = request.boutique
    produit = _produit(request, produit_pk)
    variante = get_object_or_404(VarianteProduit, pk=variante_pk, produit=produit)
    if request.method == "POST":
        variante.delete()
        messages.success(request, "Variante supprimee.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)
