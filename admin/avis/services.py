from django.db.models import Avg, Count

from admin.avis.models import Avis
from admin.boutiques.models import Boutique
from admin.commandes.models import Commande
from admin.produits.models import Produit


def recalculer_agregats(cible):
    """Recalcule note_moyenne / nombre_avis sur un Produit ou une Boutique
    a partir des avis publies."""
    if isinstance(cible, Produit):
        qs = Avis.objects.filter(produit=cible, statut=Avis.Statut.PUBLIE)
    elif isinstance(cible, Boutique):
        qs = Avis.objects.filter(boutique=cible, statut=Avis.Statut.PUBLIE)
    else:
        return
    stats = qs.aggregate(moyenne=Avg("note"), total=Count("id"))
    cible.note_moyenne = round(stats["moyenne"] or 0, 2)
    cible.nombre_avis = stats["total"]
    cible.save(update_fields=["note_moyenne", "nombre_avis", "date_modification"])


def commande_livree_pour_produit(user, produit):
    return (
        Commande.objects.filter(
            client=user, statut=Commande.Statut.LIVREE, lignes__produit=produit
        )
        .order_by("-date_creation")
        .first()
    )


def commande_livree_pour_boutique(user, boutique):
    return (
        Commande.objects.filter(
            client=user, statut=Commande.Statut.LIVREE, boutique=boutique
        )
        .order_by("-date_creation")
        .first()
    )
