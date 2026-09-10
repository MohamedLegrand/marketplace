from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from admin.boutiques.models import Boutique
from admin.produits.models import PhotoProduit, Produit, VarianteProduit
from vendeur.comptes.decorators import onboarding_complete_required

from .forms import (
    PhotoProduitForm,
    ProduitForm,
    VarianteAjoutForm,
    VarianteProduitForm,
)


def _boutique(request, boutique_pk):
    return get_object_or_404(Boutique, pk=boutique_pk, proprietaire=request.user)


def _produit(request, boutique_pk, produit_pk):
    boutique = _boutique(request, boutique_pk)
    produit = get_object_or_404(Produit, pk=produit_pk, boutique=boutique)
    return boutique, produit


@onboarding_complete_required
def liste(request, boutique_pk):
    boutique = _boutique(request, boutique_pk)
    return render(request, "vendeur/produits/liste.html", {
        "boutique": boutique,
        "produits": boutique.produits.all(),
    })


@onboarding_complete_required
def creer(request, boutique_pk):
    boutique = _boutique(request, boutique_pk)
    form = ProduitForm(request.POST or None, instance=Produit(boutique=boutique))
    if request.method == "POST" and form.is_valid():
        produit = form.save()
        messages.success(request, "Produit cree. Ajoutez des photos et, au besoin, des variantes.")
        return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)
    return render(request, "vendeur/produits/form.html", {
        "form": form, "boutique": boutique, "mode": "creer",
    })


@onboarding_complete_required
def modifier(request, boutique_pk, produit_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
    form = ProduitForm(request.POST or None, instance=produit)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Produit mis a jour.")
        return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)
    return render(request, "vendeur/produits/form.html", {
        "form": form, "boutique": boutique, "produit": produit, "mode": "modifier",
    })


@onboarding_complete_required
def detail(request, boutique_pk, produit_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
    return render(request, "vendeur/produits/detail.html", {
        "boutique": boutique,
        "produit": produit,
        "photos": produit.photos.all(),
        "variantes": produit.variantes.all(),
        "photo_form": PhotoProduitForm(),
        "variante_form": VarianteAjoutForm(),
    })


@onboarding_complete_required
def basculer_actif(request, boutique_pk, produit_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
    if request.method == "POST":
        produit.actif = not produit.actif
        produit.save(update_fields=["actif", "date_modification"])
        messages.success(request, "Produit " + ("mis en vente." if produit.actif else "retire de la vente."))
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


@onboarding_complete_required
def supprimer(request, boutique_pk, produit_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
    if request.method == "POST":
        produit.delete()
        messages.success(request, "Produit supprime.")
        return redirect("produits_vendeur:liste", boutique_pk=boutique.pk)
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


# --- Photos ---------------------------------------------------------------
@onboarding_complete_required
def photo_ajouter(request, boutique_pk, produit_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
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


@onboarding_complete_required
def photo_principale(request, boutique_pk, produit_pk, photo_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
    photo = get_object_or_404(PhotoProduit, pk=photo_pk, produit=produit)
    if request.method == "POST":
        photo.principale = True
        photo.save()
        messages.success(request, "Photo principale definie.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


@onboarding_complete_required
def photo_supprimer(request, boutique_pk, produit_pk, photo_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
    photo = get_object_or_404(PhotoProduit, pk=photo_pk, produit=produit)
    if request.method == "POST":
        photo.delete()
        messages.success(request, "Photo supprimee.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)


# --- Variantes ----------------------------------------------------------
@onboarding_complete_required
def variante_ajouter(request, boutique_pk, produit_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
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


@onboarding_complete_required
def variante_modifier(request, boutique_pk, produit_pk, variante_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
    variante = get_object_or_404(VarianteProduit, pk=variante_pk, produit=produit)
    form = VarianteProduitForm(request.POST or None, instance=variante)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Variante mise a jour.")
        return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)
    return render(request, "vendeur/produits/variante_form.html", {
        "form": form, "boutique": boutique, "produit": produit, "variante": variante,
    })


@onboarding_complete_required
def variante_supprimer(request, boutique_pk, produit_pk, variante_pk):
    boutique, produit = _produit(request, boutique_pk, produit_pk)
    variante = get_object_or_404(VarianteProduit, pk=variante_pk, produit=produit)
    if request.method == "POST":
        variante.delete()
        messages.success(request, "Variante supprimee.")
    return redirect("produits_vendeur:detail", boutique_pk=boutique.pk, produit_pk=produit.pk)
