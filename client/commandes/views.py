from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from admin.boutiques.models import Boutique
from admin.commandes.models import Commande
from admin.paiements.gateway import HRSkillsPayError
from admin.paiements.models import Paiement
from admin.paiements.services import initier_paiement_commande, synchroniser_statut
from client.comptes.decorators import client_required
from client.comptes.models import AdresseLivraison
from client.panier.panier import Panier

from .services import StockInsuffisant, creer_commande


@client_required
def liste(request):
    commandes = request.user.commandes.select_related("boutique").prefetch_related("lignes")
    return render(request, "client/commandes/liste.html", {"commandes": commandes})


@client_required
def checkout(request):
    panier = Panier(request)
    lignes = panier.lignes()
    if not lignes:
        messages.error(request, "Votre panier est vide.")
        return redirect("panier:voir")

    boutique = get_object_or_404(Boutique.objects.visibles(), pk=panier.boutique_id)
    adresses = request.user.adresses.all()
    zones = boutique.zones_livraison.filter(actif=True)
    sous_total = panier.total()

    if request.method == "POST":
        adresse = adresses.filter(pk=request.POST.get("adresse")).first()
        zone = zones.filter(pk=request.POST.get("zone")).first() if zones else None
        if adresse is None:
            messages.error(request, "Choisissez une adresse de livraison.")
        elif zones and zone is None:
            messages.error(request, "Choisissez une zone de livraison.")
        else:
            try:
                commande = creer_commande(request.user, panier, adresse, zone)
            except StockInsuffisant as err:
                messages.error(request, str(err))
                return redirect("panier:voir")
            except ValueError:
                messages.error(request, "Votre panier est vide.")
                return redirect("panier:voir")
            return redirect("commandes_client:confirmation", reference=commande.reference)

    return render(request, "client/commandes/checkout.html", {
        "lignes": lignes,
        "boutique": boutique,
        "adresses": adresses,
        "zones": zones,
        "sous_total": sous_total,
    })


@client_required
def confirmation(request, reference):
    commande = get_object_or_404(Commande, reference=reference, client=request.user)
    return render(request, "client/commandes/confirmation.html", {"commande": commande})


@client_required
def detail(request, reference):
    commande = get_object_or_404(
        Commande.objects.prefetch_related("lignes", "suivis"),
        reference=reference, client=request.user,
    )
    return render(request, "client/commandes/detail.html", {"commande": commande})


@client_required
def payer(request, reference):
    """Formulaire de paiement Mobile Money + initiation via l'agregateur."""
    commande = get_object_or_404(Commande, reference=reference, client=request.user)
    if commande.statut != Commande.Statut.EN_ATTENTE_PAIEMENT:
        return redirect("commandes_client:detail", reference=reference)

    if request.method == "POST":
        operateur = request.POST.get("operateur")
        telephone = (request.POST.get("telephone") or "").strip()
        if operateur not in dict(settings.OPERATEURS_MOBILE_MONEY) or not telephone:
            messages.error(request, "Choisissez un operateur et saisissez votre numero.")
        else:
            try:
                initier_paiement_commande(commande, operateur, telephone)
            except HRSkillsPayError as err:
                messages.error(request, f"Echec de l'initiation : {err.message or err.code}")
            else:
                messages.success(
                    request,
                    "Paiement initie. Validez la demande sur votre telephone, puis cliquez sur Verifier.",
                )
                return redirect("commandes_client:paiement_suivi", reference=reference)

    return render(request, "client/commandes/payer.html", {
        "commande": commande,
        "operateurs": settings.OPERATEURS_MOBILE_MONEY,
    })


@client_required
def paiement_suivi(request, reference):
    commande = get_object_or_404(Commande, reference=reference, client=request.user)
    if commande.statut != Commande.Statut.EN_ATTENTE_PAIEMENT:
        return redirect("commandes_client:detail", reference=reference)
    paiement = commande.paiements.order_by("-date_creation").first()
    if paiement is None:
        return redirect("commandes_client:payer", reference=reference)
    return render(request, "client/commandes/paiement_suivi.html", {
        "commande": commande, "paiement": paiement,
    })


@client_required
def paiement_verifier(request, reference):
    commande = get_object_or_404(Commande, reference=reference, client=request.user)
    paiement = commande.paiements.order_by("-date_creation").first()
    if request.method == "POST" and paiement:
        try:
            synchroniser_statut(paiement)
        except HRSkillsPayError as err:
            messages.error(request, f"Verification impossible : {err.message or err.code}")
            return redirect("commandes_client:paiement_suivi", reference=reference)
        commande.refresh_from_db()
        paiement.refresh_from_db()
        if commande.statut != Commande.Statut.EN_ATTENTE_PAIEMENT:
            messages.success(request, "Paiement confirme. Votre commande est transmise a la boutique.")
            return redirect("commandes_client:detail", reference=reference)
        if paiement.statut == Paiement.Statut.ECHOUE:
            messages.error(request, "Le paiement a echoue. Vous pouvez reessayer.")
            return redirect("commandes_client:payer", reference=reference)
    return redirect("commandes_client:paiement_suivi", reference=reference)


@client_required
def annuler(request, reference):
    commande = get_object_or_404(Commande, reference=reference, client=request.user)
    if request.method == "POST":
        if commande.annulable_par_client:
            commande.annuler(request.user, "Annulee par le client")
            messages.success(request, "Commande annulee.")
        else:
            messages.error(request, "Cette commande ne peut plus etre annulee.")
    return redirect("commandes_client:detail", reference=reference)
