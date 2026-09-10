"""Orchestration des paiements : initiation, synchronisation de statut par
polling et effets metier (confirmation de commande, activation d'abonnement).
"""
import uuid

from django.utils import timezone

from admin.paiements.gateway import get_client
from admin.paiements.models import Paiement

_STATUT_API = {
    "PENDING": Paiement.Statut.EN_ATTENTE,
    "SUCCESS": Paiement.Statut.REUSSI,
    "FAILED": Paiement.Statut.ECHOUE,
    "HOLD": Paiement.Statut.BLOQUE,
    "REFUNDED": Paiement.Statut.REMBOURSE,
}


def _initier(paiement, description):
    data = get_client().cash_in(
        operator=paiement.operateur,
        phone_number=paiement.telephone,
        amount=paiement.montant,
        currency=paiement.devise,
        description=description,
        metadata={"paiement_id": paiement.pk, "type": paiement.type},
        idempotency_key=paiement.idempotency_key,
    )
    bloc = data.get("data", data)
    paiement.reference_externe = bloc.get("reference", "")
    paiement.transaction_id = bloc.get("transaction_id", "")
    paiement.frais = bloc.get("fee") or 0
    paiement.montant_net = bloc.get("net_amount") or 0
    paiement.reponse_brute = data
    paiement.statut = _STATUT_API.get(bloc.get("status", "PENDING"), Paiement.Statut.EN_ATTENTE)
    paiement.save()
    return paiement


def initier_paiement_commande(commande, operateur, telephone):
    paiement = Paiement.objects.create(
        type=Paiement.Type.COMMANDE, commande=commande, montant=commande.total,
        operateur=operateur, telephone=telephone, idempotency_key=str(uuid.uuid4()),
    )
    return _initier(paiement, f"Commande {commande.reference}")


def initier_paiement_abonnement(abonnement, operateur, telephone):
    paiement = Paiement.objects.create(
        type=Paiement.Type.ABONNEMENT, abonnement=abonnement, montant=abonnement.plan.prix,
        operateur=operateur, telephone=telephone, idempotency_key=str(uuid.uuid4()),
    )
    return _initier(paiement, f"Abonnement {abonnement.plan.nom}")


def synchroniser_statut(paiement):
    """Interroge l'API et applique le statut si besoin (fallback au webhook)."""
    if paiement.statut in (Paiement.Statut.REUSSI, Paiement.Statut.REMBOURSE):
        return paiement
    if not paiement.reference_externe:
        return paiement
    data = get_client().statut_paiement(paiement.reference_externe)
    bloc = data.get("data", data)
    _appliquer_statut(paiement, bloc.get("status"), data)
    return paiement


def _appliquer_statut(paiement, statut_api, data=None):
    nouveau = _STATUT_API.get((statut_api or "").upper())
    if nouveau is None or nouveau == paiement.statut:
        return
    paiement.statut = nouveau
    if data is not None:
        paiement.reponse_brute = data
    if nouveau == Paiement.Statut.REUSSI:
        paiement.date_confirmation = timezone.now()
    paiement.save()
    if nouveau == Paiement.Statut.REUSSI:
        _appliquer_effet(paiement)


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
    elif paiement.abonnement_id:
        abonnement = paiement.abonnement
        if not abonnement.est_actif:
            abonnement.activer(reference=paiement.reference_externe)


def synchroniser_paiements_en_attente(timeout_min=None):
    """Parcourt les paiements encore en attente et interroge l'API pour chacun.
    Passe en 'echoue' ceux qui restent PENDING au-dela du delai (l'utilisateur
    n'ayant pas valide sur son telephone). Destinee a une tache planifiee.

    Retourne (nb_verifies, nb_reussis, nb_echoues).
    """
    from django.conf import settings

    if timeout_min is None:
        timeout_min = getattr(settings, "HRSKILLS_POLL_TIMEOUT_MIN", 20)
    limite = timezone.now() - timezone.timedelta(minutes=timeout_min)

    verifies = reussis = echoues = 0
    en_attente = Paiement.objects.filter(
        statut=Paiement.Statut.EN_ATTENTE
    ).exclude(reference_externe="")
    for paiement in en_attente:
        verifies += 1
        try:
            synchroniser_statut(paiement)
        except Exception:
            continue
        paiement.refresh_from_db()
        if paiement.statut == Paiement.Statut.REUSSI:
            reussis += 1
        elif paiement.statut == Paiement.Statut.ECHOUE:
            echoues += 1
        elif paiement.date_creation < limite:
            _appliquer_statut(paiement, "FAILED")
            echoues += 1
    return verifies, reussis, echoues
