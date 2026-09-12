"""Construit un resume texte des donnees reelles de l'ENSEMBLE des boutiques
de la plateforme (contrairement a l'assistant vendeur, limite a une seule
boutique) pour ancrer les reponses de l'assistant IA d'analyse globale.
"""
from django.db.models import Count, F, Sum

PROMPT_SYSTEME = """Tu es l'assistant IA d'analyse globale de Jennifer Website, \
integre a l'espace administrateur. Tu aides {admin} a superviser \
l'ensemble de la plateforme : performance de toutes les boutiques, sante du \
catalogue, ventes, abonnements et categories. Tu proposes des \
recommandations concretes et actionnables pour l'equipe (boutiques a \
accompagner ou sanctionner, categories a developper, vendeurs a relancer \
vers un forfait superieur, tendances a surveiller...).

Regles :
- Reponds toujours en francais, de facon claire et concise.
- Appuie-toi sur les donnees ci-dessous ; si une question depasse ces \
donnees, dis-le simplement au lieu d'inventer des chiffres.
- Structure les reponses un peu longues avec des listes a puces.
- Reste pragmatique et oriente decision (que faire concretement, sur quelle \
boutique ou categorie agir en priorite).
- Format de sortie : texte brut uniquement, affiche tel quel dans une bulle \
de discussion (pas de rendu Markdown). N'utilise donc ni **, ni #, ni tableaux ; \
pour une liste, utilise simplement un tiret en debut de ligne.

Donnees actuelles de la plateforme (toutes boutiques confondues) :
{donnees}
"""


def construire_contexte() -> str:
    from admin.abonnements.models import Abonnement, Plan
    from admin.boutiques.models import Boutique
    from admin.categories.models import Categorie
    from admin.commandes.models import Commande, LigneCommande
    from admin.produits.models import Produit

    boutiques = Boutique.objects.all()
    nb_boutiques = boutiques.count()
    par_statut_boutique = {}
    for statut, libelle in Boutique.Statut.choices:
        n = boutiques.filter(statut=statut).count()
        if n:
            par_statut_boutique[libelle] = n

    nb_produits = Produit.objects.count()
    nb_produits_actifs = Produit.objects.filter(actif=True).count()

    commandes = Commande.objects.all()
    nb_commandes = commandes.count()
    ca_livre = (
        commandes.filter(statut=Commande.Statut.LIVREE).aggregate(s=Sum("total"))["s"] or 0
    )
    par_statut_commande = {}
    for statut, libelle in Commande.Statut.choices:
        n = commandes.filter(statut=statut).count()
        if n:
            par_statut_commande[libelle] = n

    top_boutiques = (
        Commande.objects.filter(statut=Commande.Statut.LIVREE)
        .values("boutique__nom")
        .annotate(ca=Sum("total"), nb=Count("id"))
        .order_by("-ca")[:5]
    )

    boutiques_sans_vente = (
        boutiques.filter(statut=Boutique.Statut.APPROUVEE, commandes__isnull=True).count()
    )

    top_produits = (
        LigneCommande.objects.exclude(commande__statut=Commande.Statut.ANNULEE)
        .values("designation")
        .annotate(qte=Sum("quantite"), revenu=Sum(F("quantite") * F("prix_unitaire")))
        .order_by("-qte")[:5]
    )

    categories = (
        Categorie.objects.filter(type=Categorie.Type.BOUTIQUE)
        .annotate(nb=Count("boutiques"))
        .filter(nb__gt=0)
        .order_by("-nb")[:8]
    )

    par_plan = {}
    for ab in Abonnement.objects.filter(statut=Abonnement.Statut.ACTIF).select_related("plan"):
        par_plan[ab.plan.nom] = par_plan.get(ab.plan.nom, 0) + 1
    nb_plans_ia = Plan.objects.filter(actif=True, ia_analyse_ventes=True).count()

    note_moyenne_globale = 0
    boutiques_notees = boutiques.exclude(nombre_avis=0)
    if boutiques_notees.exists():
        total_notes = sum(float(b.note_moyenne) * b.nombre_avis for b in boutiques_notees)
        total_avis = sum(b.nombre_avis for b in boutiques_notees)
        if total_avis:
            note_moyenne_globale = round(total_notes / total_avis, 2)

    lignes = [f"- Nombre total de boutiques : {nb_boutiques}."]
    if par_statut_boutique:
        detail = ", ".join(f"{libelle} : {n}" for libelle, n in par_statut_boutique.items())
        lignes.append(f"- Repartition des boutiques par statut : {detail}.")
    lignes.append(f"- Boutiques approuvees sans aucune commande a ce jour : {boutiques_sans_vente}.")
    lignes.append(
        f"- Catalogue global : {nb_produits} produit(s), dont {nb_produits_actifs} en vente actuellement."
    )
    lignes.append(
        f"- Commandes : {nb_commandes} au total, chiffre d'affaires livre cumule : {ca_livre} XAF."
    )
    if par_statut_commande:
        detail = ", ".join(f"{libelle} : {n}" for libelle, n in par_statut_commande.items())
        lignes.append(f"- Repartition des commandes par statut : {detail}.")
    if top_boutiques:
        detail = "; ".join(
            f"{t['boutique__nom']} ({t['ca']} XAF sur {t['nb']} commande(s))" for t in top_boutiques
        )
        lignes.append(f"- Top boutiques par chiffre d'affaires livre : {detail}.")
    else:
        lignes.append("- Aucune commande livree enregistree pour le moment.")
    if top_produits:
        detail = "; ".join(
            f"{t['designation']} (x{t['qte']}, {t['revenu']} XAF de revenu)" for t in top_produits
        )
        lignes.append(f"- Produits les plus vendus sur la plateforme (par quantite) : {detail}.")
    if categories:
        detail = ", ".join(f"{c.nom} ({c.nb} boutique(s))" for c in categories)
        lignes.append(f"- Categories de boutique les plus representees : {detail}.")
    if par_plan:
        detail = ", ".join(f"{nom} : {n}" for nom, n in par_plan.items())
        lignes.append(f"- Abonnements actifs par forfait : {detail}.")
    lignes.append(f"- Nombre de forfaits actifs incluant l'IA d'analyse des ventes : {nb_plans_ia}.")
    lignes.append(f"- Note moyenne ponderee de l'ensemble des boutiques notees : {note_moyenne_globale}/5.")

    return "\n".join(lignes)


def prompt_systeme(admin_user) -> str:
    return PROMPT_SYSTEME.format(
        admin=admin_user.get_full_name() or admin_user.email,
        donnees=construire_contexte(),
    )
