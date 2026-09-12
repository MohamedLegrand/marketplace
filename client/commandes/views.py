from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from admin.boutiques.models import Boutique
from admin.commandes.models import Commande
from admin.paiements.models import Paiement
from admin.paiements.services import simuler_paiement_commande
from client.comptes.decorators import client_required
from client.comptes.forms import AdresseForm
from client.panier.panier import Panier

from .facture import generer_facture
from .services import StockInsuffisant, creer_commande

# Operateurs Mobile Money simules : la longueur exacte du code PIN differe
# selon l'operateur (regle metier demandee), mais sa valeur n'est jamais
# verifiee (paiement toujours simule comme reussi).
OPERATEURS = [("orange", "Orange Money"), ("mtn", "MTN MoMo")]
LONGUEUR_PIN = {"orange": 4, "mtn": 5}

# Valeur du champ "adresse" du formulaire de checkout quand l'acheteur
# renseigne une nouvelle adresse de livraison au lieu d'en choisir une deja
# enregistree.
NOUVELLE_ADRESSE = "nouvelle"


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
    formulaire_adresse = AdresseForm()

    if request.method == "POST":
        choix_adresse = request.POST.get("adresse")
        zone = zones.filter(pk=request.POST.get("zone")).first() if zones else None
        adresse = None

        if choix_adresse == NOUVELLE_ADRESSE or not adresses.exists():
            formulaire_adresse = AdresseForm(request.POST)
            if formulaire_adresse.is_valid():
                adresse = formulaire_adresse.save(commit=False)
                adresse.client = request.user
                if not adresses.exists():
                    adresse.par_defaut = True
                adresse.save()
            else:
                messages.error(request, "Corrigez les informations de livraison.")
        else:
            adresse = adresses.filter(pk=choix_adresse).first()
            if adresse is None:
                messages.error(request, "Choisissez une adresse de livraison.")

        if adresse is not None:
            if zones and zone is None:
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
        "formulaire_adresse": formulaire_adresse,
        "nouvelle_adresse": NOUVELLE_ADRESSE,
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
    """Paiement simule (plus d'agregateur externe) : l'acheteur choisit un
    operateur Mobile Money et saisit un code PIN (n'importe quelle valeur est
    acceptee, mais sa longueur doit correspondre a l'operateur : 4 chiffres
    pour Orange Money, 5 pour MTN MoMo). Le paiement est alors marque
    reussi, la commande confirmee, une notification envoyee et une facture
    generee."""
    commande = get_object_or_404(Commande, reference=reference, client=request.user)
    if commande.statut != Commande.Statut.EN_ATTENTE_PAIEMENT:
        return redirect("commandes_client:detail", reference=reference)

    if request.method == "POST":
        operateur = request.POST.get("operateur")
        pin = (request.POST.get("pin") or "").strip()
        longueur = LONGUEUR_PIN.get(operateur)
        if longueur is None:
            messages.error(request, "Choisissez un operateur Mobile Money.")
        elif not pin.isdigit() or len(pin) != longueur:
            messages.error(
                request,
                f"Le code PIN {dict(OPERATEURS)[operateur]} doit comporter exactement {longueur} chiffres.",
            )
        else:
            simuler_paiement_commande(commande, operateur=operateur)
            messages.success(request, "Paiement effectue. Votre facture est disponible.")
            return redirect("commandes_client:detail", reference=reference)

    return render(request, "client/commandes/payer.html", {
        "commande": commande,
        "operateurs": OPERATEURS,
        "longueurs_pin": LONGUEUR_PIN,
    })


@client_required
def facture(request, reference):
    commande = get_object_or_404(
        Commande.objects.prefetch_related("lignes"), reference=reference, client=request.user,
    )
    paiement = commande.paiements.filter(statut=Paiement.Statut.REUSSI).order_by("-date_confirmation").first()
    if paiement is None:
        messages.error(request, "Aucun paiement confirme pour cette commande.")
        return redirect("commandes_client:detail", reference=reference)
    contenu = generer_facture(commande, paiement)
    reponse = HttpResponse(contenu, content_type="application/pdf")
    reponse["Content-Disposition"] = f'attachment; filename="facture-{commande.reference}.pdf"'
    return reponse


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
