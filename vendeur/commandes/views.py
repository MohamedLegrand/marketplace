from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from admin.boutiques.models import Boutique
from admin.commandes.models import Commande
from vendeur.comptes.decorators import onboarding_complete_required

S = Commande.Statut

# Transitions autorisees pour le vendeur : statut courant -> statuts possibles.
TRANSITIONS_VENDEUR = {
    S.CONFIRMEE: [S.EN_PREPARATION, S.ANNULEE],
    S.EN_PREPARATION: [S.EXPEDIEE, S.ANNULEE],
    S.EXPEDIEE: [S.LIVREE],
}


def _boutique(request, boutique_pk):
    return get_object_or_404(Boutique, pk=boutique_pk, proprietaire=request.user)


@onboarding_complete_required
def liste(request, boutique_pk):
    boutique = _boutique(request, boutique_pk)
    commandes = boutique.commandes.select_related("client").prefetch_related("lignes")
    statut = request.GET.get("statut", "")
    if statut:
        commandes = commandes.filter(statut=statut)
    return render(request, "vendeur/commandes/liste.html", {
        "boutique": boutique,
        "commandes": commandes,
        "statut": statut,
        "statuts": Commande.Statut.choices,
    })


@onboarding_complete_required
def detail(request, boutique_pk, commande_pk):
    boutique = _boutique(request, boutique_pk)
    commande = get_object_or_404(
        boutique.commandes.prefetch_related("lignes", "suivis"), pk=commande_pk
    )
    return render(request, "vendeur/commandes/detail.html", {
        "boutique": boutique,
        "commande": commande,
        "transitions": TRANSITIONS_VENDEUR.get(commande.statut, []),
    })


@onboarding_complete_required
def changer_statut(request, boutique_pk, commande_pk):
    boutique = _boutique(request, boutique_pk)
    commande = get_object_or_404(boutique.commandes, pk=commande_pk)
    if request.method == "POST":
        nouveau = request.POST.get("statut")
        commentaire = request.POST.get("commentaire", "").strip()
        if nouveau not in TRANSITIONS_VENDEUR.get(commande.statut, []):
            messages.error(request, "Changement de statut non autorise.")
        elif nouveau == S.ANNULEE:
            commande.annuler(request.user, commentaire or "Annulee par la boutique")
            messages.success(request, "Commande annulee, stock retabli.")
        else:
            commande.changer_statut(request.user, nouveau, commentaire)
            messages.success(request, "Statut mis a jour.")
    return redirect("commandes_vendeur:detail", boutique_pk=boutique.pk, commande_pk=commande.pk)
