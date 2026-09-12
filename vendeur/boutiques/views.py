from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from admin.abonnements.services import peut_creer_boutique
from admin.boutiques.models import Boutique, ZoneLivraison
from vendeur.comptes.decorators import acces_boutique_required, onboarding_complete_required

from .forms import BoutiqueForm, ZoneLivraisonForm

# La boutique est active des sa creation (aucune validation par l'admin) :
# le vendeur peut toujours modifier ses informations, sauf si elle a fait
# l'objet d'une sanction (suspension ou bannissement).
_STATUTS_MODIFIABLES = (
    Boutique.Statut.BROUILLON,
    Boutique.Statut.EN_ATTENTE,
    Boutique.Statut.APPROUVEE,
    Boutique.Statut.REJETEE,
)


def _boutique_du_vendeur(request, boutique_pk):
    return get_object_or_404(Boutique, pk=boutique_pk, proprietaire=request.user)


def _permissions(request):
    role = request.role_boutique
    if role is None:
        return {"produits": True, "stock": True, "commandes": True, "statistiques": True}
    return {
        "produits": role.peut_gerer_produits,
        "stock": role.peut_gerer_stock,
        "commandes": role.peut_gerer_commandes,
        "statistiques": role.peut_voir_statistiques,
    }


@onboarding_complete_required
def liste(request):
    boutiques = request.user.boutiques.all()
    autorise, message = peut_creer_boutique(request.user)
    return render(request, "vendeur/boutiques/liste.html", {
        "boutiques": boutiques,
        "peut_creer": autorise,
        "message_quota": message,
    })


@onboarding_complete_required
def creer(request):
    autorise, message = peut_creer_boutique(request.user)
    if not autorise:
        messages.error(request, message)
        return redirect("boutiques_vendeur:liste")

    form = BoutiqueForm(
        request.POST or None,
        request.FILES or None,
        instance=Boutique(proprietaire=request.user),
    )
    if request.method == "POST" and form.is_valid():
        boutique = form.save(commit=False)
        # Pas de validation par l'administrateur : la boutique est active des
        # sa creation (le KYC du vendeur a deja ete verifie en amont).
        boutique.statut = Boutique.Statut.APPROUVEE
        boutique.save()
        messages.success(request, "Boutique creee et publiee.")
        return redirect("boutiques_vendeur:detail", boutique_pk=boutique.pk)
    return render(request, "vendeur/boutiques/form.html", {"form": form, "mode": "creer"})


@acces_boutique_required()
def avis(request, boutique_pk):
    boutique = request.boutique
    from admin.avis.models import Avis

    return render(request, "vendeur/boutiques/avis.html", {
        "boutique": boutique,
        "avis_boutique": boutique.avis.select_related("auteur"),
        "avis_produits": Avis.objects.filter(produit__boutique=boutique).select_related("auteur", "produit"),
    })


@acces_boutique_required()
def detail(request, boutique_pk):
    boutique = request.boutique
    return render(request, "vendeur/boutiques/detail.html", {
        "boutique": boutique,
        "zones": boutique.zones_livraison.all(),
        "zone_form": ZoneLivraisonForm(),
        "modifiable": request.est_proprietaire_boutique and boutique.statut in _STATUTS_MODIFIABLES,
        "est_proprietaire": request.est_proprietaire_boutique,
        "permissions": _permissions(request),
    })


@onboarding_complete_required
def modifier(request, boutique_pk):
    boutique = _boutique_du_vendeur(request, boutique_pk)
    form = BoutiqueForm(request.POST or None, request.FILES or None, instance=boutique)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Boutique mise a jour.")
        return redirect("boutiques_vendeur:detail", boutique_pk=boutique.pk)
    return render(request, "vendeur/boutiques/form.html", {
        "form": form, "mode": "modifier", "boutique": boutique,
    })


# --- Zones de livraison -----------------------------------------------------
@onboarding_complete_required
def zone_creer(request, boutique_pk):
    boutique = _boutique_du_vendeur(request, boutique_pk)
    if request.method == "POST":
        form = ZoneLivraisonForm(request.POST)
        if form.is_valid():
            zone = form.save(commit=False)
            zone.boutique = boutique
            try:
                zone.validate_constraints()
                zone.save()
                messages.success(request, "Zone de livraison ajoutee.")
            except ValidationError:
                messages.error(request, "Une zone porte deja ce nom pour cette boutique.")
        else:
            messages.error(request, "Formulaire de zone invalide.")
    return redirect("boutiques_vendeur:detail", boutique_pk=boutique_pk)


@onboarding_complete_required
def zone_modifier(request, boutique_pk, zone_pk):
    boutique = _boutique_du_vendeur(request, boutique_pk)
    zone = get_object_or_404(ZoneLivraison, pk=zone_pk, boutique=boutique)
    form = ZoneLivraisonForm(request.POST or None, instance=zone)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Zone mise a jour.")
        return redirect("boutiques_vendeur:detail", boutique_pk=boutique_pk)
    return render(request, "vendeur/boutiques/zone_form.html", {
        "form": form, "boutique": boutique, "zone": zone,
    })


@onboarding_complete_required
def zone_supprimer(request, boutique_pk, zone_pk):
    boutique = _boutique_du_vendeur(request, boutique_pk)
    zone = get_object_or_404(ZoneLivraison, pk=zone_pk, boutique=boutique)
    if request.method == "POST":
        zone.delete()
        messages.success(request, "Zone supprimee.")
    return redirect("boutiques_vendeur:detail", boutique_pk=boutique_pk)
