"""Paiements simules (plus d'agregateur externe) et effets metier associes
(confirmation de commande, activation d'abonnement). Chaque paiement simule
est tout de meme stocke dans la table "paiement", qui fait office d'historique
des transactions.
"""
import uuid

from django.utils import timezone

from admin.paiements.models import Paiement


def _appliquer_effet(paiement):
    """Idempotent : confirme la commande ou active l'abonnement lie."""
    from admin.commandes.models import Commande

    if paiement.commande_id:
        commande = paiement.commande
        if commande.statut == Commande.Statut.EN_ATTENTE_PAIEMENT:
            commande.changer_statut(
                commande.client, Commande.Statut.CONFIRMEE,
                f"Paiement {paiement.reference_externe} confirme",
            )
            from client.notifications.services import notifier

            notifier(
                commande.client,
                "Paiement effectue",
                f"Votre paiement pour la commande {commande.reference} a ete confirme. "
                "Une facture est disponible.",
                lien=f"/commande/{commande.reference}/",
            )
    elif paiement.abonnement_id:
        abonnement = paiement.abonnement
        if not abonnement.est_actif:
            abonnement.activer(reference=paiement.reference_externe)


def simuler_paiement_commande(commande, operateur=""):
    """Marque immediatement la transaction reussie (formulaire de paiement
    simule cote acheteur : operateur + code PIN, tout code accepte) et
    confirme la commande."""
    paiement = Paiement.objects.create(
        type=Paiement.Type.COMMANDE,
        commande=commande,
        montant=commande.total,
        montant_net=commande.total,
        operateur=operateur or "simulation",
        telephone=commande.adresse_telephone,
        idempotency_key=str(uuid.uuid4()),
        reference_externe=f"SIM-{uuid.uuid4().hex[:10].upper()}",
        statut=Paiement.Statut.REUSSI,
        date_confirmation=timezone.now(),
        reponse_brute={"mode": "simulation", "note": "Paiement effectue (simulation, sans agregateur)."},
    )
    _appliquer_effet(paiement)
    return paiement


def simuler_paiement_abonnement(abonnement):
    """Idem, pour le paiement d'un abonnement vendeur."""
    paiement = Paiement.objects.create(
        type=Paiement.Type.ABONNEMENT,
        abonnement=abonnement,
        montant=abonnement.plan.prix,
        montant_net=abonnement.plan.prix,
        operateur="simulation",
        telephone="",
        idempotency_key=str(uuid.uuid4()),
        reference_externe=f"SIM-{uuid.uuid4().hex[:10].upper()}",
        statut=Paiement.Statut.REUSSI,
        date_confirmation=timezone.now(),
        reponse_brute={"mode": "simulation", "note": "Paiement effectue (simulation, sans agregateur)."},
    )
    _appliquer_effet(paiement)
    return paiement
