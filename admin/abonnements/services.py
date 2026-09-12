"""Regles metier de l'abonnement, partagees par l'admin et (plus tard) par
l'espace vendeur. Chaque fonction renvoie ``(autorise: bool, message: str)``.
"""
from admin.abonnements.models import Abonnement


def abonnement_actif(vendeur):
    """Retourne l'abonnement actif du vendeur, sinon ``None``."""
    if vendeur is None or not getattr(vendeur, "pk", None):
        return None
    for ab in (
        vendeur.abonnements.filter(statut=Abonnement.Statut.ACTIF).select_related("plan")
    ):
        if ab.est_actif:
            return ab
    return None


def plan_actif(vendeur):
    ab = abonnement_actif(vendeur)
    return ab.plan if ab else None


def peut_creer_boutique(vendeur):
    ab = abonnement_actif(vendeur)
    if ab is None:
        return False, (
            "Aucun abonnement actif : la souscription a un plan est requise "
            "pour ouvrir une boutique."
        )
    plan = ab.plan
    if plan.max_boutiques is not None:
        actuelles = vendeur.boutiques.exclude(statut="bannie").count()
        if actuelles >= plan.max_boutiques:
            return False, (
                f"Le plan « {plan.nom} » est limite a {plan.max_boutiques} "
                f"boutique(s). Passez a un plan superieur pour en ouvrir davantage."
            )
    return True, ""


def peut_utiliser_ia(vendeur):
    ab = abonnement_actif(vendeur)
    if ab is None:
        return False, "Aucun abonnement actif : souscrivez a un plan incluant l'IA d'analyse des ventes."
    if not ab.plan.ia_analyse_ventes:
        return False, (
            f"Le plan « {ab.plan.nom} » n'inclut pas l'assistant IA d'analyse des ventes. "
            "Passez a un plan superieur pour en beneficier."
        )
    return True, ""


def peut_creer_role(boutique):
    from admin.boutiques.models import RoleBoutique

    vendeur = boutique.proprietaire
    ab = abonnement_actif(vendeur)
    if ab is None:
        return False, "Aucun abonnement actif pour le proprietaire de la boutique."
    plan = ab.plan
    if not plan.delegation_roles:
        return False, f"Le plan « {plan.nom} » n'autorise pas la delegation de roles."
    if plan.max_roles is not None:
        actuels = RoleBoutique.objects.filter(boutique__proprietaire=vendeur).count()
        if actuels >= plan.max_roles:
            return False, (
                f"Le plan « {plan.nom} » est limite a {plan.max_roles} role(s) delegue(s)."
            )
    return True, ""
