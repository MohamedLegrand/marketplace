"""Construit un resume texte des donnees reelles d'une boutique (catalogue,
ventes, avis) pour ancrer les reponses de l'assistant IA sur des chiffres
concrets plutot que des generalites.
"""
from django.db.models import F, Sum

PROMPT_SYSTEME = """Tu es l'assistant IA d'analyse des ventes de Jennifer Website, \
integre a l'espace vendeur. Tu aides {vendeur} a comprendre les performances \
de sa boutique « {boutique} » et tu proposes des recommandations concretes et \
actionnables pour vendre davantage (mise en avant de produits, gestion du \
stock, tarification, promotions, zones de livraison, service client...).

Regles :
- Reponds toujours en francais, de facon claire et concise.
- Appuie-toi sur les donnees ci-dessous ; si une question depasse ces \
donnees, dis-le simplement au lieu d'inventer des chiffres.
- Structure les reponses un peu longues avec des listes a puces.
- Reste bienveillant et pragmatique, adapte au contexte camerounais \
(Mobile Money, livraison locale).
- Format de sortie : texte brut uniquement, affiche tel quel dans une bulle \
de discussion (pas de rendu Markdown). N'utilise donc ni **, ni #, ni tableaux ; \
pour une liste, utilise simplement un tiret en debut de ligne.

Donnees actuelles de la boutique :
{donnees}
"""


def construire_contexte(boutique) -> str:
    from admin.commandes.models import Commande, LigneCommande
    from admin.produits.models import Produit

    produits = Produit.objects.filter(boutique=boutique)
    nb_produits = produits.count()
    nb_actifs = produits.filter(actif=True).count()
    en_rupture = [p.nom for p in produits if p.stock_total == 0]

    commandes = Commande.objects.filter(boutique=boutique)
    nb_commandes = commandes.count()
    ca_livre = (
        commandes.filter(statut=Commande.Statut.LIVREE).aggregate(s=Sum("total"))["s"]
        or 0
    )
    par_statut = {}
    for statut, libelle in Commande.Statut.choices:
        n = commandes.filter(statut=statut).count()
        if n:
            par_statut[libelle] = n

    top = (
        LigneCommande.objects.filter(commande__boutique=boutique)
        .exclude(commande__statut=Commande.Statut.ANNULEE)
        .values("designation")
        .annotate(qte=Sum("quantite"), revenu=Sum(F("quantite") * F("prix_unitaire")))
        .order_by("-qte")[:5]
    )

    lignes = [
        f"- Boutique : {boutique.nom} ({boutique.ville or 'ville non renseignee'}), "
        f"categorie : {boutique.categorie or 'non definie'}, statut : {boutique.get_statut_display()}.",
        f"- Note moyenne : {boutique.note_moyenne}/5 sur {boutique.nombre_avis} avis.",
        f"- Catalogue : {nb_produits} produit(s), dont {nb_actifs} en vente actuellement.",
    ]
    if en_rupture:
        aperçu = ", ".join(en_rupture[:10])
        suite = f" (+{len(en_rupture) - 10} autre(s))" if len(en_rupture) > 10 else ""
        lignes.append(f"- Produits en rupture de stock : {aperçu}{suite}.")
    else:
        lignes.append("- Aucun produit en rupture de stock actuellement.")

    lignes.append(
        f"- Commandes : {nb_commandes} au total, chiffre d'affaires livre : {ca_livre} XAF."
    )
    if par_statut:
        detail = ", ".join(f"{libelle} : {n}" for libelle, n in par_statut.items())
        lignes.append(f"- Repartition des commandes par statut : {detail}.")
    if top:
        detail_top = "; ".join(
            f"{t['designation']} (x{t['qte']}, {t['revenu']} XAF de revenu)" for t in top
        )
        lignes.append(f"- Produits les plus vendus (par quantite) : {detail_top}.")
    else:
        lignes.append("- Aucune vente enregistree pour le moment.")

    return "\n".join(lignes)


def prompt_systeme(boutique) -> str:
    return PROMPT_SYSTEME.format(
        vendeur=boutique.proprietaire.get_full_name() or boutique.proprietaire.email,
        boutique=boutique.nom,
        donnees=construire_contexte(boutique),
    )
