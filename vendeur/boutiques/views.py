from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from admin.abonnements.services import peut_creer_boutique
from admin.boutiques.models import Boutique, ZoneLivraison
from vendeur.comptes.decorators import onboarding_complete_required

from .forms import BoutiqueForm, ZoneLivraisonForm

_STATUTS_MODIFIABLES = (Boutique.Statut.BROUILLON, Boutique.Statut.REJETEE)


def _boutique_du_vendeur(request, pk):
    return get_object_or_404(Boutique, pk=pk, proprietaire=request.user)


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
        boutique = form.save()
        messages.success(request, "Boutique creee en brouillon. Completez-la puis soumettez-la a validation.")
        return redirect("boutiques_vendeur:detail", pk=boutique.pk)
    return render(request, "vendeur/boutiques/form.html", {"form": form, "mode": "creer"})


@onboarding_complete_required
def avis(request, pk):
    boutique = _boutique_du_vendeur(request, pk)
    from admin.avis.models import Avis

    return render(request, "vendeur/boutiques/avis.html", {
        "boutique": boutique,
        "avis_boutique": boutique.avis.select_related("auteur"),
        "avis_produits": Avis.objects.filter(produit__boutique=boutique).select_related("auteur", "produit"),
    })


@onboarding_complete_required
def detail(request, pk):
    boutique = _boutique_du_vendeur(request, pk)
    return render(request, "vendeur/boutiques/detail.html", {
        "boutique": boutique,
        "zones": boutique.zones_livraison.all(),
        "zone_form": ZoneLivraisonForm(),
        "modifiable": boutique.statut in _STATUTS_MODIFIABLES,
        "soumettable": boutique.statut in _STATUTS_MODIFIABLES,
    })


@onboarding_complete_required
def modifier(request, pk):
    boutique = _boutique_du_vendeur(request, pk)
    form = BoutiqueForm(request.POST or None, request.FILES or None, instance=boutique)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Boutique mise a jour.")
        return redirect("boutiques_vendeur:detail", pk=boutique.pk)
    return render(request, "vendeur/boutiques/form.html", {
        "form": form, "mode": "modifier", "boutique": boutique,
    })


@onboarding_complete_required
def soumettre(request, pk):
    boutique = _boutique_du_vendeur(request, pk)
    if request.method != "POST":
        return redirect("boutiques_vendeur:detail", pk=pk)
    if boutique.statut not in _STATUTS_MODIFIABLES:
        messages.error(request, "Cette boutique ne peut pas etre soumise dans son etat actuel.")
        return redirect("boutiques_vendeur:detail", pk=pk)
    manquants = [
        libelle
        for champ, libelle in (("nom", "nom"), ("description", "description"),
                               ("categorie", "categorie"), ("telephone", "telephone"),
                               ("email", "e-mail"), ("ville", "ville"))
        if not getattr(boutique, champ)
    ]
    if manquants:
        messages.error(request, "Completez d'abord : " + ", ".join(manquants) + ".")
        return redirect("boutiques_vendeur:detail", pk=pk)

    boutique.soumettre()
    messages.success(request, "Boutique soumise a validation.")
    return redirect("boutiques_vendeur:detail", pk=pk)


# --- Zones de livraison -----------------------------------------------------
@onboarding_complete_required
def zone_creer(request, pk):
    boutique = _boutique_du_vendeur(request, pk)
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
    return redirect("boutiques_vendeur:detail", pk=pk)


@onboarding_complete_required
def zone_modifier(request, pk, zone_pk):
    boutique = _boutique_du_vendeur(request, pk)
    zone = get_object_or_404(ZoneLivraison, pk=zone_pk, boutique=boutique)
    form = ZoneLivraisonForm(request.POST or None, instance=zone)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Zone mise a jour.")
        return redirect("boutiques_vendeur:detail", pk=pk)
    return render(request, "vendeur/boutiques/zone_form.html", {
        "form": form, "boutique": boutique, "zone": zone,
    })


@onboarding_complete_required
def zone_supprimer(request, pk, zone_pk):
    boutique = _boutique_du_vendeur(request, pk)
    zone = get_object_or_404(ZoneLivraison, pk=zone_pk, boutique=boutique)
    if request.method == "POST":
        zone.delete()
        messages.success(request, "Zone supprimee.")
    return redirect("boutiques_vendeur:detail", pk=pk)
