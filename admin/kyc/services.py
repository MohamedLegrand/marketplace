"""Regles metier KYC, partagees par l'admin et (plus tard) l'espace vendeur."""
from admin.kyc.models import DossierKYC


def kyc_valide(vendeur):
    """True si le vendeur a un dossier KYC valide."""
    if vendeur is None or not getattr(vendeur, "pk", None):
        return False
    return DossierKYC.objects.filter(
        vendeur=vendeur, statut=DossierKYC.Statut.VALIDE
    ).exists()
