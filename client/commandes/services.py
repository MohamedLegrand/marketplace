from django.db import transaction

from admin.boutiques.models import Boutique
from admin.commandes.models import Commande, LigneCommande, SuiviCommande
from admin.produits.models import MouvementStock, Produit, VarianteProduit


class StockInsuffisant(Exception):
    pass


@transaction.atomic
def creer_commande(client, panier, adresse, zone):
    """Cree une commande a partir du panier : verrouille les stocks, les
    decremente, fige produits + adresse, puis vide le panier."""
    lignes_panier = panier.lignes()
    if not lignes_panier:
        raise ValueError("Panier vide.")

    boutique = Boutique.objects.select_for_update().get(pk=panier.boutique_id)

    commande = Commande(
        client=client,
        boutique=boutique,
        adresse_nom=adresse.nom_destinataire,
        adresse_telephone=adresse.telephone,
        adresse_ville=adresse.ville,
        adresse_quartier=adresse.quartier,
        adresse_details=adresse.details,
        zone_nom=zone.nom if zone else "",
        frais_livraison=zone.tarif if zone else 0,
    )
    commande.save()

    sous_total = 0
    for lp in lignes_panier:
        produit = Produit.objects.select_for_update().get(pk=lp["produit"].pk)
        variante = None
        if lp["variante"]:
            variante = VarianteProduit.objects.select_for_update().get(pk=lp["variante"].pk)
        quantite = lp["quantite"]
        stock = variante.stock if variante else produit.stock
        if quantite > stock:
            raise StockInsuffisant(
                f"Stock insuffisant pour « {produit.nom} » (reste {stock})."
            )
        if variante:
            variante.stock -= quantite
            variante.save(update_fields=["stock", "date_modification"])
        else:
            produit.stock -= quantite
            produit.save(update_fields=["stock", "date_modification"])

        prix = variante.prix_effectif if variante else produit.prix
        designation = produit.nom + (f" - {variante.libelle}" if variante else "")
        LigneCommande.objects.create(
            commande=commande,
            produit=produit,
            variante=variante,
            designation=designation,
            prix_unitaire=prix,
            quantite=quantite,
        )
        MouvementStock.objects.create(
            produit=produit,
            variante=variante,
            type_mouvement=MouvementStock.Type.VENTE,
            quantite=quantite,
            montant=prix * quantite,
            commande=commande,
        )
        sous_total += prix * quantite

    commande.sous_total = sous_total
    commande.total = sous_total + commande.frais_livraison
    commande.save(update_fields=["sous_total", "total", "date_modification"])

    SuiviCommande.objects.create(
        commande=commande, auteur=client, ancien_statut="",
        nouveau_statut=commande.statut, commentaire="Commande creee",
    )
    panier.vider()
    return commande
