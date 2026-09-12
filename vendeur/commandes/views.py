from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from admin.commandes.models import Commande
from vendeur.comptes.decorators import acces_boutique_required

S = Commande.Statut

# Transitions autorisees pour le vendeur : statut courant -> statuts possibles.
TRANSITIONS_VENDEUR = {
    S.CONFIRMEE: [S.EN_PREPARATION, S.ANNULEE],
    S.EN_PREPARATION: [S.EXPEDIEE, S.ANNULEE],
    S.EXPEDIEE: [S.LIVREE],
}


def _permissions(request):
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
    commandes = boutique.commandes.select_related("client").prefetch_related("lignes")
    statut = request.GET.get("statut", "")
    if statut:
        commandes = commandes.filter(statut=statut)
    return render(request, "vendeur/commandes/liste.html", {
        "boutique": boutique,
        "commandes": commandes,
        "statut": statut,
        "statuts": Commande.Statut.choices,
        "permissions": _permissions(request),
    })


@acces_boutique_required()
def detail(request, boutique_pk, commande_pk):
    boutique = request.boutique
    commande = get_object_or_404(
        boutique.commandes.prefetch_related("lignes", "suivis"), pk=commande_pk
    )
    permissions = _permissions(request)
    return render(request, "vendeur/commandes/detail.html", {
        "boutique": boutique,
        "commande": commande,
        "transitions": TRANSITIONS_VENDEUR.get(commande.statut, []) if permissions["commandes"] else [],
        "permissions": permissions,
    })


@acces_boutique_required("commandes")
def changer_statut(request, boutique_pk, commande_pk):
    boutique = request.boutique
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
