"""Etat d'avancement du parcours d'inscription d'un vendeur.

L'etape courante se deduit entierement de l'etat des autres modeles
(profil utilisateur, dossier KYC, abonnement) : pas de table dediee.
"""
from admin.abonnements.models import Abonnement
from admin.abonnements.services import abonnement_actif
from admin.kyc.models import DossierKYC

PROFIL = "profil"
IDENTITE = "identite"
FORFAIT = "forfait"
PAIEMENT = "paiement"
TERMINE = "termine"


def profil_complet(user):
    return bool(user.first_name and user.last_name and user.telephone)


def dossier_kyc(user):
    return DossierKYC.objects.filter(vendeur=user).first()


def etape_courante(user):
    if not profil_complet(user):
        return PROFIL

    dossier = dossier_kyc(user)
    if dossier is None or dossier.statut in (
        DossierKYC.Statut.BROUILLON,
        DossierKYC.Statut.EN_ATTENTE,
        DossierKYC.Statut.REJETE,
    ):
        return IDENTITE

    # KYC valide
    if abonnement_actif(user):
        return TERMINE
    if Abonnement.objects.filter(
        vendeur=user, statut=Abonnement.Statut.EN_ATTENTE
    ).exists():
        return PAIEMENT
    return FORFAIT


def onboarding_termine(user):
    return etape_courante(user) == TERMINE


# Pour l'affichage du fil d'etapes (3 jalons visibles).
def jalon_visible(etape):
    return {
        PROFIL: 1,
        IDENTITE: 1,
        FORFAIT: 2,
        PAIEMENT: 2,
        TERMINE: 3,
    }[etape]
