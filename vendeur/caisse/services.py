from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from admin.commandes.models import Commande
from admin.produits.models import MouvementStock

PERIODES_JOURS = {"7j": 7, "30j": 30, "90j": 90}
LIBELLES_PERIODE = {
    "7j": "7 derniers jours",
    "30j": "30 derniers jours",
    "90j": "90 derniers jours",
    "tout": "Depuis le debut",
}


def borne_debut(periode):
    jours = PERIODES_JOURS.get(periode)
    if jours is None:
        return None
    return timezone.now() - timedelta(days=jours)


def construire_rapport(boutique, periode="30j"):
    """Chiffres cles (argent, commandes) et historique des mouvements de
    stock (ventes, reapprovisionnements) d'une boutique sur une periode."""
    debut = borne_debut(periode)

    commandes = boutique.commandes.all()
    if debut:
        commandes = commandes.filter(date_creation__gte=debut)
    livrees = commandes.filter(statut=Commande.Statut.LIVREE)
    ca_livre = livrees.aggregate(s=Sum("total"))["s"] or 0

    mouvements = MouvementStock.objects.filter(produit__boutique=boutique)
    if debut:
        mouvements = mouvements.filter(date_creation__gte=debut)
    mouvements = mouvements.select_related("produit", "variante", "auteur").order_by("-date_creation")

    ventes = [m for m in mouvements if m.type_mouvement == MouvementStock.Type.VENTE]
    restocks = [m for m in mouvements if m.type_mouvement == MouvementStock.Type.RESTOCK]

    return {
        "debut": debut,
        "ca_livre": ca_livre,
        "nb_commandes": commandes.count(),
        "nb_commandes_livrees": livrees.count(),
        "qte_vendue": sum(m.quantite for m in ventes),
        "qte_reappro": sum(m.quantite for m in restocks),
        "mouvements": list(mouvements),
    }
