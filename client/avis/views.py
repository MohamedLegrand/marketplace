from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from admin.avis.models import Avis
from admin.avis.services import (
    commande_livree_pour_boutique,
    commande_livree_pour_produit,
)
from admin.boutiques.models import Boutique
from admin.produits.models import Produit
from client.comptes.decorators import client_required

from .forms import AvisForm


@client_required
def mes_avis(request):
    return render(request, "client/avis/mes_avis.html", {
        "avis": request.user.avis.select_related("produit", "boutique"),
    })


def _noter(request, *, produit=None, boutique=None, retour):
    cible = produit or boutique
    if produit is not None:
        commande = commande_livree_pour_produit(request.user, produit)
    else:
        commande = commande_livree_pour_boutique(request.user, boutique)
    if commande is None:
        messages.error(request, "Vous ne pouvez noter qu'apres reception d'une commande livree.")
        return redirect(retour)

    avis = Avis.objects.filter(
        auteur=request.user, produit=produit, boutique=boutique
    ).first()
    existant = avis is not None
    if avis is None:
        avis = Avis(
            auteur=request.user, produit=produit, boutique=boutique, commande=commande
        )
    form = AvisForm(request.POST or None, instance=avis)
    if request.method == "POST" and form.is_valid():
        avis = form.save(commit=False)
        avis.commande = commande
        avis.statut = Avis.Statut.PUBLIE
        avis.save()
        messages.success(request, "Merci, votre avis est publie.")
        return redirect(retour)

    return render(request, "client/avis/form.html", {
        "form": form, "cible": cible, "type": "produit" if produit else "boutique",
        "modification": existant,
    })


@client_required
def noter_produit(request, produit_pk):
    produit = get_object_or_404(Produit, pk=produit_pk)
    retour = f"/b/{produit.boutique.slug}/{produit.slug}/"
    return _noter(request, produit=produit, retour=retour)


@client_required
def noter_boutique(request, boutique_pk):
    boutique = get_object_or_404(Boutique, pk=boutique_pk)
    return _noter(request, boutique=boutique, retour=f"/b/{boutique.slug}/")


@client_required
def supprimer(request, pk):
    avis = get_object_or_404(Avis, pk=pk, auteur=request.user)
    if request.method == "POST":
        avis.delete()
        messages.success(request, "Avis supprime.")
    return redirect("avis_client:mes_avis")
